from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import datetime
import hashlib
import json
import random
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import threading
import time

import db
from procesar_y_guardar_db import ejecutar_crawler
from chatbot_service import chatbot_service


app = Flask(__name__)

# ==================== CONFIGURACIÓN CORS CORREGIDA ====================
CORS(app, 
     origins=[
         "https://antihumonews.vercel.app",
         "https://www.antihumonews.vercel.app", 
         "http://localhost:5173",
         "http://localhost:3000"
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Secret-Key", "X-Requested-With"],
     supports_credentials=True,
     max_age=600)

# Middleware adicional para asegurar CORS
@app.after_request
def after_request(response):
    """Agregar headers CORS manualmente"""
    origin = request.headers.get('Origin')
    allowed_origins = [
        "https://antihumonews.vercel.app",
        "https://www.antihumonews.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Secret-Key, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        origin = request.headers.get('Origin')
        allowed_origins = [
            "https://antihumonews.vercel.app",
            "https://www.antihumonews.vercel.app", 
            "http://localhost:5173",
            "http://localhost:3000"
        ]
        
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Secret-Key, X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
@app.route("/api/cors-test", methods=["GET", "OPTIONS"])
def cors_test():
    """Endpoint para probar CORS"""
    return jsonify({
        "message": "✅ CORS está funcionando correctamente",
        "allowed_origins": [
            "https://antihumonews.vercel.app",
            "https://www.antihumonews.vercel.app",
            "http://localhost:5173", 
            "http://localhost:3000"
        ],
        "timestamp": datetime.datetime.now().isoformat()
    })

# ---------------------------
#   ESTADO GLOBAL ORGANIZADO
# ---------------------------

APP_STATE = {
    "anti_sleep_activo": False,
    "anti_sleep_timer": None,
    "ultimo_ping": None,
    "frase_cache": {"date": None, "frase": None},
    "scheduler": None
}

# ---------------------------
#   CONFIGURACIÓN DE CONSTANTES
# ---------------------------

EXTERNAL_QUOTES_API = "https://frasedeldia.azurewebsites.net/api/phrase"

FRASES_RESPALDO = [
    {"texto": "La educación es el arma más poderosa para cambiar el mundo.", "autor": "Nelson Mandela"},
    {"texto": "El único modo de hacer un gran trabajo es amar lo que haces.", "autor": "Steve Jobs"},
    {"texto": "No cuentes los días, haz que los días cuenten.", "autor": "Muhammad Ali"},
    {"texto": "La vida es lo que pasa mientras estás ocupado haciendo otros planes.", "autor": "John Lennon"},
    {"texto": "El éxito es la suma de pequeños esfuerzos repetidos día tras día.", "autor": "Robert Collier"}
]

# ---------------------------
#   ANTI-SLEEP INTELIGENTE MEJORADO
# ---------------------------

def activar_anti_sleep():
    """Activa el sistema anti-sleep antes de la ejecución del crawler."""
    if not APP_STATE["anti_sleep_activo"]:
        APP_STATE["anti_sleep_activo"] = True
        print("🔋 ACTIVANDO Sistema Anti-Sleep Inteligente")
        mantener_servidor_activo()

def desactivar_anti_sleep():
    """Desactiva el sistema anti-sleep después del crawler."""
    if APP_STATE["anti_sleep_activo"]:
        APP_STATE["anti_sleep_activo"] = False
        
        # Cancelar timer explícitamente para limpieza de recursos
        if APP_STATE["anti_sleep_timer"]:
            APP_STATE["anti_sleep_timer"].cancel()
            APP_STATE["anti_sleep_timer"] = None
            
        print("🔌 DESACTIVANDO Sistema Anti-Sleep y cancelando Timer")

def mantener_servidor_activo():
    """Hace ping cada 2 minutos durante el período activo."""
    if APP_STATE["anti_sleep_activo"] and os.getenv('ENVIRONMENT') == 'production':
        try:
            # Programar siguiente ejecución en 2 minutos (120 segundos)
            APP_STATE["anti_sleep_timer"] = threading.Timer(120, mantener_servidor_activo)
            APP_STATE["anti_sleep_timer"].start()
            
            # URL de tu propio servidor en Render
            render_url = os.getenv('RENDER_URL')
            if render_url:
                health_url = f"{render_url}/api/health"
                response = requests.get(health_url, timeout=10)
                APP_STATE["ultimo_ping"] = datetime.datetime.now()
                print(f"🔄 Ping anti-sleep: {response.status_code} - {APP_STATE['ultimo_ping'].strftime('%H:%M:%S')}")
            else:
                print("⚠️ RENDER_URL no configurada")
                
        except Exception as e:
            print(f"⚠️ Error en ping anti-sleep: {e}")

# ---------------------------
#   SISTEMA DE FRASE DEL DÍA OPTIMIZADO
# ---------------------------

def actualizar_frase_del_dia():
    """Obtiene la frase del día de la API externa o usa respaldo y la guarda en APP_STATE.
    
    Esta función se ejecuta en segundo plano vía APScheduler.
    """
    today = datetime.date.today().isoformat()
    
    # Si ya se actualizó hoy (p. ej., por una ejecución manual), no hace nada.
    if APP_STATE["frase_cache"]["date"] == today:
        print(f"📝 Frase del día ya actualizada para {today}. Saltando la tarea.")
        return

    try:
        print("🔄 Scheduler: Intentando obtener frase de la API externa...")
        # Usamos un timeout corto, ya que es una tarea de fondo no crítica
        response = requests.get(EXTERNAL_QUOTES_API, timeout=5) 
        response.raise_for_status()
        data = response.json()

        # Lógica de parseo robusta (mantenemos la lógica de tu ruta original)
        if isinstance(data, dict):
            texto = data.get("phrase") or data.get("texto") or data.get("frase")
            autor = data.get("author") or data.get("autor")
        elif isinstance(data, str):
            texto = data
            autor = "Anónimo"
        else:
            raise ValueError("Estructura de respuesta de API no reconocida")

        if texto:
            nueva_frase = {
                "texto": texto,
                "autor": autor or "Anónimo"
            }
        else:
            raise ValueError("No se pudo extraer el texto de la frase")
            
        APP_STATE["frase_cache"]["date"] = today
        APP_STATE["frase_cache"]["frase"] = nueva_frase
        print(f"✅ Frase del día actualizada en caché: {nueva_frase['texto'][:30]}...")

    except Exception as e:
        print(f"❌ Scheduler: Error obteniendo frase externa: {str(e)}")
        print("🔄 Usando frase de respaldo aleatoria...")
        
        # Uso de seed para asegurar que todos los procesos/workers obtengan la misma
        random.seed(today)  
        frase_respaldo = random.choice(FRASES_RESPALDO)
        
        APP_STATE["frase_cache"]["date"] = today
        APP_STATE["frase_cache"]["frase"] = frase_respaldo
        print(f"✅ Frase de respaldo cargada: {frase_respaldo['texto'][:30]}...")

# ---------------------------
#   CONFIGURACIÓN SCHEDULER CON 4 EJECUCIONES DIARIAS + FRASE DEL DÍA
# ---------------------------

def iniciar_scheduler():
    """Inicia el scheduler para ejecutar el crawler 4 veces al día (redundancia) y actualizar la frase."""
    scheduler = BackgroundScheduler()
    
    # Configurar zona horaria Argentina
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    
    # ==================== PRIMER PAR: 12:00 PM ====================
    scheduler.add_job(
        activar_anti_sleep,
        trigger=CronTrigger(hour=11, minute=55, timezone=tz_argentina),
        id='activar_anti_sleep_mediodia'
    )
    
    scheduler.add_job(
        ejecutar_crawler_desde_scheduler,
        trigger=CronTrigger(hour=12, minute=0, timezone=tz_argentina),
        id='crawler_mediodia'
    )
    
    # ==================== SEGUNDO PAR: 12:00 AM ====================
    scheduler.add_job(
        activar_anti_sleep,
        trigger=CronTrigger(hour=23, minute=55, timezone=tz_argentina),
        id='activar_anti_sleep_medianoche'
    )
    
    scheduler.add_job(
        ejecutar_crawler_desde_scheduler,
        trigger=CronTrigger(hour=0, minute=0, timezone=tz_argentina),
        id='crawler_medianoche'
    )
    
    # ==================== TERCER PAR: 6:00 AM (REDUNDANCIA) ====================
    scheduler.add_job(
        activar_anti_sleep,
        trigger=CronTrigger(hour=5, minute=55, timezone=tz_argentina),
        id='activar_anti_sleep_manana_temprano'
    )
    
    scheduler.add_job(
        ejecutar_crawler_desde_scheduler,
        trigger=CronTrigger(hour=6, minute=0, timezone=tz_argentina),
        id='crawler_manana_temprano'
    )
    
    # ==================== CUARTO PAR: 6:00 PM (REDUNDANCIA) ====================
    scheduler.add_job(
        activar_anti_sleep,
        trigger=CronTrigger(hour=17, minute=55, timezone=tz_argentina),
        id='activar_anti_sleep_tarde'
    )
    
    scheduler.add_job(
        ejecutar_crawler_desde_scheduler,
        trigger=CronTrigger(hour=18, minute=0, timezone=tz_argentina),
        id='crawler_tarde'
    )
    
    # ==================== TAREA DIARIA: ACTUALIZAR FRASE DEL DÍA ====================
    scheduler.add_job(
        actualizar_frase_del_dia,
        # Se ejecuta 5 minutos después de medianoche (hora Argentina).
        trigger=CronTrigger(hour=0, minute=5, timezone=tz_argentina), 
        id='actualizar_frase_diaria'
    )
    
    scheduler.start()
    APP_STATE["scheduler"] = scheduler
    print("✅ Scheduler iniciado - 4 ejecuciones diarias con redundancia + Frase diaria.")
    return scheduler

def ejecutar_crawler_desde_scheduler():
    """Función wrapper para ejecutar el crawler desde el scheduler."""
    try:
        print("\n" + "="*60)
        print("🕒 INICIANDO CRAWLER AUTOMÁTICO DESDE SCHEDULER")
        print(f"📅 Fecha/Hora: {datetime.datetime.now()}")
        print("="*60)
        
        resultado = ejecutar_crawler()
        
        print("="*60)
        print("✅ CRAWLER AUTOMÁTICO COMPLETADO")
        print(f"📊 Resultado: {resultado}")
        print("="*60 + "\n")
        
        # Desactivar anti-sleep 10 minutos después del crawler
        threading.Timer(600, desactivar_anti_sleep).start()
        print("⏰ Anti-sleep se desactivará automáticamente en 10 minutos")
        
        return resultado
        
    except Exception as e:
        print(f"❌ ERROR en crawler automático: {e}")
        # Desactivar anti-sleep incluso si hay error
        threading.Timer(600, desactivar_anti_sleep).start()
        return {"error": str(e)}

# Iniciar scheduler cuando el servidor arranque
scheduler = iniciar_scheduler()

# ---------------------------
#   FUNCIONES AUXILIARES MEJORADAS
# ---------------------------

def get_user_ip():
    """Obtiene la IP real del usuario de forma concisa."""
    # Render suele usar X-Real-IP o X-Forwarded-For
    ip = request.headers.get('X-Real-IP')
    if not ip:
        # X-Forwarded-For puede contener múltiples IPs, toma la primera
        ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    
    # Fallback a la IP local si no hay headers HTTP
    return ip or request.remote_addr

# ==================== RUTAS CHATBOT ====================

@app.route("/api/chat", methods=["POST"])
def chat_con_noticia():
    """Endpoint para chat contextual con noticias."""
    try:
        if request.method != 'POST':
            return jsonify({"error": "Método no permitido"}), 405
            
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Datos JSON requeridos"}), 400
        
        pregunta = data.get("pregunta")
        noticia_id = data.get("noticia_id")
        
        # Obtener IP real del usuario
        user_ip = get_user_ip()
        
        print(f"🤖 Pregunta recibida de IP {user_ip}: {pregunta[:50]}...")
        print(f"📰 Noticia ID: {noticia_id}")
        
        if not pregunta or not pregunta.strip():
            return jsonify({"error": "La pregunta es requerida"}), 400
        
        # Validar noticia_id si se proporciona
        noticia_id_int = None
        if noticia_id is not None:
            try:
                noticia_id_int = int(noticia_id)
            except (ValueError, TypeError):
                return jsonify({"error": "noticia_id debe ser un número válido"}), 400
        
        # Generar respuesta usando el servicio CON IP
        resultado = chatbot_service.generar_respuesta(pregunta.strip(), noticia_id_int, user_ip)
        
        print(f"✅ Respuesta generada - Tipo: {resultado['tipo_contexto']}")
        if resultado.get('rate_limit_info'):
            print(f"📊 Rate Limit: {resultado['rate_limit_info']['contador_actual']}/{resultado['rate_limit_info']['limite']}")
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Error en endpoint /api/chat: {e}")
        return jsonify({
            "respuesta": "❌ Error interno del servidor. Por favor, intenta más tarde.",
            "tipo_contexto": "error", 
            "noticia_id": None,
            "noticia_info": "error",
            "titulo_noticia": None,
            "exito": False,
            "modelo": "error"
        }), 500

@app.route("/api/chat/health", methods=["GET"])
def chat_health_check():
    """Health check específico para el chatbot."""
    try:
        test_response = chatbot_service.generar_respuesta("Hola, ¿estás funcionando?", None)
        
        return jsonify({
            "status": "healthy",
            "chatbot": "operational",
            "model": chatbot_service.modelo_actual,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "chatbot": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

# ---------------------------
#   RUTAS PRINCIPALES EXISTENTES
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
#   NUEVO ENDPOINT PARA PROCESAR NOTICIAS (MANUAL)
# ---------------------------

@app.route('/procesar', methods=['GET'])
def procesar_noticias_externo():
    """Endpoint para ejecutar el crawler de noticias desde externo."""
    
    secret_key = request.headers.get('X-Secret-Key')
    expected_key = os.getenv('CRON_SECRET')
    
    if expected_key and secret_key != expected_key:
        return jsonify({"error": "Acceso denegado"}), 403

    try:
        print("🔄 Iniciando proceso de crawler desde endpoint externo...")
        
        # Activar anti-sleep para ejecución manual
        activar_anti_sleep()
        
        resultado = ejecutar_crawler()
        
        # Desactivar anti-sleep después de 10 minutos
        threading.Timer(600, desactivar_anti_sleep).start()
        
        if "error" in resultado:
            return jsonify({"error": f"Error en el crawler: {resultado['error']}"}), 500
        
        return jsonify({
            "mensaje": "Crawler ejecutado con éxito", 
            "data": resultado,
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error ejecutando crawler: {str(e)}")
        # Desactivar anti-sleep incluso si hay error
        threading.Timer(600, desactivar_anti_sleep).start()
        return jsonify({"error": f"Error al ejecutar el crawler: {str(e)}"}), 500

# ---------------------------
#   RUTA FRASE DEL DÍA OPTIMIZADA (INSTANTÁNEA)
# ---------------------------

@app.route("/api/frase-del-dia", methods=["GET"])
def frase_del_dia():
    """Devuelve la frase del día pre-cargada desde el scheduler."""
    today = datetime.date.today().isoformat()

    # Si la caché está vacía o es de ayer (lo cual no debería pasar si el scheduler funciona), 
    # se intenta cargar de forma síncrona como fallback.
    if APP_STATE["frase_cache"]["date"] != today or not APP_STATE["frase_cache"]["frase"]:
        print(f"⚠️ Caché de frase vacía o desactualizada. Forzando actualización síncrona.")
        actualizar_frase_del_dia() # Llama a la función de forma síncrona como FALLBACK

    # Se devuelve el contenido de la caché.
    frase = APP_STATE["frase_cache"]["frase"]
    
    if frase:
        print(f"✅ Devolviendo frase en caché para hoy: {today}")
        return jsonify(frase)
    else:
        # Esto solo pasaría si el fallback síncrono también falla.
        return jsonify({"error": "No se pudo obtener la frase del día"}), 500

# ---------------------------
#   RUTA TRADUCCIÓN APOD CON CACHÉ
# ---------------------------

@app.route("/api/translate-apod", methods=["POST"])
def translate_apod():
    """Traduce el APOD una sola vez por usuario por día."""
    data = request.json
    title = data.get("title")
    explanation = data.get("explanation")
    apod_date = data.get("date") 
    
    if not title or not explanation or not apod_date:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    user_ip = get_user_ip()
    
    content_hash = hashlib.md5(f"{title}{explanation}".encode()).hexdigest()
    
    cached_translation = db.get_cached_apod_translation(apod_date, user_ip)
    if cached_translation:
        print(f"✅ Devolviendo traducción en caché para IP: {user_ip}")
        return jsonify({
            "translatedTitle": cached_translation["translated_title"],
            "translatedExplanation": cached_translation["translated_explanation"],
            "fromCache": True
        })
    
    try:
        url = "https://api.mymemory.translated.net/get"
        
        title_response = requests.get(url, params={"q": title, "langpair": "en|es"}, timeout=10)
        title_response.raise_for_status()
        translated_title = title_response.json()["responseData"]["translatedText"]
        
        explanation_chunks = []
        chunk_size = 500
        for i in range(0, len(explanation), chunk_size):
            chunk = explanation[i:i + chunk_size]
            chunk_response = requests.get(url, params={"q": chunk, "langpair": "en|es"}, timeout=10)
            chunk_response.raise_for_status()
            explanation_chunks.append(chunk_response.json()["responseData"]["translatedText"])
        
        translated_explanation = " ".join(explanation_chunks)
        
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
        tipo = request.args.get('type', 'titulo')  
        
        if not query:
            return jsonify({"error": "Parámetro 'q' requerido"}), 400
        
        results = db.search_noticias(query, tipo)
        return jsonify(results)
    except Exception as e:
        print(f"❌ Error buscando noticias: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ---------------------------
#   HEALTH CHECK MEJORADO
# ---------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Endpoint para verificar el estado del servidor."""
    try:
        # Verificar base de datos
        db.get_noticias(limit=1)
        
        # Verificar chatbot
        chat_status = "operational"
        try:
            test_chat = chatbot_service.generar_respuesta("Test de salud", None)
            chat_status = "operational" if test_chat["exito"] else "degraded"
        except Exception as e:
            chat_status = f"error: {str(e)}"
        
        # Verificar scheduler
        scheduler_status = "running" if scheduler and scheduler.running else "stopped"
        
        # Verificar anti-sleep
        anti_sleep_status = "active" if APP_STATE["anti_sleep_activo"] else "inactive"
        
        # Verificar frase del día
        frase_status = "cached" if APP_STATE["frase_cache"]["frase"] else "empty"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": "connected",
            "chatbot": chat_status,
            "scheduler": scheduler_status,
            "anti_sleep": anti_sleep_status,
            "frase_cache": frase_status,
            "ultimo_ping": APP_STATE["ultimo_ping"].isoformat() if APP_STATE["ultimo_ping"] else None,
            "endpoints": {
                "noticias": "active",
                "chat": "active", 
                "frase_del_dia": "active",
                "apod": "active"
            }
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
        "message": "Bienvenido a la API de AntiHumo News",
        "version": "3.0",
        "database": "Supabase",
        "features": {
            "noticias": "Agregador con IA",
            "chatbot": "AntiBot Assistant con Gemini",
            "apod": "Astronomy Picture of the Day",
            "frase_del_dia": "Frase inspiradora diaria (optimizada)",
            "crawler_auto": "Ejecución automática 4x/día con redundancia",
            "anti_sleep": "Sistema anti-dormancia inteligente"
        },
        "endpoints": {
            "noticias": "/api/noticias",
            "popular_posts": "/api/popular-posts",
            "random_posts": "/api/random-posts",
            "related_posts": "/api/related-posts",
            "chat": "/api/chat (POST)",
            "frase_del_dia": "/api/frase-del-dia",
            "stats": "/api/stats",
            "health": "/api/health",
            "procesar": "/procesar (GET) - Ejecuta el crawler de noticias"
        },
        "system_optimizations": {
            "crawler_schedule": "4 ejecuciones diarias con redundancia",
            "anti_sleep": "Activación inteligente 5 minutos antes de cada ejecución",
            "frase_cache": "Actualización automática a las 00:05 AM",
            "performance": "Respuestas instantáneas en todos los endpoints"
        }
    })

# Manejar cierre graceful del scheduler
import atexit
atexit.register(lambda: scheduler.shutdown() if scheduler else None)

if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask con Supabase en http://localhost:5000")
    print("🤖 AntiBot Assistant integrado y listo")
    print("⏰ Scheduler redundante iniciado - 4 ejecuciones diarias + Frase diaria")
    print("🔋 Sistema Anti-Sleep: INTELIGENTE con cancelación de threads")
    print("📝 Frase del Día: OPTIMIZADA (caché automática a las 00:05 AM)")
    
    print("📊 Endpoints disponibles:")
    print("   - GET  /api/noticias")
    print("   - POST /api/chat 🤖")
    print("   - GET  /api/popular-posts")
    print("   - GET  /api/random-posts") 
    print("   - GET  /api/related-posts")
    print("   - GET  /api/frase-del-dia")
    print("   - POST /api/translate-apod")
    print("   - POST /api/noticias/<id>/click")
    print("   - GET  /api/health")
    print("   - GET  /procesar - Ejecuta el crawler de noticias")
    
    print("\n🕒 SISTEMA REDUNDANTE PROGRAMADO:")
    print("   CRAWLER (4 ejecuciones diarias):")
    print("   - 11:55 AM → Activar Anti-Sleep")
    print("   - 12:00 PM → Ejecutar Crawler + Noticias")
    print("   - 23:55 PM → Activar Anti-Sleep") 
    print("   - 12:00 AM → Ejecutar Crawler + Noticias")
    print("   - 5:55 AM  → Activar Anti-Sleep")
    print("   - 6:00 AM  → Ejecutar Crawler (backup)")
    print("   - 17:55 PM → Activar Anti-Sleep")
    print("   - 18:00 PM → Ejecutar Crawler (backup)")
    
    print("   FRASE DEL DÍA (optimizada):")
    print("   - 00:05 AM → Actualizar Frase del Día (automático)")
    print("   - +10 min  → Desactivar Anti-Sleep después de cada ejecución")
    
    app.run(debug=True)