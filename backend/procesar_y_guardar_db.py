import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from time import sleep
from tqdm import tqdm
from datetime import datetime
import hashlib
import re
import db 
from bs4 import BeautifulSoup
import trafilatura

load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ES_PRODUCCION = os.getenv("ENVIRONMENT") == "production"

if not GNEWS_API_KEY or not GEMINI_API_KEY:
    raise ValueError("⚠️ Asegúrate de configurar GNEWS_API_KEY y GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CATEGORIAS = {
    "business": "Negocios", "entertainment": "Entretenimiento", "health": "Salud",
    "science": "Ciencia", "sports": "Deportes", "technology": "Tecnología", "general": "General"
}

MAX_NOTICIAS_POR_CATEGORIA = 3  # Aumenté ligeramente para compensar filtros más flexibles
TIEMPO_ESPERA_ENTRE_REQUESTS = 2
MAX_PALABRAS_RESUMEN = 350
MAX_PALABRAS_SCRAPING = 600
MIN_PALABRAS_CONTENIDO_VALIDO = 30  # REDUCIDO de 50 a 30
MIN_PALABRAS_RESUMEN_SIGNIFICATIVO = 40  # REDUCIDO de 80 a 40
MIN_PALABRAS_DESCRIPCION = 40  # REDUCIDO de 80 a 40

RESUMENES_INVALIDOS = [
    "Resumen no disponible - contenido insuficiente",
    "Contenido insuficiente para generar un resumen significativo.",
    "Resumen no disponible por limitaciones técnicas.",
    "Resumen no disponible",
    "contenido insuficiente",
    "limitaciones técnicas"
]

def generar_hash_titulo(titulo):
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()

def limpiar_noticias_existentes_invalidas():
    """Elimina noticias existentes en la base de datos que tengan resúmenes inválidos"""
    print("🧹 Buscando noticias existentes con resúmenes inválidos...")
    
    try:
        todas_noticias = db.get_noticias(limit=1000)
        
        noticias_invalidas = []
        
        for noticia in todas_noticias:
            resumen = noticia.get('resumen', '')
            
            if any(invalido.lower() in resumen.lower() for invalido in RESUMENES_INVALIDOS):
                noticias_invalidas.append(noticia['id'])
                print(f"🚫 Encontrada noticia inválida: ID {noticia['id']} - {noticia['titulo'][:50]}...")
        
        if noticias_invalidas:
            print(f"🗑️  Eliminando {len(noticias_invalidas)} noticias con resúmenes inválidos...")
            
            eliminadas_exitosas = 0
            for noticia_id in noticias_invalidas:
                try:
                    if db.eliminar_noticia_por_id(noticia_id):
                        eliminadas_exitosas += 1
                        print(f"✅ Eliminada noticia ID {noticia_id}")
                    else:
                        print(f"⚠️ No se pudo eliminar noticia ID {noticia_id}")
                except Exception as e:
                    print(f"❌ Error eliminando noticia ID {noticia_id}: {e}")
            
            print(f"🎯 Limpieza completada: {eliminadas_exitosas}/{len(noticias_invalidas)} noticias inválidas eliminadas")
            return eliminadas_exitosas
        else:
            print("✅ No se encontraron noticias con resúmenes inválidos")
            return 0
            
    except Exception as e:
        print(f"❌ Error en limpieza de noticias existentes: {e}")
        return 0
    
