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

MAX_NOTICIAS_POR_CATEGORIA = 2
TIEMPO_ESPERA_ENTRE_REQUESTS = 2
MAX_PALABRAS_RESUMEN = 350
MAX_PALABRAS_SCRAPING = 600
MIN_PALABRAS_CONTENIDO_VALIDO = 50
MIN_PALABRAS_RESUMEN_SIGNIFICATIVO = 80

def generar_hash_titulo(titulo):
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()



def obtener_noticias_por_categoria(categoria, max_noticias=MAX_NOTICIAS_POR_CATEGORIA, urls_existentes=None):
    if urls_existentes is None:
        urls_existentes = set()
    
    print(f"📡 Buscando {max_noticias} noticias NUEVAS de: '{CATEGORIAS.get(categoria, categoria)}'...")
    
    noticias_nuevas = []
    urls_encontradas = set()
    
    try:
        url = (f"https://gnews.io/api/v4/top-headlines?"
               f"category={categoria}&lang=es&max={max_noticias * 3}&apikey={GNEWS_API_KEY}")
        
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
            

            if (url_noticia not in urls_existentes and 
                url_noticia not in urls_encontradas and
                len(articulo.get("title", "").strip()) > 10 and
                len(articulo.get("description", "").strip()) > 50):
                
                if not db.noticia_existe(articulo.get("title"), url_noticia):
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
    """Scraping robusto con múltiples métodos de extracción"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    

    try:
        downloaded = trafilatura.fetch_url(url, headers=headers)
        if downloaded:
            content = trafilatura.extract(
                downloaded, 
                include_comments=False, 
                include_tables=False,
                no_fallback=True
            )
            if content and len(content.split()) > 100:
                print(f"✅ Trafilatura: {len(content.split())} palabras")

                return ' '.join(content.split()[:MAX_PALABRAS_SCRAPING])
    except Exception as e:
        print(f"⚠️ Trafilatura falló: {e}")


    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectores = [
            'article .article-content', 'article .story-content', '.news-content',
            '.entry-content', '.post-content', '[class*="content"]',
            'article p', '.article-body', '.news-body'
        ]
        
        for selector in selectores:
            elements = soup.select(selector)
            if elements:
                text_content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(text_content.split()) > 100:
                    print(f"✅ BeautifulSoup con selector '{selector}': {len(text_content.split())} palabras")
                    return ' '.join(text_content.split()[:MAX_PALABRAS_SCRAPING])
        

        paragraphs = soup.find_all('p')
        if paragraphs:
            text_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            if len(text_content.split()) > 100:
                print(f"✅ Fallback párrafos: {len(text_content.split())} palabras")
                return ' '.join(text_content.split()[:MAX_PALABRAS_SCRAPING])
                
    except Exception as e:
        print(f"⚠️ BeautifulSoup falló: {e}")


    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        clean = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        text = re.sub(clean, ' ', response.text)
        
        text = ' '.join(text.split())
        

        if len(text.split()) > 300: 
            print(f"✅ Regex cleaning (fallback robusto): {len(text.split())} palabras")
            return ' '.join(text.split()[:800]) 
        else:
            print(f"⚠️ Regex cleaning: contenido insuficiente/ruido ({len(text.split())} palabras)")
            
    except Exception as e:
        print(f"⚠️ Regex cleaning falló: {e}")


    print(f"❌ Todos los métodos fallaron, usando descripción: {len(fallback_description.split()) if fallback_description else 0} palabras")
    return fallback_description if fallback_description and len(fallback_description.split()) > 30 else None

def validar_contenido_noticia(texto, titulo):
    """Valida que el contenido sea realmente una noticia y no código/ruido"""

    if not texto or len(texto.split()) < MIN_PALABRAS_CONTENIDO_VALIDO:
        return False
    

    patrones_no_deseados = [
        r'<!DOCTYPE', r'<html', r'<head>', r'<body>', r'function\s*\(',
        r'var\s+', r'const\s+', r'let\s+', r'classList\.', r'addEventListener',
        r'@media', r'font-family', r'background-color', r'padding:',
        r'margin:', r'display:\s*(flex|block|inline)', r'position:',
        r'z-index:', r'window\.', r'document\.', r'\.getElementById',
        r'\.querySelector', r'\.addClass', r'\.removeClass'
    ]
    
    for patron in patrones_no_deseados:
        if re.search(patron, texto, re.IGNORECASE):
            print(f"⚠️ Contenido rechazado por patrón: {patron}")
            return False
    

    palabras_clave_noticia = ['anunció', 'confirmó', 'informó', 'declaró', 'según', 'fuentes', 
                              'investigación', 'estudio', 'datos', 'informe', 'autoridades',
                              'gobierno', 'empresa', 'mercado', 'economía', 'política']
    
    palabras_encontradas = sum(1 for palabra in palabras_clave_noticia if palabra in texto.lower())
    
    return palabras_encontradas >= 2

def resumir_texto_robusto(texto, titulo):
    """Genera resúmenes robustos con validación de contenido"""
    
    
    if not validar_contenido_noticia(texto, titulo):
        print("❌ Contenido no válido para resumir")
        return "Resumen no disponible - contenido insuficiente"
    

    if len(texto.split()) < MIN_PALABRAS_RESUMEN_SIGNIFICATIVO:
        return "Contenido insuficiente para generar un resumen significativo."
    

    if len(texto.split()) > MAX_PALABRAS_SCRAPING:
        texto = ' '.join(texto.split()[:MAX_PALABRAS_SCRAPING])
        print(f"✂️ Texto recortado para resumen a {MAX_PALABRAS_SCRAPING} palabras.")

    
    prompt = f"""
