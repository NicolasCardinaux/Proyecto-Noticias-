import os
import requests
from supabase import create_client
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random  # ✅ AGREGADO

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Configuración de Rate Limiting
MAX_REQUESTS_PER_DAY = 20  # ✅ 20 preguntas por día por IP

print("🔧 Inicializando ChatBot Service con Rate Limiting...")
print(f"✅ Límite: {MAX_REQUESTS_PER_DAY} preguntas por día por IP")
print(f"✅ GROQ_API_KEY cargada: {bool(GROQ_API_KEY)}")
print(f"✅ Supabase configurado: {bool(SUPABASE_URL)}")

# Contexto base mejorado
CONTEXTO_BASE_WEB = """
Eres AntiBot, el asistente inteligente de AntiHumo News. Tu propósito es ayudar a los usuarios a encontrar información veraz y objetiva.

SOBRE ANTIHUMO NEWS:
• Agregador de noticias argentinas y globales
• Resúmenes con IA que eliminan amarillismo
• Información verificada y sin "humo" informativo
• Secciones: Noticias, Clima, Deportes, Mercados, NASA, Tecnología

INSTRUCCIONES:
• Responde SIEMPRE en español
• Sé breve y directo (2-3 oraciones máximo)
• Mantén tono profesional pero amigable
• Si no sabes algo, admítelo amablemente
• Usa emojis moderadamente (🚀📰🔍)
• Evita inventar información

Responde de forma útil y veraz.
"""