def obtener_noticias_por_categoria(categoria, max_noticias=MAX_NOTICIAS_POR_CATEGORIA, urls_existentes=None):
    if urls_existentes is None:
        urls_existentes = set()
    
    print(f"📡 Buscando {max_noticias} noticias NUEVAS de: '{CATEGORIAS.get(categoria, categoria)}'...")
    
    noticias_nuevas = []
    urls_encontradas = set()
    
    try:
        url = (f"https://gnews.io/api/v4/top-headlines?"
               f"category={categoria}&lang=es&max={max_noticias * 4}&apikey={GNEWS_API_KEY}")  # Aumenté el buffer
        
        sleep(TIEMPO_ESPERA_ENTRE_REQUESTS)
        
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 429:
            print(f"⏳ Rate limit alcanzado para {categoria}, esperando...")
            sleep(15)
            return []
            
        if resp.status_code != 200:
            print(f"❌ Error HTTP {resp.status_code} para {categoria}")
            return []
            
        data = resp.json()
        articulos = data.get("articles", [])
       
        for articulo in articulos:
            if not all([articulo.get("url"), articulo.get("title"), articulo.get("description")]):
                continue
                
            url_noticia = articulo.get("url")
            
            descripcion = articulo.get("description", "").strip()
            titulo = articulo.get("title", "").strip()
            
            # CRITERIOS MÁS FLEXIBLES - REDUCIDOS
            if (url_noticia not in urls_existentes and 
                url_noticia not in urls_encontradas and
                len(titulo) > 10 and  # REDUCIDO de 15 a 10
                len(descripcion) > MIN_PALABRAS_DESCRIPCION and  # Usando la nueva variable
                not db.noticia_existe(titulo, url_noticia)):
                
                articulo['categoria_asignada'] = CATEGORIAS.get(categoria, "General")
                noticias_nuevas.append(articulo)
                urls_encontradas.add(url_noticia)
                
                if len(noticias_nuevas) >= max_noticias:
                    break
        
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout al obtener noticias de {categoria}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión con GNews para '{categoria}': {e}")
    except Exception as e:
        print(f"⚠️ Error inesperado en {categoria}: {e}")
    
    print(f"✅ Encontradas {len(noticias_nuevas)} noticias válidas para '{CATEGORIAS.get(categoria, categoria)}'")
    return noticias_nuevas