# CONTEXTO Y ROL
Eres un periodista senior especializado en crear resúmenes ejecutivos para medios de comunicación. Tu tarea es transformar el texto proporcionado en un resumen periodístico de alta calidad.

# TÍTULO DE LA NOTICIA: {titulo}

# INSTRUCCIONES ESTRICTAS
## FORMATO:
- EXCLUSIVAMENTE un párrafo continuo
- SIN saltos de línea, viñetas, números o encabezados
- LONGITUD: 200-330 palabras (NUNCA exceder {MAX_PALABRAS_RESUMEN} palabras)
- Lenguaje 100% en español

## CONTENIDO PERIODÍSTICO:
Aplica la técnica de las **5W+H** de forma implícita:
- **QUÉ**: Evento principal/descubrimiento/anuncio
- **QUIÉN**: Actores principales (personas, empresas, instituciones)
- **CUÁNDO**: Marco temporal relevante
- **DÓNDE**: Ubicación/contexto geográfico
- **POR QUÉ**: Causas o motivos subyacentes
- **CÓMO**: Metodología o desarrollo del evento

## ESTILO Y TONO:
- Lenguaje formal pero accesible
- Objetividad absoluta: cero opiniones, cero adjetivos valorativos
- Densidad informativa: máxima información en mínimo espacio
- Coherencia temporal: mantener secuencia lógica de eventos
- Eliminar redundancias y información secundaria

## CRITERIOS DE CALIDAD:
✅ PRIORIZAR: Impacto, relevancia, consecuencias
✅ MENCIONAR: Cifras, datos concretos, fechas clave
✅ ESTRUCTURAR: De lo general a lo específico
❌ ELIMINAR: Lenguaje promocional, sensacionalismo, juicios de valor
❌ EVITAR: Repeticiones, información trivial, anécdotas irrelevantes

# TEXTO ORIGINAL PARA RESUMIR:
{texto}

# RESULTADO ESPERADO:
[Tu resumen periodístico aquí, en un solo párrafo continuo]
"""
    
    try:
        response = model.generate_content(prompt)
        resumen = response.text.strip()
        

        if len(resumen.split()) < 50 or len(resumen.split()) > MAX_PALABRAS_RESUMEN:
            raise ValueError(f"Resumen fuera de los límites de longitud ({len(resumen.split())} palabras)")
            
        print(f"✅ Resumen generado: {len(resumen.split())} palabras")
        return resumen
        
    except Exception as e:
        print(f"⚠️ Error al generar resumen con Gemini: {repr(e)}")
        
        sentences = re.split(r'[.!?]+', texto)
        meaningful_sentences = [s.strip() for s in sentences if len(s.split()) > 8][:5]
        fallback = ". ".join(meaningful_sentences) + "."
        return fallback if len(fallback) > 50 else "Resumen no disponible por limitaciones técnicas."

def procesar_y_guardar_noticias():
    """Proceso principal robusto de obtención y procesamiento de noticias"""
    
    db.inicializar_db()
    
    print("🕒 Iniciando proceso de obtención de noticias...")
    print("=" * 60)
    print(f"📊 Hora de ejecución: {datetime.now()}")
    
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
            "mensaje": "No se encontraron noticias nuevas válidas",
            "categorias_procesadas": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    print(f"\n📝 Procesando y guardando {len(todas_las_noticias)} NOTICIAS NUEVAS...\n")
    
    noticias_guardadas = 0
    noticias_fallidas = 0
    
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
        print("\n🗑️  Ejecutando limpieza de noticias antiguas...")
        db.delete_old_noticias(max_months=6)
    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")
    
    print(f"\n🎯 PROCESO COMPLETADO")
    print("=" * 50)
    print(f"✅ Noticias guardadas: {noticias_guardadas}")
    print(f"❌ Noticias fallidas: {noticias_fallidas}")
    print(f"📊 Categorías procesadas: {categorias_procesadas}/{len(CATEGORIAS)}")
    
    stats = db.get_stats()
    print(f"📈 Total en base de datos: {stats['total_noticias']} noticias")
    print(f"👆 Total de clics: {stats['total_clics']}")
    print(f"📅 Noticias hoy: {stats['noticias_hoy']}")
    
    return {
        "nuevas_guardadas": noticias_guardadas,
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
            "noticias_fallidas": 0,
            "categorias_procesadas": 0,
            "timestamp": datetime.now().isoformat(),
            "proceso_exitoso": False
        }

if __name__ == "__main__":
    ejecutar_crawler()