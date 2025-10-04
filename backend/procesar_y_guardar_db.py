import os
import requests
from newspaper import Article, ArticleException
from dotenv import load_dotenv
import google.generativeai as genai
from time import sleep
from tqdm import tqdm
from datetime import datetime
import hashlib

# Importar nuestro módulo de base de datos Supabase
import db

# --- Carga y configuración ---
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GNEWS_API_KEY or not GEMINI_API_KEY:
    raise ValueError("⚠️  Asegúrate de configurar GNEWS_API_KEY y GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CATEGORIAS = {
    "business": "Negocios", "entertainment": "Entretenimiento", "health": "Salud",
    "science": "Ciencia", "sports": "Deportes", "technology": "Tecnología",
}

# --- Función para generar hash del título ---
def generar_hash_titulo(titulo):
    """Genera un hash único del título para detectar duplicados."""
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()

# --- Obtener noticias por categoría EVITANDO DUPLICADOS ---
def obtener_noticias_por_categoria(categoria, max_noticias=3, urls_existentes=None):
    """Obtiene titulares de GNews para una categoría específica, evitando duplicados."""
    if urls_existentes is None:
        urls_existentes = set()
    
    print(f"📡 Buscando {max_noticias} noticias NUEVAS de: '{CATEGORIAS.get(categoria, categoria)}'...")
    
    # Intentar con diferentes queries para obtener noticias diferentes
    queries_alternativas = [
        None,  # Sin query (noticias principales)
        "actualidad",
        "última hora",
        "hoy"
    ]
    
    noticias_nuevas = []
    urls_encontradas = set()
    
    for query in queries_alternativas:
        if len(noticias_nuevas) >= max_noticias:
            break
            
        url = (f"https://gnews.io/api/v4/top-headlines?"
               f"category={categoria}&lang=es&max={max_noticias * 2}&apikey={GNEWS_API_KEY}")
        
        if query:
            url += f"&q={query}"
        
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            articulos = data.get("articles", [])
            
            for articulo in articulos:
                if (articulo.get("url") and 
                    articulo.get("url") not in urls_existentes and
                    articulo.get("url") not in urls_encontradas and
                    articulo.get("title")):
                    
                    # Verificar también por título (evitar mismos titulares con URLs diferentes)
                    titulo = articulo.get("title")
                    if not db.noticia_existe(titulo, articulo.get("url")):
                        articulo['categoria_asignada'] = CATEGORIAS.get(categoria, "General")
                        noticias_nuevas.append(articulo)
                        urls_encontradas.add(articulo.get("url"))
                        
                        if len(noticias_nuevas) >= max_noticias:
                            break
            
            sleep(1)  # Pausa entre requests a la API
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al conectar con GNews para '{categoria}': {e}")
            continue
    
    print(f"✅ Encontradas {len(noticias_nuevas)} noticias nuevas para '{CATEGORIAS.get(categoria, categoria)}'")
    return noticias_nuevas

# --- Scraping del texto ---
def scrapear_texto(url, fallback_description=None):
    """Descarga y parsea el texto completo del artículo usando newspaper3k."""
    try:
        art = Article(url, language="es")
        art.download()
        art.parse()
        return art.text if art.text else fallback_description
    except (ArticleException, Exception):
        return fallback_description