def scrapear_texto_robusto(url, fallback_description=None):
    """Scraping robusto con múltiples métodos de extracción - CRITERIOS MÁS FLEXIBLES"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Trafilatura - CON UMBRAL MÁS BAJO
    try:
        downloaded = trafilatura.fetch_url(url) 
        if downloaded:
            content = trafilatura.extract(
                downloaded, 
                include_comments=False, 
                include_tables=False,
                no_fallback=True
            )
            if content and len(content.split()) > 50:  # REDUCIDO de 100 a 50
                print(f"✅ Trafilatura: {len(content.split())} palabras")
                return ' '.join(content.split()[:MAX_PALABRAS_SCRAPING])
    except Exception as e:
        print(f"⚠️ Trafilatura falló: {e}")

    # BeautifulSoup - CON UMBRALES MÁS BAJOS
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectores = [
            'article .article-content', 'article .story-content', '.news-content',
            '.entry-content', '.post-content', '[class*="content"]',
            'article p', '.article-body', '.news-body', '.story-text', '.news-text'
        ]
        
        for selector in selectores:
            elements = soup.select(selector)
            if elements:
                text_content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(text_content.split()) > 50:  # REDUCIDO de 100 a 50
                    print(f"✅ BeautifulSoup con selector '{selector}': {len(text_content.split())} palabras")
                    return ' '.join(text_content.split()[:MAX_PALABRAS_SCRAPING])
        
        # Párrafos individuales - MÁS FLEXIBLE
        paragraphs = soup.find_all('p')
        if paragraphs:
            text_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])  # REDUCIDO de 50 a 30
            if len(text_content.split()) > 40:  # REDUCIDO de 100 a 40
                print(f"✅ Fallback párrafos: {len(text_content.split())} palabras")
                return ' '.join(text_content.split()[:MAX_PALABRAS_SCRAPING])
                
    except Exception as e:
        print(f"⚠️ BeautifulSoup falló: {e}")

    # Regex cleaning - MÁS PERMISIVO
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        clean = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        text = re.sub(clean, ' ', response.text)
        
        text = ' '.join(text.split())
        
        if len(text.split()) > 80:  # REDUCIDO de 300 a 80
            print(f"✅ Regex cleaning (fallback robusto): {len(text.split())} palabras")
            return ' '.join(text.split()[:500])  # REDUCIDO el límite
        else:
            print(f"⚠️ Regex cleaning: contenido insuficiente/ruido ({len(text.split())} palabras)")
            
    except Exception as e:
        print(f"⚠️ Regex cleaning falló: {e}")

    # FALLBACK MÁS PERMISIVO
    if fallback_description and len(fallback_description.split()) >= 20:  # REDUCIDO de 30 a 20
        print(f"✅ Usando descripción fallback: {len(fallback_description.split())} palabras")
        return fallback_description
    
    print(f"❌ Todos los métodos fallaron, contenido insuficiente")
    return None

def validar_contenido_noticia(texto, titulo):
    """Valida que el contenido sea realmente una noticia - FILTROS MUY FLEXIBLES"""
    
    if not texto or len(texto.split()) < MIN_PALABRAS_CONTENIDO_VALIDO:
        print(f"⚠️ Contenido muy corto: {len(texto.split()) if texto else 0} palabras")
        return False
    
    # PATRONES MUCHO MÁS ESPECÍFICOS para evitar falsos positivos
    patrones_no_deseados = [
        r'<!DOCTYPE', r'<html', r'<head>', r'<body>', 
        r'function\s*\(', r'classList\.', r'addEventListener',
        r'@media', r'font-family', r'background-color',
        r'window\.', r'document\.', r'\.getElementById',
        r'\.querySelector', r'\.addClass', r'\.removeClass'
    ]
    
    # Solo buscar patrones si aparecen múltiples veces (evitar falsos positivos)
    for patron in patrones_no_deseados:
        matches = re.findall(patron, texto, re.IGNORECASE)
        if len(matches) > 2:  # Solo rechazar si aparece más de 2 veces
            print(f"⚠️ Contenido rechazado por patrón múltiple: {patron} ({len(matches)} veces)")
            return False
    
    # ELIMINAR patrones que causan falsos positivos con lenguaje natural
    patrones_problematicos = [
        r'var\s+', r'const\s+', r'let\s+',  # DEMASIADOS FALSOS POSITIVOS
        r'padding:', r'margin:', r'display:\s*(flex|block|inline)',
        r'position:', r'z-index:'
    ]
    
    # PALABRAS CLAVE MÁS FLEXIBLES
    palabras_clave_noticia = [
        'anunció', 'confirmó', 'informó', 'declaró', 'según', 'fuentes', 
        'investigación', 'estudio', 'datos', 'informe', 'autoridades',
        'gobierno', 'empresa', 'mercado', 'economía', 'política',
        'afirmó', 'señaló', 'explicó', 'indicó', 'manifestó',
        'expresó', 'reveló', 'destacó', 'comentó', 'mencionó',
        'país', 'ciudad', 'presidente', 'ministro', 'director',
        'año', 'mes', 'día', 'semana', 'horas', 'minutos'
    ]
    
    palabras_encontradas = sum(1 for palabra in palabras_clave_noticia if palabra in texto.lower())
    
    # ACEPTAR incluso si tiene solo 1 palabra clave (para noticias muy cortas)
    tiene_suficientes_palabras_clave = palabras_encontradas >= 1
    
    # Verificar que sea texto legible (no código)
    es_texto_legible = (
        len(re.findall(r'[.!?]', texto)) > 2 or  # Tiene puntuación
        len(re.findall(r'\b[a-zA-Záéíóúñ]{4,}\b', texto)) > 20  # Palabras largas
    )
    
    return tiene_suficientes_palabras_clave and es_texto_legible

def resumir_texto_robusto(texto, titulo):
    """Genera resúmenes robustos con validación de contenido MÁS FLEXIBLE"""
    
    if not validar_contenido_noticia(texto, titulo):
        print("❌ Contenido no válido para resumir")
        return "Resumen no disponible - contenido insuficiente"

    if len(texto.split()) < MIN_PALABRAS_RESUMEN_SIGNIFICATIVO:  # Ahora 40 palabras mínimo
        return "Contenido insuficiente para generar un resumen significativo."

    if len(texto.split()) > MAX_PALABRAS_SCRAPING:
        texto = ' '.join(texto.split()[:MAX_PALABRAS_SCRAPING])
        print(f"✂️ Texto recortado para resumen a {MAX_PALABRAS_SCRAPING} palabras.")

    # PROMPT ADAPTADO PARA TEXTOS MÁS CORTOS
    prompt = f"""
# CONTEXTO Y ROL
Eres un periodista senior especializado en crear resúmenes ejecutivos para medios de comunicación. Tu tarea es transformar el texto proporcionado en un resumen periodístico de alta calidad.

# TÍTULO DE LA NOTICIA: {titulo}

# INSTRUCCIONES ESTRICTAS
## FORMATO:
- EXCLUSIVAMENTE un párrafo continuo
- SIN saltos de línea, viñetas, números o encabezados
- LONGITUD: 100-330 palabras (AJUSTADO para contenido más corto)
- Lenguaje 100% en español

## CONTENIDO PERIODÍSTICO:
Aplica la técnica de las **5W+H** de forma implícita pero concisa:
- **QUÉ**: Evento principal/descubrimiento/anuncio
- **QUIÉN**: Actores principales
- **CONTEXTO**: Información esencial

