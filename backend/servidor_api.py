from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import datetime
import hashlib
import json
import random
import os

# Importar nuestro módulo de base de datos Supabase
import db
from procesar_y_guardar_db import ejecutar_crawler

app = Flask(__name__)
CORS(app)

# ---------------------------
#   CACHÉ DE TRADUCCIONES APOD
# ---------------------------
def get_user_ip():
    """Obtiene la IP real del usuario."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

# ---------------------------
#   VARIABLES EN MEMORIA - FRASE DEL DÍA
# ---------------------------
frase_cache = {
    "date": None,
    "frase": None
}

# API externa de frases en español (sin token)
EXTERNAL_QUOTES_API = "https://frasedeldia.azurewebsites.net/api/phrase"

# Frases de respaldo en caso de que falle la API
FRASES_RESPALDO = [
    {"texto": "La educación es el arma más poderosa para cambiar el mundo.", "autor": "Nelson Mandela"},
    {"texto": "El único modo de hacer un gran trabajo es amar lo que haces.", "autor": "Steve Jobs"},
    {"texto": "No cuentes los días, haz que los días cuenten.", "autor": "Muhammad Ali"},
    {"texto": "La vida es lo que pasa mientras estás ocupado haciendo otros planes.", "autor": "John Lennon"},
    {"texto": "El éxito es la suma de pequeños esfuerzos repetidos día tras día.", "autor": "Robert Collier"}
]

# ---------------------------
#   RUTAS PRINCIPALES
# ---------------------------

@app.route("/api/noticias", methods=["GET"])
def get_noticias():
    """Obtiene todas las noticias ordenadas por fecha."""
    try:
        limit = request.args.get('limit', type=int)
        noticias = db.get_noticias(limit=limit)
        return jsonify(noticias)
    except Exception as e:
        print(f"❌ Error obteniendo noticias: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/popular-posts", methods=["GET"])
def get_popular_posts():
    """Obtiene posts populares con filtrado opcional."""
    try:
        exclude_id = request.args.get('exclude', type=int)
        limit = request.args.get('limit', 5, type=int)
        
        popular_posts = db.get_popular_posts(limit=limit, exclude_id=exclude_id)
        return jsonify(popular_posts)
    except Exception as e:
        print(f"❌ Error obteniendo posts populares: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/random-posts", methods=["GET"])
def get_random_posts():
    """Obtiene noticias aleatorias."""
    try:
        random_news = db.get_random_posts()
        if not random_news:
            return jsonify({"message": "No se encontraron noticias aleatorias."}), 404
        return jsonify(random_news)
    except Exception as e:
        print(f"❌ Error obteniendo noticias aleatorias: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/latest-by-category", methods=["GET"])
def get_latest_by_category():
    """Obtiene la última noticia de cada categoría."""
    try:
        latest_news_list = db.get_latest_by_category()
        return jsonify(latest_news_list)
    except Exception as e:
        print(f"❌ Error obteniendo últimas noticias por categoría: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/noticias/<int:noticia_id>/click", methods=["POST"])
def registrar_clic(noticia_id):
    """Registra un clic en una noticia."""
    try:
        success = db.increment_clics(noticia_id)
        if success:
            return jsonify({"status": "success", "message": f"Clic registrado para la noticia {noticia_id}"})
        else:
            return jsonify({"status": "error", "message": "Error registrando clic"}), 500
    except Exception as e:
        print(f"❌ Error registrando clic: {e}")
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

@app.route("/api/related-posts", methods=["GET"])
def get_related_posts():
    """Obtiene noticias relacionadas por categoría."""
    try:
        categoria = request.args.get('categoria')
        exclude_id = request.args.get('exclude', type=int)
        limit = request.args.get('limit', 3, type=int)
        
        if not categoria:
            return jsonify({"error": "Parámetro 'categoria' requerido"}), 400
        
        related_posts = db.get_related_posts(categoria, exclude_id, limit)
        return jsonify(related_posts)
    except Exception as e:
        print(f"❌ Error obteniendo posts relacionados: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/posts-by-source", methods=["GET"])
def get_posts_by_source():
    """Obtiene noticias por fuente."""
    try:
        fuente = request.args.get('fuente')
        limit = request.args.get('limit', 10, type=int)
        
        if not fuente:
            return jsonify({"error": "Parámetro 'fuente' requerido"}), 400
        
        posts = db.get_posts_by_source(fuente, limit)
        return jsonify(posts)
    except Exception as e:
        print(f"❌ Error obteniendo posts por fuente: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ---------------------------
#   NUEVO ENDPOINT PARA PROCESAR NOTICIAS
# ---------------------------

@app.route('/procesar', methods=['GET'])
def procesar_noticias_externo():
    """Endpoint para ejecutar el crawler de noticias desde externo."""
    
    # Opcional: agregar seguridad con una clave secreta
    secret_key = request.headers.get('X-Secret-Key')
    expected_key = os.environ.get('CRON_SECRET')
    
    if expected_key and secret_key != expected_key:
        return jsonify({"error": "Acceso denegado"}), 403

    try:
        print("🔄 Iniciando proceso de crawler desde endpoint externo...")
        
        # Ejecutar el crawler
        resultado = ejecutar_crawler()
        
        # Si hay error en el crawler
        if "error" in resultado:
            return jsonify({"error": f"Error en el crawler: {resultado['error']}"}), 500
        
        # Éxito
        return jsonify({
            "mensaje": "Crawler ejecutado con éxito", 
            "data": resultado,
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error ejecutando crawler: {str(e)}")
        return jsonify({"error": f"Error al ejecutar el crawler: {str(e)}"}), 500

# ---------------------------
#   RUTA FRASE DEL DÍA MEJORADA
# ---------------------------
@app.route("/api/frase-del-dia", methods=["GET"])
def frase_del_dia():
    """Devuelve una frase del día (la misma para todos durante ese día)."""
    today = datetime.date.today().isoformat()

    # Si ya tenemos una frase guardada de hoy → la devolvemos
    if frase_cache["date"] == today and frase_cache["frase"]:
        print(f"✅ Devolviendo frase en caché para hoy: {today}")
        return jsonify(frase_cache["frase"])

    # Si no, intentamos obtener una nueva de la API externa
    try:
        print("🔄 Intentando obtener frase de la API externa...")
        response = requests.get(EXTERNAL_QUOTES_API, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"📝 Respuesta de la API: {data}")

        # Verificar la estructura de la respuesta
        if isinstance(data, dict):
            # Si es un diccionario, usar las claves esperadas
            texto = data.get("phrase") or data.get("texto") or data.get("frase")
            autor = data.get("author") or data.get("autor")
        elif isinstance(data, str):
            # Si es un string, usarlo como texto
            texto = data
            autor = "Anónimo"
        else:
            texto = None
            autor = None

        if texto:
            nueva_frase = {
                "texto": texto,
                "autor": autor or "Anónimo"
            }
        else:
            # Si no podemos obtener datos válidos, usar respaldo
            raise ValueError("Estructura de respuesta no reconocida")

        # Guardamos en caché
        frase_cache["date"] = today
        frase_cache["frase"] = nueva_frase

        print(f"✅ Nueva frase obtenida y guardada en caché: {nueva_frase}")
        return jsonify(nueva_frase)

    except Exception as e:
        print(f"❌ Error obteniendo frase externa: {str(e)}")
        print("🔄 Usando frase de respaldo...")
        
        # Usar una frase de respaldo (seleccionada por el día para consistencia)
        random.seed(today)  # Para que sea la misma para todos hoy
        frase_respaldo = random.choice(FRASES_RESPALDO)
        
        # Guardar en caché igualmente para hoy
        frase_cache["date"] = today
        frase_cache["frase"] = frase_respaldo
        
        return jsonify(frase_respaldo)

# ---------------------------
#   RUTA TRADUCCIÓN APOD CON CACHÉ
# ---------------------------
@app.route("/api/translate-apod", methods=["POST"])
def translate_apod():
    """Traduce el APOD una sola vez por usuario por día."""
    data = request.json
    title = data.get("title")
    explanation = data.get("explanation")
    apod_date = data.get("date")  # Fecha del APOD
    
    if not title or not explanation or not apod_date:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    # Obtener IP del usuario
    user_ip = get_user_ip()
    
    # Crear hash del contenido para verificar cambios
    content_hash = hashlib.md5(f"{title}{explanation}".encode()).hexdigest()
    
    # Verificar si ya existe una traducción para este usuario y esta fecha
    cached_translation = db.get_cached_apod_translation(apod_date, user_ip)
    if cached_translation:
        print(f"✅ Devolviendo traducción en caché para IP: {user_ip}")
        return jsonify({
            "translatedTitle": cached_translation["translated_title"],
            "translatedExplanation": cached_translation["translated_explanation"],
            "fromCache": True
        })
    
    # Si no está en caché, traducir
    try:
        # Traducir título y explicación
        url = "https://api.mymemory.translated.net/get"
        
        # Traducir título
        title_response = requests.get(url, params={"q": title, "langpair": "en|es"})
        title_response.raise_for_status()
        translated_title = title_response.json()["responseData"]["translatedText"]
        
        # Traducir explicación en chunks si es muy larga
        explanation_chunks = []
        chunk_size = 500
        for i in range(0, len(explanation), chunk_size):
            chunk = explanation[i:i + chunk_size]
            chunk_response = requests.get(url, params={"q": chunk, "langpair": "en|es"})
            chunk_response.raise_for_status()
            explanation_chunks.append(chunk_response.json()["responseData"]["translatedText"])
        
        translated_explanation = " ".join(explanation_chunks)
        
        # Guardar en caché
        db.save_apod_translation(
            apod_date, 
            content_hash, 
            translated_title, 
            translated_explanation, 
            user_ip
        )
        
        print(f"✅ Traducción nueva guardada en caché para IP: {user_ip}")
        
        return jsonify({
            "translatedTitle": translated_title,
            "translatedExplanation": translated_explanation,
            "fromCache": False
        })
        
    except Exception as e:
        print(f"❌ Error en traducción: {e}")
        return jsonify({
            "translatedTitle": title,
            "translatedExplanation": explanation,
            "fromCache": False,
            "error": str(e)
        }), 500

# ---------------------------
#   RUTAS ADICIONALES PARA MEJOR FUNCIONALIDAD
# ---------------------------

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Obtiene todas las categorías disponibles."""
    try:
        categories = db.get_categories()
        return jsonify(categories)
    except Exception as e:
        print(f"❌ Error obteniendo categorías: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/sources", methods=["GET"])