# --- Resumen con Gemini (con fallback manual) ---
def resumir_texto(texto):
    """Genera un resumen del texto usando el modelo Gemini."""
    if not texto or len(texto.split()) < 40:
        return "Contenido insuficiente para generar un resumen."

    # Limitar texto si es muy largo para evitar errores
    if len(texto) > 15000:
        texto = texto[:15000]

    prompt = f"""
    Eres un editor de noticias experto, objetivo y riguroso. Tu única tarea es crear un resumen informativo y de alta calidad del texto proporcionado.
    
    Sigue estas reglas estrictas:
    1. **Formato**: El resumen debe ser un solo párrafo, sin encabezados ni viñetas.
    2. **Longitud**: El resumen no puede superar las 400 palabras. Sé conciso y elimina toda la información secundaria.
    3. **Contenido**: Céntrate exclusivamente en los **hechos clave**: Qué sucedió, Quién o qué está involucrado, Cuándo y dónde ocurrieron los eventos, y Por qué sucedió (si se menciona la causa).
    4. **Tono**: El lenguaje debe ser completamente objetivo. Elimina cualquier opinión, especulación, juicio personal, lenguaje emocional o de 'clickbait'.
    5. **Idioma**: El resumen debe estar en español.

    Texto original:
    ---
    {texto}
    ---
    Resumen objetivo:
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️  Error al generar resumen con Gemini: {repr(e)}")
        # Fallback: tomar las primeras 5 oraciones del texto original si Gemini falla.
        fallback = " ".join(texto.split(".")[:5]) + "..."
        return fallback if fallback.strip() != "..." else "El servicio de resumen no está disponible en este momento."

# --- Procesar y guardar NOTICIAS NUEVAS ---
def procesar_y_guardar_noticias():
    """Ejecuta el proceso completo de obtención, resumen y guardado de noticias NUEVAS."""
    # Inicializar base de datos (compatibilidad)
    db.inicializar_db()
    
    # Obtener URLs existentes para evitar duplicados
    urls_existentes = db.obtener_urls_existentes()
    print(f"📊 Noticias existentes en la base de datos: {len(urls_existentes)}")
    
    todas_las_noticias = []
    for categoria_api in CATEGORIAS.keys():
        noticias_de_categoria = obtener_noticias_por_categoria(
            categoria_api, 
            max_noticias=2, 
            urls_existentes=urls_existentes
        )
        todas_las_noticias.extend(noticias_de_categoria)
        sleep(1)  # Pausa para no saturar la API de GNews

    if not todas_las_noticias:
        print("❌ No se encontraron noticias NUEVAS para procesar. Todas las noticias ya están en la base de datos.")
        return {"nuevas_guardadas": 0, "mensaje": "No se encontraron noticias nuevas"}

    print(f"\n📝 Procesando y guardando {len(todas_las_noticias)} NOTICIAS NUEVAS en Supabase...\n")
    
    noticias_guardadas = 0
    for art in tqdm(todas_las_noticias, desc="Guardando noticias nuevas"):
        texto_completo = scrapear_texto(art.get("url"), art.get("description"))
        
        # Si no hay suficiente texto, saltar esta noticia
        if not texto_completo or len(texto_completo.split()) < 40:
            continue
            
        resumen = resumir_texto(texto_completo)

        if all([art.get("title"), art.get("url"), art.get("publishedAt")]):
            try:
                # Intenta formatear la fecha correctamente
                fecha_obj = datetime.strptime(art.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ")
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                # Si falla, guarda la fecha tal como viene
                fecha_formateada = art.get("publishedAt", "Fecha no disponible")

            noticia = {
                "titulo": art.get("title"),
                "url": art.get("url"),
                "categoria": art.get("categoria_asignada"),
                "imagen": art.get("image", ""),
                "fuente": art.get("source", {}).get("name", "Desconocida"),
                "fecha": fecha_formateada,
                "resumen": resumen,
                "titulo_hash": generar_hash_titulo(art.get("title"))
            }

            try:
                db.insert_noticia(noticia)
                noticias_guardadas += 1
            except Exception as e:
                # Ignora si la URL o el título ya existen
                print(f"⚠️  Duplicado omitido: {art.get('title')[:50]}... Error: {e}")
                continue
    
    # Limpiar noticias antiguas (mantener sólo las de menos de 6 meses)
    db.delete_old_noticias(max_months=6)
    
    print(f"\n✅ ¡Proceso completado! Se guardaron {noticias_guardadas} NUEVAS noticias en Supabase")
    
    # Mostrar estadísticas actualizadas
    stats = db.get_stats()
    print(f"📈 Total de noticias en la base de datos: {stats['total_noticias']}")
    
    return {
        "nuevas_guardadas": noticias_guardadas,
        "total_noticias": stats['total_noticias'],
        "total_clics": stats['total_clics'],
        "noticias_hoy": stats['noticias_hoy']
    }

# --- FUNCIÓN PARA EL ENDPOINT ---
def ejecutar_crawler():
    """Función que ejecuta el crawler y retorna resultados para el endpoint."""
    print("🚀 INICIANDO CRAWLER DESDE ENDPOINT")
    print("=" * 50)
    
    try:
        resultado = procesar_y_guardar_noticias()
        print("🎯 CRAWLER COMPLETADO EXITOSAMENTE")
        return resultado
    except Exception as e:
        print(f"❌ ERROR EN CRAWLER: {e}")
        return {"error": str(e), "nuevas_guardadas": 0}

if __name__ == "__main__":
    ejecutar_crawler()