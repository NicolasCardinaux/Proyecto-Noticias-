import os
import requests
from supabase import create_client
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import google.generativeai as genai
import time
import logging
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY_ANON = os.getenv("SUPABASE_KEY_ANON")

supabase_anon = None
supabase_service = None

try:
    supabase_anon = create_client(SUPABASE_URL, SUPABASE_KEY_ANON)
    logger.info("✅ Supabase cliente ANÓNIMO inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando Supabase anónimo: {e}")

try:
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_SERVICE_KEY:
        supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase cliente SERVICE ROLE inicializado correctamente")
except Exception as e:
    logger.warning(f"⚠️ No se pudo inicializar Supabase Service Role: {e}")


supabase = supabase_service if supabase_service else supabase_anon

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_01")
GEMINI_MODEL = "gemini-2.5-flash"
MAX_REQUESTS_PER_DAY = 25


CATEGORIAS_NOTICIAS = {
    "Negocios": ["negocio", "negocios", "finanza", "finanzas", "economía", "economia", "empresa", "mercado", "inversión", "inversion", "bursátil", "bursatil"],
    "Entretenimiento": ["entretenimiento", "cine", "película", "pelicula", "música", "musica", "show", "celebridad", "famoso", "espectáculo", "espectaculo"],
    "Salud": ["salud", "medicina", "médico", "medico", "hospital", "enfermedad", "tratamiento", "bienestar"],
    "Ciencia": ["ciencia", "científico", "cientifico", "investigación", "investigacion", "descubrimiento", "estudio", "tecnología", "tecnologia", "innovación", "innovacion"],
    "Deportes": ["deporte", "deportes", "fútbol", "futbol", "partido", "jugador", "equipo", "competición", "competicion", "liga"],
    "Tecnología": ["tecnología", "tecnologia", "tech", "digital", "software", "hardware", "aplicación", "aplicacion", "app", "internet"],
    "General": ["general", "noticia", "actualidad", "última", "ultima", "reciente"]
}


SECCIONES_ESPECIALES = {
    "clima_actual": {
        "nombre": "Clima Actual",
        "descripcion": "Muestra el clima en tu ciudad actual y en otras ciudades importantes del mundo. Datos meteorológicos en tiempo real.",
        "palabras_clave": ["clima", "tiempo", "meteorológico", "meteorologico", "temperatura", "lluvia", "soleado", "pronóstico", "pronostico"]
    },
    "mundo_futbol": {
        "nombre": "Mundo Fútbol", 
        "descripcion": "Resultados recientes, próximos partidos, calendarios de Premier League, Liga Española, Champions League y Serie A.",
        "palabras_clave": ["fútbol", "futbol", "partido", "resultado", "liga", "premier", "champions", "calendario", "equipo"]
    },
    "mundo_inversion": {
        "nombre": "Mundo Inversión",
        "descripcion": "Cotizaciones de divisas, acciones, índices bursátiles y criptomonedas en tiempo real.",
        "palabras_clave": ["inversión", "inversion", "divisa", "acción", "accion", "bolsa", "criptomoneda", "bitcoin", "dólar", "dolar", "euro", "mercado"]
    },
    "ventana_del_universo": {
        "nombre": "Ventana del Universo",
        "descripcion": "Astronomy Picture of the Day (APOD) de la NASA - Imágenes astronómicas diarias con explicaciones.",
        "palabras_clave": ["universo", "nasa", "astronomía", "astronomia", "espacio", "planeta", "estrella", "galaxia", "cosmos"]
    },
    "frase_del_dia": {
        "nombre": "Frase del Día",
        "descripcion": "Frase inspiradora o reflexiva que cambia diariamente para motivar a los usuarios.",
        "palabras_clave": ["frase", "inspiradora", "motivación", "motivacion", "reflexión", "reflexion", "sabiduría", "sabiduria", "pensamiento"]
    }
}

print("🔧 DIAGNÓSTICO GEMINI:")
print(f"✅ GEMINI_API_KEY_01 existe: {bool(GEMINI_API_KEY)}")