def get_sources():
    """Obtiene todas las fuentes disponibles."""
    try:
        sources = db.get_sources()
        return jsonify(sources)
    except Exception as e:
        print(f"❌ Error obteniendo fuentes: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Obtiene estadísticas generales."""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/search", methods=["GET"])
def search_noticias():
    """Busca noticias por término."""
    try:
        query = request.args.get('q', '')
        tipo = request.args.get('type', 'titulo')  # titulo, fuente, categoria
        
        if not query:
            return jsonify({"error": "Parámetro 'q' requerido"}), 400
        
        results = db.search_noticias(query, tipo)
        return jsonify(results)
    except Exception as e:
        print(f"❌ Error buscando noticias: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ---------------------------
#   HEALTH CHECK
# ---------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Endpoint para verificar el estado del servidor."""
    try:
        # Verificar conexión a Supabase
        db.get_noticias(limit=1)
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route("/")
def home():
    """Página de inicio de la API."""
    return jsonify({
        "message": "Bienvenido a la API de Noticias",
        "version": "1.0",
        "database": "Supabase",
        "endpoints": {
            "noticias": "/api/noticias",
            "popular_posts": "/api/popular-posts",
            "random_posts": "/api/random-posts",
            "related_posts": "/api/related-posts",
            "frase_del_dia": "/api/frase-del-dia",
            "stats": "/api/stats",
            "health": "/api/health",
            "procesar": "/procesar (GET) - Ejecuta el crawler de noticias"
        }
    })

if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask con Supabase en http://localhost:5000")
    print("📊 Endpoints disponibles:")
    print("   - GET  /api/noticias")
    print("   - GET  /api/popular-posts")
    print("   - GET  /api/random-posts") 
    print("   - GET  /api/related-posts")
    print("   - GET  /api/frase-del-dia")
    print("   - POST /api/translate-apod")
    print("   - POST /api/noticias/<id>/click")
    print("   - GET  /api/health")
    print("   - GET  /procesar - Ejecuta el crawler de noticias")
    app.run(debug=True, port=5000)