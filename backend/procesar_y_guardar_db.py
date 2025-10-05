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


load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


NOTICIAS_POR_CATEGORIA = 1  
EJECUCIONES_POR_DIA = 4   
TIEMPO_ESPERA_ENTRE_REQUESTS = 3 

if not GNEWS_API_KEY or not GEMINI_API_KEY:
    raise ValueError("⚠️ Asegúrate de configurar GNEWS_API_KEY y GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CATEGORIAS = {
    "business": "Negocios", 
    "entertainment": "Entretenimiento", 
    "health": "Salud",
    "science": "Ciencia", 
    "sports": "Deportes", 
    "technology": "Tecnología",
}


def generar_hash_titulo(titulo):
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()


def obtener_noticias_por_categoria(categoria, max_noticias=NOTICIAS_POR_CATEGORIA, urls_existentes=None):
    if urls_existentes is None:
        urls_existentes = set()
   
    print(f"📡 Buscando {max_noticias} noticia de: '{CATEGORIAS.get(categoria, categoria)}'...")
   
    noticias_nuevas = []
    urls_encontradas = set()
   

    url = (f"https://gnews.io/api/v4/top-headlines?"
           f"category={categoria}&lang=es&max=5&apikey={GNEWS_API_KEY}")
   
    try:

        sleep(TIEMPO_ESPERA_ENTRE_REQUESTS)
        
        resp = requests.get(url, timeout=15)
        

        if resp.status_code == 429:
            print(f"⏳ Rate limit alcanzado para {categoria}, esperando 15 segundos...")
            sleep(15)
            return []
            
        if resp.status_code != 200:
            print(f"⚠️ Código {resp.status_code} para {categoria}, continuando...")
            return []
            
        resp.raise_for_status()
        data = resp.json()
        articulos = data.get("articles", [])
       
        for articulo in articulos:
            if (articulo.get("url") and
                articulo.get("url") not in urls_existentes and
                articulo.get("url") not in urls_encontradas and
                articulo.get("title")):
               
                titulo = articulo.get("title")
                if not db.noticia_existe(titulo, articulo.get("url")):
                    articulo['categoria_asignada'] = CATEGORIAS.get(categoria, "General")
                    noticias_nuevas.append(articulo)
                    urls_encontradas.add(articulo.get("url"))
                   
  
                    if len(noticias_nuevas) >= max_noticias:
                        break
       
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout al obtener noticias de {categoria}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en {categoria}: {e}")
    except Exception as e:
        print(f"⚠️ Error inesperado en {categoria}: {e}")
   
    resultado = "✅" if noticias_nuevas else "❌"
    print(f"{resultado} {len(noticias_nuevas)} noticia para '{CATEGORIAS.get(categoria, categoria)}'")
    return noticias_nuevas


def scrapear_texto(url, fallback_description=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
       
        text = response.text
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        text = ' '.join(text.split()[:500])
       
        return text if len(text) > 100 else fallback_description
           
    except Exception as e:
        print(f"⚠️ Error en scraping para {url}: {e}")
        return fallback_description


def resumir_texto(texto):
    if not texto or len(texto.split()) < 30:
        return "Contenido insuficiente para generar un resumen."

    if len(texto) > 8000: 
        texto = texto[:8000]

    prompt = f"""
    Resumen objetivo en español (máximo 200 palabras) del siguiente texto:
    {texto}
    """
    
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ Error al generar resumen: {repr(e)}")
        sentences = texto.split('.')
        fallback = ". ".join(sentences[:3]) + "."
        return fallback if len(fallback) > 20 else "Resumen no disponible."


def procesar_y_guardar_noticias():
    db.inicializar_db()
    
    print("🕒 Iniciando proceso de obtención de noticias...")
    print(f"🎯 Objetivo: {NOTICIAS_POR_CATEGORIA} noticia por cada {len(CATEGORIAS)} categorías")
    
    urls_existentes = db.obtener_urls_existentes()
    print(f"📊 Noticias existentes en la base de datos: {len(urls_existentes)}")
   
    todas_las_noticias = []
    

    for i, categoria_api in enumerate(CATEGORIAS.keys()):
        print(f"\n📍 [{i+1}/{len(CATEGORIAS)}] Procesando: {CATEGORIAS[categoria_api]}")
        
        noticias_de_categoria = obtener_noticias_por_categoria(
            categoria_api,
            max_noticias=NOTICIAS_POR_CATEGORIA,
            urls_existentes=urls_existentes
        )
        todas_las_noticias.extend(noticias_de_categoria)
        

        if i < len(CATEGORIAS) - 1:
            sleep(2) 
    
    if not todas_las_noticias:
        print("❌ No se encontraron noticias NUEVAS en esta ejecución.")
        return {
            "nuevas_guardadas": 0, 
            "mensaje": "No se encontraron noticias nuevas",
            "ejecucion": f"{len(todas_las_noticias)}/{len(CATEGORIAS)} categorías"
        }
   
    print(f"\n📝 Procesando {len(todas_las_noticias)} noticias nuevas...")
   
    noticias_guardadas = 0
    for art in tqdm(todas_las_noticias, desc="Guardando"):
        texto_completo = art.get("description") or ""
       

        if not texto_completo or len(texto_completo.split()) < 25:
            texto_completo = scrapear_texto(art.get("url"), art.get("description"))
       
        if not texto_completo or len(texto_completo.split()) < 20:
            continue
           
        resumen = resumir_texto(texto_completo)

        if all([art.get("title"), art.get("url"), art.get("publishedAt")]):
            try:
                fecha_obj = datetime.strptime(art.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ")
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
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
                print(f"⚠️ Duplicado: {art.get('title')[:50]}...")
                continue
    

    db.delete_old_noticias(max_months=3)
   
    print(f"\n✅ ¡Ejecución completada! Se guardaron {noticias_guardadas} noticias nuevas")
   
    stats = db.get_stats()
    print(f"📈 Total en base de datos: {stats['total_noticias']}")
    print(f"📊 Noticias de hoy: {stats['noticias_hoy']}")
   
    return {
        "nuevas_guardadas": noticias_guardadas,
        "total_noticias": stats['total_noticias'],
        "total_clics": stats['total_clics'],
        "noticias_hoy": stats['noticias_hoy'],
        "categorias_exitosas": f"{noticias_guardadas}/{len(CATEGORIAS)}",
        "proxima_ejecucion": f"En ~6 horas ({EJECUCIONES_POR_DIA}x día)"
    }


def ejecutar_crawler():
    """Función que ejecuta el crawler y retorna resultados para el endpoint."""
    print("🚀 INICIANDO CRAWLER - ESTRATEGIA DISTRIBUIDA")
    print("=" * 50)
    print(f"🎯 Configuración: {NOTICIAS_POR_CATEGORIA} noticia × {len(CATEGORIAS)} categorías")
    print(f"📅 Frecuencia: {EJECUCIONES_POR_DIA} veces al día")
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