gemini_model = None
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        
        print("🔄 Probando conexión con Gemini 2.5 Flash...")
        test_response = gemini_model.generate_content("Responde solo 'CONECTADO'")
        if test_response and test_response.text:
            print(f"✅ Gemini 2.5 Flash configurado correctamente - Test: {test_response.text.strip()}")
        else:
            print("❌ Gemini respondió pero sin texto")
            gemini_model = None
    else:
        print("❌ ERROR CRÍTICO: GEMINI_API_KEY_01 no encontrada en variables de entorno")
        gemini_model = None
except Exception as e:
    print(f"❌ Error configurando Gemini 2.5 Flash: {e}")
    gemini_model = None


CONTEXTO_BASE_WEB = """
Eres AntiBot, el asistente inteligente de AntiHumo News. Tu propósito es ayudar a los usuarios con información veraz sobre noticias y contenido del sitio.

INFORMACIÓN CRÍTICA SOBRE EL SITIO:

1. CATEGORÍAS DE NOTICIAS (contenido noticioso real):
   • Negocios - Noticias financieras, económicas, empresariales
   • Entretenimiento - Cine, música, espectáculos, celebridades
   • Salud - Medicina, bienestar, tratamientos, investigaciones médicas
   • Ciencia - Descubrimientos, investigaciones científicas, avances
   • Deportes - Fútbol, competiciones, partidos, resultados
   • Tecnología - Innovaciones tech, software, hardware, digital
   • General - Noticias variadas y de actualidad

2. SECCIONES ESPECIALES DEL HOME (NO son noticias tradicionales):
   • Clima Actual - Datos meteorológicos en tiempo real
   • Mundo Fútbol - Resultados, calendarios de ligas internacionales
   • Mundo Inversión - Cotizaciones de divisas, acciones, criptomonedas
   • Ventana del Universo - Imágenes astronómicas diarias de la NASA (APOD)
   • Frase del Día - Frase inspiradora diaria

REGLAS ESTRICTAS DE COMPORTAMIENTO:
- SOLO saludas en el PRIMER mensaje de la conversación
- Respuestas directas, útiles y específicas
- NO repetir información innecesariamente
- Reconocer cuando no se tiene información específica
- Para recomendaciones: usar ÚLTIMA noticia disponible de la categoría
- Para secciones especiales: explicar QUÉ son y QUÉ muestran

PALABRAS CLAVE PARA DETECCIÓN:
• "recomienda", "sugiere", "qué noticia" → RECOMENDACIÓN
• "clima", "tiempo" → SECCIÓN CLIMA
• "fútbol", "partido", "liga" → SECCIÓN MUNDO FÚTBOL
• "inversión", "divisa", "bolsa" → SECCIÓN MUNDO INVERSIÓN
• "universo", "nasa", "espacio" → SECCIÓN VENTANA UNIVERSO
• "frase", "inspiración" → SECCIÓN FRASE DEL DÍA
"""