class ChatBotService:
    def __init__(self):
        self.contexto_base = CONTEXTO_BASE_WEB
        self.modelo_actual = "llama3-8b-8192"
        # Cache en memoria para rate limiting
        self.rate_limit_cache = {}
    
    def verificar_rate_limit(self, user_ip: str) -> Dict[str, Any]:
        """Verifica si el usuario ha excedido el límite de 20 preguntas por día."""
        ahora = datetime.now()
        fecha_actual = ahora.date()
        
        if user_ip in self.rate_limit_cache:
            cache_data = self.rate_limit_cache[user_ip]
            
            # Si es el mismo día, verificar contador
            if cache_data['fecha'] == fecha_actual:
                if cache_data['contador'] >= MAX_REQUESTS_PER_DAY:
                    # Calcular tiempo hasta mañana
                    manana = ahora + timedelta(days=1)
                    manana_medianoche = manana.replace(hour=0, minute=0, second=0, microsecond=0)
                    segundos_restantes = (manana_medianoche - ahora).seconds
                    horas_restantes = segundos_restantes // 3600
                    minutos_restantes = (segundos_restantes % 3600) // 60
                    
                    return {
                        "permitido": False,
                        "mensaje": f"⏰ Has alcanzado el límite de {MAX_REQUESTS_PER_DAY} preguntas por día. Podrás hacer más preguntas en {horas_restantes}h {minutos_restantes}m.",
                        "contador_actual": cache_data['contador'],
                        "limite": MAX_REQUESTS_PER_DAY,
                        "reset_time": manana_medianoche.isoformat()
                    }
                else:
                    # Incrementar contador
                    cache_data['contador'] += 1
                    preguntas_restantes = MAX_REQUESTS_PER_DAY - cache_data['contador']
                    return {
                        "permitido": True,
                        "mensaje": f"📊 Usadas: {cache_data['contador']}/{MAX_REQUESTS_PER_DAY} | Restantes: {preguntas_restantes}",
                        "contador_actual": cache_data['contador'],
                        "limite": MAX_REQUESTS_PER_DAY,
                        "preguntas_restantes": preguntas_restantes
                    }
            else:
                # Nuevo día, resetear contador
                self.rate_limit_cache[user_ip] = {
                    'fecha': fecha_actual,
                    'contador': 1
                }
                return {
                    "permitido": True,
                    "mensaje": f"📊 Usadas: 1/{MAX_REQUESTS_PER_DAY} | Restantes: {MAX_REQUESTS_PER_DAY - 1}",
                    "contador_actual": 1,
                    "limite": MAX_REQUESTS_PER_DAY,
                    "preguntas_restantes": MAX_REQUESTS_PER_DAY - 1
                }
        else:
            # Primera pregunta de esta IP
            self.rate_limit_cache[user_ip] = {
                'fecha': fecha_actual,
                'contador': 1
            }
            return {
                "permitido": True,
                "mensaje": f"📊 Usadas: 1/{MAX_REQUESTS_PER_DAY} | Restantes: {MAX_REQUESTS_PER_DAY - 1}",
                "contador_actual": 1,
                "limite": MAX_REQUESTS_PER_DAY,
                "preguntas_restantes": MAX_REQUESTS_PER_DAY - 1
            }
    
    def limpiar_cache_antiguo(self):
        """Limpia entradas de cache más antiguas de 2 días."""
        fecha_actual = datetime.now().date()
        ips_a_eliminar = []
        
        for ip, data in self.rate_limit_cache.items():
            if (fecha_actual - data['fecha']).days > 2:
                ips_a_eliminar.append(ip)
        
        for ip in ips_a_eliminar:
            del self.rate_limit_cache[ip]
            
        if ips_a_eliminar:
            print(f"🧹 Limpiadas {len(ips_a_eliminar)} IPs antiguas del cache")
    
    def obtener_contexto_noticia(self, noticia_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene TODOS los datos de una noticia desde Supabase."""
        try:
            response = supabase.table("noticias").select("*").eq("id", noticia_id).execute()
            
            if not response.data:
                print(f"❌ Noticia {noticia_id} no encontrada en Supabase")
                return None
            
            noticia = response.data[0]
            print(f"✅ Noticia {noticia_id} encontrada: {noticia['titulo'][:50]}...")
            
            return noticia
            
        except Exception as e:
            print(f"❌ Error obteniendo noticia {noticia_id}: {e}")
            return None
    
    def construir_contexto_noticia(self, noticia: Dict[str, Any]) -> str:
        """Construye un contexto rico con todos los datos de la noticia."""
        
        contexto = f"""
📰 CONTEXTO COMPLETO DE LA NOTICIA:

**TITULAR:** {noticia['titulo']}

**RESUMEN COMPLETO:** 
{noticia['resumen']}

**INFORMACIÓN ADICIONAL:**
• 🏷️ Categoría: {noticia.get('categoria', 'No especificada')}
• 📢 Fuente: {noticia.get('fuente', 'No especificada')}
• 📅 Fecha: {noticia.get('fecha', 'No especificada')}
• 🔗 Enlace original: {noticia.get('url', 'No disponible')}
• 👁️ Vistas: {noticia.get('clics', 0)} clics

**INSTRUCCIONES ESPECÍFICAS:**
1. Responde ÚNICAMENTE basado en la información de esta noticia
2. Si la pregunta no puede responderse con esta noticia, di: "No tengo esa información específica en esta noticia. Te sugiero leer la noticia completa en el enlace proporcionado."
3. Sé objetivo y enfócate en los hechos del resumen
4. Destaca los puntos clave de lo que sí está en la noticia
5. Máximo 3 oraciones por respuesta

**IMPORTANTE:** Tu valor está en resumir y aclarar lo que SÍ está en la noticia, no en adivinar lo que no está.
"""
        return contexto
    
    def llamar_groq_api(self, prompt: str) -> str:
        """Llama a la API de Groq para obtener respuestas de IA."""
        try:
            if not GROQ_API_KEY:
                return "🔧 Configuración pendiente: GROQ_API_KEY no configurada."
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.modelo_actual,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres AntiBot, un asistente especializado en noticias veraces y objetivas. Responde siempre en español de forma clara, concisa y útil."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 350,
                "top_p": 0.9,
                "stream": False
            }
            
            print("🔄 Enviando pregunta a Groq API...")
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data["choices"][0]["message"]["content"].strip()
                print("✅ Respuesta recibida de Groq")
                return respuesta
            elif response.status_code == 429:
                return "⏰ Límite de uso excedido temporalmente. Por favor, intenta en unos minutos. 🕒"
            elif response.status_code == 401:
                return "🔑 Error de autenticación con el servicio de IA. ⚠️"
            else:
                print(f"❌ Error Groq API: {response.status_code} - {response.text}")
                return "⚠️ Error temporal con el servicio de IA. Intenta nuevamente. 🔄"
                
        except requests.exceptions.Timeout:
            return "⏰ El servicio está tardando demasiado. Intenta nuevamente. 🕒"
        except requests.exceptions.ConnectionError:
            return "🔌 Error de conexión. Verifica tu internet. 🌐"
        except Exception as e:
            print(f"❌ Error inesperado llamando a Groq: {e}")
            return "❌ Error inesperado. Por favor, intenta más tarde. ⚠️"
    
    def generar_respuesta(self, pregunta: str, noticia_id: Optional[int] = None, user_ip: str = "desconocida") -> Dict[str, Any]:
        """Genera una respuesta contextual basada en la noticia o contexto general."""
        try:
            # ✅ PRIMERO verificar rate limiting
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
            
            # Limpiar cache antiguo periódicamente (10% de probabilidad)
            if random.random() < 0.1:  # ✅ CORREGIDO
                self.limpiar_cache_antiguo()
            
            # Determinar el contexto a usar
            if noticia_id:
                noticia_data = self.obtener_contexto_noticia(noticia_id)
                if noticia_data:
                    contexto = self.construir_contexto_noticia(noticia_data)
                    tipo_contexto = "noticia"
                    noticia_info = "noticia_encontrada"
                    titulo_noticia = noticia_data['titulo']
                else:
                    contexto = self.contexto_base
                    tipo_contexto = "general"
                    noticia_info = "noticia_no_encontrada"
                    titulo_noticia = None
            else:
                contexto = self.contexto_base
                tipo_contexto = "general"
                noticia_info = "sin_noticia"
                titulo_noticia = None
            
            # Construir prompt final optimizado
            prompt_final = f"""{contexto}

**PREGUNTA DEL USUARIO:** {pregunta}

**RESPONDE AHORA** (en español, breve y directo):"""
            
            # Obtener respuesta del modelo
            respuesta = self.llamar_groq_api(prompt_final)
            
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
            print(f"❌ Error generando respuesta: {e}")
            return {
                "respuesta": "❌ Lo siento, ocurrió un error inesperado. Por favor, intenta nuevamente. ⚠️",
                "tipo_contexto": "error",
                "noticia_id": noticia_id,
                "noticia_info": "error",
                "titulo_noticia": None,
                "exito": False,
                "modelo": "error",
                "rate_limit_info": None
            }

# Instancia global del servicio
chatbot_service = ChatBotService()
print("✅ ChatBot Service con Rate Limiting (20/día) inicializado correctamente")