## ESTILO Y TONO:
- Lenguaje formal pero accesible
- Objetividad absoluta
- Densidad informativa máxima
- Adaptado al contenido disponible

## PARA CONTENIDO MÁS CORTO:
Si el texto original es breve, crea un resumen conciso pero informativo que expanda ligeramente la información disponible.

# TEXTO ORIGINAL PARA RESUMIR:
{texto}

# RESULTADO ESPERADO:
[Tu resumen periodístico aquí, en un solo párrafo continuo, adaptado a la longitud del contenido original]
"""
    
    try:
        response = model.generate_content(prompt)
        resumen = response.text.strip()
        
        # CRITERIOS DE VALIDACIÓN MÁS FLEXIBLES
        if (len(resumen.split()) < 30 or  # REDUCIDO de 50 a 30
            len(resumen.split()) > MAX_PALABRAS_RESUMEN or
            any(invalido in resumen for invalido in RESUMENES_INVALIDOS)):
            raise ValueError(f"Resumen inválido o fuera de límites ({len(resumen.split())} palabras)")
            
        print(f"✅ Resumen generado: {len(resumen.split())} palabras")
        return resumen
        
    except Exception as e:
        print(f"⚠️ Error al generar resumen con Gemini: {repr(e)}")
        
        # FALLBACK MÁS PERMISIVO
        if len(texto.split()) > 30:  # REDUCIDO de 100 a 30
            sentences = re.split(r'[.!?]+', texto)
            meaningful_sentences = [s.strip() for s in sentences if len(s.split()) > 5][:4]  # REDUCIDO umbral
            fallback = ". ".join(meaningful_sentences) + "."
            if len(fallback) > 50:  # REDUCIDO de 80 a 50
                return fallback
        
        return "Resumen no disponible - contenido insuficiente"

def es_resumen_valido(resumen):
    """🔥 VALIDA si el resumen es aceptable - CRITERIOS MÁS FLEXIBLES"""
    if not resumen or len(resumen.strip()) == 0:
        return False
    
    resumen_lower = resumen.lower()
    if any(invalido.lower() in resumen_lower for invalido in RESUMENES_INVALIDOS):
        return False
    
    if len(resumen.split()) < 25:  # REDUCIDO de 40 a 25 palabras mínimas
        return False
    
    return True

def procesar_y_guardar_noticias():
    """Proceso principal robusto de obtención y procesamiento de noticias - MÁS PERMISIVO"""
    
    db.inicializar_db()
    
    print("🕒 Iniciando proceso de obtención de noticias...")
    print("=" * 60)
    print(f"📊 Hora de ejecución: {datetime.now()}")
    print(f"🎯 UMBRALES FLEXIBLES: Mínimo {MIN_PALABRAS_CONTENIDO_VALIDO} palabras para contenido válido")
    
    noticias_eliminadas = limpiar_noticias_existentes_invalidas()
    
    urls_existentes = db.obtener_urls_existentes()
    print(f"📊 Noticias existentes en la base de datos: {len(urls_existentes)}")
   
    todas_las_noticias = []
    categorias_procesadas = 0

    for i, categoria_api in enumerate(CATEGORIAS.keys()):
        print(f"\n📍 Procesando categoría {i+1}/{len(CATEGORIAS)}: {categoria_api}")
        
        try:
            noticias_de_categoria = obtener_noticias_por_categoria(
                categoria_api,
                max_noticias=MAX_NOTICIAS_POR_CATEGORIA,
                urls_existentes=urls_existentes
            )
            
            if noticias_de_categoria:
                todas_las_noticias.extend(noticias_de_categoria)
                categorias_procesadas += 1
                print(f"✅ Categoría {categoria_api}: {len(noticias_de_categoria)} noticias nuevas")
            else:
                print(f"⚠️ Categoría {categoria_api}: 0 noticias nuevas")
                
            if i < len(CATEGORIAS) - 1:
                sleep(2)
                
        except Exception as e:
            print(f"❌ Error procesando categoría {categoria_api}: {e}")
            continue
    
    if not todas_las_noticias:
        print("❌ No se encontraron noticias NUEVAS válidas para procesar.")
        return {
            "nuevas_guardadas": 0, 
            "existentes_eliminadas": noticias_eliminadas, 
            "mensaje": "No se encontraron noticias nuevas válidas",
            "categorias_procesadas": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    print(f"\n📝 Procesando y guardando {len(todas_las_noticias)} NOTICIAS NUEVAS...\n")
    
    noticias_guardadas = 0
    noticias_fallidas = 0
    noticias_rechazadas = 0  
    
    for art in tqdm(todas_las_noticias, desc="Procesando noticias"):
        try:
            print(f"\n🔍 Procesando: {art.get('title')[:60]}...")
            
            texto_completo = scrapear_texto_robusto(
                art.get("url"), 
                art.get("description")
            )
            
            if not texto_completo:
                print(f"⚠️ Sin contenido para: {art.get('title')[:60]}...")
                noticias_fallidas += 1
                continue
                
            print(f"✅ Contenido obtenido: {len(texto_completo.split())} palabras")
            
            resumen = resumir_texto_robusto(texto_completo, art.get("title"))
            
            if not es_resumen_valido(resumen):
                print(f"🚫 RESUMEN INVÁLIDO - Rechazando noticia: {resumen[:50]}...")
                noticias_rechazadas += 1
                continue
            
            if not all([art.get("title"), art.get("url"), art.get("publishedAt")]):
                print(f"⚠️ Datos incompletos para: {art.get('title')[:60]}...")
                noticias_fallidas += 1
                continue

            try:
                fecha_obj = datetime.strptime(art.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ")
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                fecha_formateada = datetime.now().strftime("%Y-%m-%d")

            noticia = {
                "titulo": art.get("title").strip(),
                "url": art.get("url"),
                "categoria": art.get("categoria_asignada", "General"),
                "imagen": art.get("image", ""),
                "fuente": art.get("source", {}).get("name", "Desconocida"),
                "fecha": fecha_formateada,
                "resumen": resumen,
                "titulo_hash": generar_hash_titulo(art.get("title"))
            }

            db.insert_noticia(noticia)
            noticias_guardadas += 1
            print(f"✅ Guardada: {art.get('title')[:70]}...")
            
        except Exception as e:
            print(f"❌ Error guardando noticia: {e}")
            noticias_fallidas += 1
            continue

    try:
        print("\n🗑️  Ejecutando limpieza de noticias antiguas...")
        db.delete_old_noticias(max_months=6)
    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")
    
    print(f"\n🎯 PROCESO COMPLETADO")
    print("=" * 50)
    print(f"✅ Noticias guardadas: {noticias_guardadas}")
    print(f"🧹 Noticias existentes eliminadas: {noticias_eliminadas}")
    print(f"🚫 Noticias rechazadas (resumen inválido): {noticias_rechazadas}")
    print(f"❌ Noticias fallidas: {noticias_fallidas}")
    print(f"📊 Categorías procesadas: {categorias_procesadas}/{len(CATEGORIAS)}")
    
    stats = db.get_stats()
    print(f"📈 Total en base de datos: {stats['total_noticias']} noticias")
    print(f"👆 Total de clics: {stats['total_clics']}")
    print(f"📅 Noticias hoy: {stats['noticias_hoy']}")
    
    return {
        "nuevas_guardadas": noticias_guardadas,
        "existentes_eliminadas": noticias_eliminadas,
        "noticias_rechazadas": noticias_rechazadas,
        "noticias_fallidas": noticias_fallidas,
        "categorias_procesadas": categorias_procesadas,
        "total_noticias": stats['total_noticias'],
        "total_clics": stats['total_clics'],
        "noticias_hoy": stats['noticias_hoy'],
        "timestamp": datetime.now().isoformat(),
        "proceso_exitoso": True
    }

def ejecutar_crawler():
    """Función que ejecuta el crawler y retorna resultados para el endpoint."""
    print("🚀 INICIANDO CRAWLER DESDE ENDPOINT")
    print("=" * 60)
    
    try:
        resultado = procesar_y_guardar_noticias()
        print("🎯 CRAWLER COMPLETADO EXITOSAMENTE")
        return resultado
    except Exception as e:
        print(f"❌ ERROR EN CRAWLER: {e}")
        return {
            "error": str(e), 
            "nuevas_guardadas": 0,
            "existentes_eliminadas": 0,
            "noticias_rechazadas": 0,
            "noticias_fallidas": 0,
            "categorias_procesadas": 0,
            "timestamp": datetime.now().isoformat(),
            "proceso_exitoso": False
        }

if __name__ == "__main__":
    ejecutar_crawler()