class ChatBotService:
    def __init__(self):
        self.contexto_base = CONTEXTO_BASE_WEB
        self.modelo_actual = GEMINI_MODEL
        self.rate_limit_cache = {}
        self.conversaciones_activas = {} 
        logger.info("🤖 ChatBotService inicializado - Versión Mejorada 1000%")
   
    def verificar_rate_limit(self, user_ip: str) -> Dict[str, Any]:
        """Verifica y actualiza el rate limit por IP"""
        ahora = datetime.now()
        fecha_actual = ahora.date()
        
        if user_ip in self.rate_limit_cache:
            cache_data = self.rate_limit_cache[user_ip]
            
            if cache_data['fecha'] == fecha_actual:
                if cache_data['contador'] >= MAX_REQUESTS_PER_DAY:
                    manana = ahora + timedelta(days=1)
                    manana_medianoche = manana.replace(hour=0, minute=0, second=0, microsecond=0)
                    segundos_restantes = (manana_medianoche - ahora).seconds
                    horas_restantes = segundos_restantes // 3600
                    minutos_restantes = (segundos_restantes % 3600) // 60
                    
                    return {
                        "permitido": False,
                        "mensaje": f"⏰ Límite diario alcanzado ({MAX_REQUESTS_PER_DAY} preguntas). Nuevas preguntas en {horas_restantes}h {minutos_restantes}m.",
                        "contador_actual": cache_data['contador'],
                        "limite": MAX_REQUESTS_PER_DAY,
                        "reset_time": manana_medianoche.isoformat()
                    }
                else:
                    cache_data['contador'] += 1
                    preguntas_restantes = MAX_REQUESTS_PER_DAY - cache_data['contador']
                    return {
                        "permitido": True,
                        "mensaje": f"📊 Preguntas: {cache_data['contador']}/{MAX_REQUESTS_PER_DAY}",
                        "contador_actual": cache_data['contador'],
                        "limite": MAX_REQUESTS_PER_DAY,
                        "preguntas_restantes": preguntas_restantes
                    }
            else:
                self.rate_limit_cache[user_ip] = {
                    'fecha': fecha_actual,
                    'contador': 1
                }
                return {
                    "permitido": True,
                    "mensaje": f"📊 Preguntas: 1/{MAX_REQUESTS_PER_DAY}",
                    "contador_actual": 1,
                    "limite": MAX_REQUESTS_PER_DAY,
                    "preguntas_restantes": MAX_REQUESTS_PER_DAY - 1
                }
        else:
            self.rate_limit_cache[user_ip] = {
                'fecha': fecha_actual,
                'contador': 1
            }
            return {
                "permitido": True,
                "mensaje": f"📊 Preguntas: 1/{MAX_REQUESTS_PER_DAY}",
                "contador_actual": 1,
                "limite": MAX_REQUESTS_PER_DAY,
                "preguntas_restantes": MAX_REQUESTS_PER_DAY - 1
            }
   
    def limpiar_cache_antiguo(self):
        """Limpia caches antiguos para evitar memory leaks"""
        fecha_actual = datetime.now().date()
        

        ips_a_eliminar = []
        for ip, data in self.rate_limit_cache.items():
            if (fecha_actual - data['fecha']).days > 2:
                ips_a_eliminar.append(ip)
        for ip in ips_a_eliminar:
            del self.rate_limit_cache[ip]
        

        conversaciones_a_eliminar = []
        ahora = datetime.now()
        for ip, data in self.conversaciones_activas.items():
            if (ahora - data['ultima_interaccion']).seconds > 3600: 
                conversaciones_a_eliminar.append(ip)
        for ip in conversaciones_a_eliminar:
            del self.conversaciones_activas[ip]
        
        if ips_a_eliminar or conversaciones_a_eliminar:
            logger.info(f"🧹 Limpiadas {len(ips_a_eliminar)} IPs y {len(conversaciones_a_eliminar)} conversaciones antiguas")
   
    def obtener_contexto_noticia(self, noticia_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una noticia específica por ID"""
        try:
            if not supabase:
                logger.error("❌ Supabase no está inicializado")
                return None
            
            response = supabase.table("noticias").select("*").eq("id", noticia_id).execute()
            if not response.data:
                logger.warning(f"❌ Noticia {noticia_id} no encontrada en Supabase")
                return None
            
            noticia = response.data[0]
            logger.info(f"✅ Noticia {noticia_id} encontrada: {noticia['titulo'][:50]}...")
            return noticia
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo noticia {noticia_id}: {e}")
            return None
   
    def construir_contexto_noticia(self, noticia: Dict[str, Any]) -> str:
        """Construye el contexto específico para una noticia"""
        contexto = f"""
📰 CONTEXTO DE NOTICIA PARA ANÁLISIS:

TITULAR: {noticia['titulo']}

RESUMEN COMPLETO:
{noticia['resumen']}

INFORMACIÓN ADICIONAL:
• Categoría: {noticia.get('categoria', 'No especificada')}
• Fuente: {noticia.get('fuente', 'No especificada')}
• Fecha: {noticia.get('fecha', 'No especificada')}

INSTRUCCIONES PARA TI:
Eres un analista de noticias. El usuario te hará preguntas SOBRE ESTA NOTICIA ESPECÍFICA.
• Responde basado ÚNICAMENTE en la información proporcionada arriba
• Si algo no está claro en la noticia, reconócelo amablemente
• Sé objetivo y enfócate en los hechos presentados
"""
        return contexto
    
    def inicializar_chat_gemini(self, user_ip: str, contexto_sistema: str):
        """Inicializa o reinicia un chat de Gemini para un usuario"""
        try:
            if not gemini_model:
                return None
            

            chat_session = gemini_model.start_chat(history=[])
            
            chat_session.send_message(f"""
{contexto_sistema}

INSTRUCCIÓN INICIAL: 
Eres AntiBot de AntiHumo News. Mantén conversaciones naturales y útiles. 
SOLO saluda en el primer mensaje de cada sesión.
Responde de forma directa y enfocada en ayudar.
""")
            
            self.conversaciones_activas[user_ip] = {
                'chat': chat_session,
                'ultima_interaccion': datetime.now(),
                'primer_mensaje': True,
                'contexto_actual': None  
            }
            
            logger.info(f"✅ Chat Gemini inicializado para IP: {user_ip}")
            return chat_session
            
        except Exception as e:
            logger.error(f"❌ Error inicializando chat Gemini: {e}")
            return None
    
    def obtener_chat_gemini(self, user_ip: str, contexto_sistema: str) -> Any:
        """Obtiene el chat activo de Gemini o crea uno nuevo"""
        ahora = datetime.now()
        
        if user_ip in self.conversaciones_activas:
            datos_chat = self.conversaciones_activas[user_ip]
            

            if (ahora - datos_chat['ultima_interaccion']).seconds > 1800:
                logger.info(f"🔄 Reiniciando chat por inactividad para IP: {user_ip}")
                return self.inicializar_chat_gemini(user_ip, contexto_sistema)
            
            datos_chat['ultima_interaccion'] = ahora
            datos_chat['primer_mensaje'] = False
            return datos_chat['chat']
        else:

            return self.inicializar_chat_gemini(user_ip, contexto_sistema)
    
    def es_primer_mensaje(self, user_ip: str) -> bool:
        """Determina si es el primer mensaje del usuario en esta sesión"""
        if user_ip not in self.conversaciones_activas:
            return True
        
        es_primer = self.conversaciones_activas[user_ip]['primer_mensaje']
        self.conversaciones_activas[user_ip]['primer_mensaje'] = False
        return es_primer
    
    def construir_prompt_inteligente(self, pregunta: str, contexto: str, es_primer_mensaje: bool, 
                                   tipo_contexto: str, noticia_data: Optional[Dict] = None) -> str:
        """Construye un prompt inteligente basado en el contexto y tipo de consulta"""
        
        saludo = "¡Hola! Soy AntiBot de AntiHumo News. " if es_primer_mensaje else ""
        
        if tipo_contexto == "recomendacion":
            if noticia_data:
                prompt_especifico = f"""
{saludo}El usuario está pidiendo una recomendación de noticia. 

NOTICIA RECOMENDADA DISPONIBLE:
• Título: {noticia_data['titulo']}
• Resumen: {noticia_data['resumen']}
• Categoría: {noticia_data.get('categoria', 'General')}

RESPONDE:
- Recomienda esta noticia específica mencionando el titular
- Explica brevemente por qué es relevante
- Usa un tono natural y útil
- NO digas "te recomiendo esta noticia" de forma genérica
- Integra la recomendación en tu respuesta naturalmente
"""
            else:
                prompt_especifico = f"""
{saludo}El usuario quiere una recomendación pero no hay noticias recientes en esa categoría.

RESPONDE:
- Informa amablemente que no hay noticias recientes en esa categoría
- Sugiere explorar otras categorías como General o Deportes
- Mantén un tono útil y proactivo
"""
        
        elif tipo_contexto == "seccion_especial":
            seccion_info = noticia_data
            prompt_especifico = f"""
{saludo}El usuario está preguntando sobre la sección: {seccion_info['nombre']}

INFORMACIÓN DE LA SECCIÓN:
• Descripción: {seccion_info['descripcion']}

RESPONDE:
- Explica claramente qué es esta sección y qué muestra
- Enfatiza que NO es una noticia tradicional
- Describe el tipo de contenido que el usuario encontrará allí
- Usa un tono informativo y útil
"""
        
        elif tipo_contexto == "noticia_especifica":
            prompt_especifico = f"""
{saludo}El usuario está preguntando sobre una noticia específica.

CONTEXTO DE LA NOTICIA:
• Título: {noticia_data['titulo']}
• Resumen: {noticia_data['resumen']}

RESPONDE:
- Basa tu respuesta ÚNICAMENTE en la información de esta noticia
- Sé preciso y objetivo con los hechos presentados
- Si la pregunta no puede responderse con la información disponible, reconócelo amablemente
"""
        
        else:  
            prompt_especifico = f"""
{saludo}El usuario está haciendo una pregunta general.

RESPONDE:
- De forma directa y útil
- Enfócate en ayudar con información real del sitio
- Si no tienes información específica, sugiere explorar las categorías
- Mantén un tono profesional pero amigable
"""

        return f"""{prompt_especifico}

PREGUNTA DEL USUARIO: {pregunta}

RESPONDE de forma natural y directa:"""
    
    def clasificar_intencion(self, pregunta: str) -> Dict[str, Any]:
        """Clasificación MUCHO más precisa de la intención del usuario"""
        pregunta_lower = pregunta.lower().strip()
        

        palabras_recomendacion = ["recomienda", "sugiere", "qué noticia", "noticia de", "última noticia", "noticia nueva", "recomiendas"]
        if any(palabra in pregunta_lower for palabra in palabras_recomendacion):
            for categoria, palabras_clave in CATEGORIAS_NOTICIAS.items():
                if any(clave in pregunta_lower for clave in palabras_clave):
                    return {"tipo": "recomendacion_categoria", "categoria": categoria}
        

        for seccion_id, seccion_info in SECCIONES_ESPECIALES.items():
            if any(clave in pregunta_lower for clave in seccion_info["palabras_clave"]):
                return {"tipo": "seccion_especial", "seccion": seccion_id, "info": seccion_info}
        

        if "noticia" in pregunta_lower and any(word in pregunta_lower for word in ["qué", "cómo", "cuándo", "dónde", "por qué"]):
            return {"tipo": "consulta_especifica", "categoria": None}
        
        return {"tipo": "general", "categoria": None}
    
    def llamar_gemini_con_chat(self, prompt: str, user_ip: str, contexto_sistema: str) -> str:
        """Llama a Gemini usando chat con historial"""
        try:
            if not gemini_model:
                logger.error("❌ Gemini no está configurado correctamente")
                return self.get_fallback_response("")
            

            chat_session = self.obtener_chat_gemini(user_ip, contexto_sistema)
            if not chat_session:
                return self.get_fallback_response(prompt)
            
            logger.info("🔄 Enviando mensaje a Gemini Chat API...")
            

            response = chat_session.send_message(prompt)
            
            if response and response.text:
                respuesta = response.text.strip()
                logger.info("✅ Respuesta recibida de Gemini Chat")
                

                if "noticia" in prompt.lower() or "recomienda" in prompt.lower():
                    self.conversaciones_activas[user_ip]['contexto_actual'] = "discutiendo_noticia"
                
                return respuesta
            else:
                logger.warning("❌ Gemini no devolvió texto en la respuesta")
                return self.get_fallback_response(prompt)
               
        except Exception as e:
            logger.error(f"❌ Error llamando a Gemini Chat: {e}")
            return self.get_fallback_response(prompt)
    
    def get_fallback_response(self, prompt: str) -> str:
        """Respuestas de fallback mejoradas"""
        prompt_lower = prompt.lower()
        

        if any(palabra in prompt_lower for palabra in ["recomienda", "sugiere", "noticia de"]):
            return "📰 Actualmente no tengo noticias recientes en esa categoría específica. Te sugiero explorar las secciones de 'General' o 'Deportes' donde suele haber contenido actualizado."
        
        if any(palabra in prompt_lower for palabra in ["clima", "tiempo"]):
            return "🌤️ En la sección 'Clima Actual' puedes ver el tiempo en tu ciudad y otras ciudades del mundo. Son datos meteorológicos en tiempo real, no noticias tradicionales."
        
        if any(palabra in prompt_lower for palabra in ["fútbol", "futbol", "partido", "liga"]):
            return "⚽ La sección 'Mundo Fútbol' muestra resultados recientes, próximos partidos y calendarios de ligas como Premier League, Champions League y más."
        
        if any(palabra in prompt_lower for palabra in ["inversión", "inversion", "bolsa", "divisa"]):
            return "📈 En 'Mundo Inversión' encontrarás cotizaciones de divisas, acciones y criptomonedas en tiempo real. Es información financiera actualizada."
        
        if any(palabra in prompt_lower for palabra in ["universo", "nasa", "espacio"]):
            return "🪐 La 'Ventana del Universo' muestra la Astronomy Picture of the Day de la NASA - imágenes astronómicas espectaculares con explicaciones."
        
        return "🤖 Puedo ayudarte a encontrar noticias por categoría o explicarte las secciones especiales del sitio. ¿Qué te interesa explorar?"
    
    def generar_respuesta(self, pregunta: str, noticia_id: Optional[int] = None, user_ip: str = "desconocida") -> Dict[str, Any]:
        try:

            rate_limit_check = self.verificar_rate_limit(user_ip)
            
            if not rate_limit_check["permitido"]:
                return {
                    "respuesta": rate_limit_check["mensaje"],
                    "tipo_contexto": "rate_limit",
                    "noticia_id": noticia_id,
                    "noticia_info": "limite_excedido",
                    "titulo_noticia": None,
                    "exito": False,
                    "modelo": "rate_limit",
                    "rate_limit_info": rate_limit_check
                }


            es_primer_mensaje = self.es_primer_mensaje(user_ip)
            

            intencion = self.clasificar_intencion(pregunta)
            
            contexto = self.contexto_base
            tipo_contexto = intencion["tipo"]
            noticia_info = "sin_noticia"
            titulo_noticia = None
            noticia_data = None
            

            if noticia_id:
                noticia_data = self.obtener_contexto_noticia(noticia_id)
                if noticia_data:
                    contexto = self.construir_contexto_noticia(noticia_data)
                    tipo_contexto = "noticia_especifica"
                    noticia_info = "noticia_encontrada"
                    titulo_noticia = noticia_data['titulo']
                else:
                    noticia_info = "noticia_no_encontrada"
            
            elif intencion["tipo"] == "recomendacion_categoria":
                categoria = intencion["categoria"]
                

                noticia_data = db.get_latest_noticia_by_category(categoria)
                
                if noticia_data:
                    titulo_noticia = noticia_data['titulo']
                    noticia_info = "recomendacion_encontrada"
                    tipo_contexto = "recomendacion"
                else:
                    noticia_info = "recomendacion_no_encontrada"
                    tipo_contexto = "recomendacion"
                    noticia_data = {"categoria": categoria}
            
            elif intencion["tipo"] == "seccion_especial":
                seccion_info = intencion["info"]
                noticia_data = seccion_info
                noticia_info = "seccion_especial"
                tipo_contexto = "seccion_especial"
                titulo_noticia = seccion_info["nombre"]
            

            prompt_final = self.construir_prompt_inteligente(
                pregunta, contexto, es_primer_mensaje, tipo_contexto, noticia_data
            )
            

            respuesta = self.llamar_gemini_con_chat(prompt_final, user_ip, contexto)
            
            logger.info(f"✅ Respuesta generada - Tipo: {tipo_contexto}, Longitud: {len(respuesta)}")
            
            return {
                "respuesta": respuesta,
                "tipo_contexto": tipo_contexto,
                "noticia_id": noticia_id,
                "noticia_info": noticia_info,
                "titulo_noticia": titulo_noticia,
                "exito": True,
                "modelo": self.modelo_actual,
                "rate_limit_info": rate_limit_check
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return {
                "respuesta": "⚠️ Ocurrió un error inesperado. Por favor, intenta nuevamente.",
                "tipo_contexto": "error",
                "noticia_id": noticia_id,
                "noticia_info": "error",
                "titulo_noticia": None,
                "exito": False,
                "modelo": "error",
                "rate_limit_info": None
            }


chatbot_service = ChatBotService()

try:
    test_result = chatbot_service.generar_respuesta("test de conexión", None, "test_init")
    if test_result["exito"]:
        print(f"✅ Test inicial exitoso: {test_result['respuesta'][:80]}...")
    else:
        print(f"⚠️ Test inicial con problemas: {test_result['respuesta']}")
except Exception as e:
    print(f"❌ Error en test inicial: {e}")