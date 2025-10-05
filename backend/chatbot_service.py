import os
import requests
from supabase import create_client
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import google.generativeai as genai
import time


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_01")
GEMINI_MODEL = "gemini-2.5-flash"


MAX_REQUESTS_PER_DAY = 30

print("🔧 Inicializando ChatBot Service con Gemini...")
print(f"✅ Límite: {MAX_REQUESTS_PER_DAY} preguntas por día por IP")
print(f"✅ GEMINI_API_KEY_01 cargada: {bool(GEMINI_API_KEY)}")
print(f"✅ Supabase configurado: {bool(SUPABASE_URL)}")


try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        print(f"✅ Gemini configurado correctamente - Modelo: {GEMINI_MODEL}")
    else:
        print("❌ GEMINI_API_KEY_01 no encontrada")
        gemini_model = None
except Exception as e:
    print(f"❌ Error configurando Gemini: {e}")
    gemini_model = None


CONTEXTO_BASE_WEB = """
Eres AntiBot, el asistente inteligente de AntiHumo News. Tu propósito es ayudar a los usuarios con información sobre noticias y contenido del sitio.

# 🎯 TU ROL PRINCIPAL:
Eres un **especialista en noticias** que puede:
• Analizar y explicar noticias ESPECÍFICAS de AntiHumo News
• Responder preguntas sobre el contenido de noticias publicadas
• Ayudar a navegar categorías y funcionalidades del sitio
• Contextualizar información basada en noticias reales

# 📰 SOBRE ANTIHUMO NEWS:
• Agregador de noticias argentinas y globales
• Resúmenes con IA que eliminan amarillismo y sesgos
• Información verificada y sin "humo" informativo
• Secciones: Noticias, Clima, Deportes, Mercados, NASA, Tecnología

# 💬 CÓMO RESPONDER:
1. **Cuando hay una noticia específica**: Analiza y responde basado EN EL CONTENIDO de esa noticia
2. **Cuando es sobre el sitio**: Explica funcionalidades y categorías
3. **Cuando es pregunta general sobre noticias**: Responde brevemente si está relacionado con temas noticiosos actuales
4. **Cuando NO puedes responder**: Di amablemente tu límite

# 🚫 LÍMITES CLAROS:
NO PUEDES:
• Crear noticias ficticias o inventar información
• Dar consejos médicos, legales o financieros
• Hacer predicciones futuras no basadas en hechos
• Responder sobre temas completamente ajenos a noticias (como matemáticas puras, ficción, etc.)

# 🌟 EJEMPLOS DE USO CORRECTO:
✅ "¿Qué pasó con Felipe Chávez según esta noticia?" → ANALIZAS la noticia
✅ "¿Qué categorías hay en AntiHumo News?" → EXPLICAS el sitio
✅ "¿Hay noticias sobre tecnología hoy?" → DIRIGES al sitio
❌ "¿Cuánto es 2+2?" → RECHAZAS educadamente

Responde de forma útil, veraz y siempre basado en hechos reales cuando haya noticias de referencia.
"""

class ChatBotService:
    def __init__(self):
        self.contexto_base = CONTEXTO_BASE_WEB
        self.modelo_actual = GEMINI_MODEL
        self.rate_limit_cache = {}
    
    def verificar_rate_limit(self, user_ip: str) -> Dict[str, Any]:
        """Verifica si el usuario ha excedido el límite de 30 preguntas por día."""
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
                        "mensaje": f"⏰ Has alcanzado el límite de {MAX_REQUESTS_PER_DAY} preguntas por día. Podrás hacer más preguntas en {horas_restantes}h {minutos_restantes}m.",
                        "contador_actual": cache_data['contador'],
                        "limite": MAX_REQUESTS_PER_DAY,
                        "reset_time": manana_medianoche.isoformat()
                    }
                else:
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
        """Construye un contexto más efectivo para noticias."""
        
        contexto = f"""
📰 **CONTEXTO DE NOTICIA PARA ANÁLISIS:**

**TITULAR:** {noticia['titulo']}

**RESUMEN COMPLETO:** 
{noticia['resumen']}

**INFORMACIÓN ADICIONAL:**
• Categoría: {noticia.get('categoria', 'No especificada')}
• Fuente: {noticia.get('fuente', 'No especificada')}
• Fecha: {noticia.get('fecha', 'No especificada')}

**INSTRUCCIONES PARA TI:**
Eres un analista de noticias. El usuario te hará preguntas SOBRE ESTA NOTICIA ESPECÍFICA.
• Responde basado ÚNICAMENTE en la información proporcionada arriba
• Si algo no está claro en la noticia, reconócelo amablemente
• Sé objetivo y enfócate en los hechos presentados
• Puedes explicar el contexto y significado de lo que SÍ está en la noticia

**EJEMPLO:**
Si el usuario pregunta "¿Qué pasó con [persona]?" → Explica lo que la noticia dice sobre esa persona
Si pregunta "¿Cuándo ocurrió?" → Usa las fechas de la noticia
Si pregunta "¿Por qué es importante?" → Analiza el impacto basado en el contenido
"""
        return contexto
    
    def llamar_gemini_api(self, prompt: str) -> str:
        """Llama a la API de Gemini para obtener respuestas de IA."""
        try:
            if not GEMINI_API_KEY or not gemini_model:
                print("❌ Gemini no configurado correctamente")
                return self.get_fallback_response(prompt)
            
            print("🔄 Enviando pregunta a Gemini API...")
            
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 350,
            }
            
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response.text:
                respuesta = response.text.strip()
                print("✅ Respuesta recibida de Gemini")
                return respuesta
            else:
                print("❌ Gemini no devolvió texto")
                return self.get_fallback_response(prompt)
                
        except Exception as e:
            print(f"❌ Error llamando a Gemini: {e}")
            return self.get_fallback_response(prompt)
    
    def get_fallback_response(self, prompt: str) -> str:
        """Respuestas de fallback mejoradas."""
        
        fallback_responses = {
            "hola": "¡Hola! 🤖 Soy AntiBot de AntiHumo News. Puedo ayudarte a entender noticias específicas o explicarte sobre nuestro sitio. ¿En qué necesitas ayuda?",
            "holaa": "¡Hola! 👋 Soy AntiBot. Puedo analizar noticias específicas o ayudarte a navegar AntiHumo News. ¿Sobre qué noticia quieres hablar?",
            "qué puedes hacer": "Puedo: 📰 Analizar noticias específicas publicadas, 🔍 Explicar categorías del sitio, 📊 Ayudarte a navegar AntiHumo News. ¿Sobre qué noticia quieres hablar?",
            "noticias": "📰 En AntiHumo News encontrarás noticias actualizadas de Argentina y el mundo, resumidas con IA para eliminar el amarillismo. ¡Explora las diferentes categorías!",
            "clima": "🌤️ En AntiHumo News tenemos una sección de clima con pronósticos actualizados. Puedes consultarla en nuestro sitio para información meteorológica.",
            "deportes": "⚽ Tenemos una sección dedicada a deportes con las últimas noticias. ¡Navega por la categoría Deportes en AntiHumo News para ver lo último!",
            "tecnología": "💻 En nuestra sección de Tecnología encontrarás las últimas novedades en innovación. Visita AntiHumo News para ver el contenido actualizado.",
            "ayuda": "🤖 Puedo ayudarte a entender noticias específicas, explicar categorías del sitio y guiarte en AntiHumo News. ¿Sobre qué noticia necesitas información?"
        }
        
        prompt_lower = prompt.lower()
        
        # PALABRAS que SÍ deben bloquearse (temas completamente fuera de contexto)
        palabras_fuera_contexto = [
            "calcula", "resuelve", "ecuación", "matemática pura", 
            "consejo médico", "consejo legal", "qué droga", "ilegal",
            "futuro predicción", "horóscopo", "magia", "hechizo",
            "fórmula química", "teorema", "álgebra", "trigonometría"
        ]
        
        for palabra in palabras_fuera_contexto:
            if palabra in prompt_lower:
                return "🚫 Lo siento, no puedo ayudarte con ese tipo de consultas. Mi especialidad es noticias y contenido de AntiHumo News."
        
        # Si no es un tema bloqueado, permite la conversación
        for keyword, response in fallback_responses.items():
            if keyword in prompt_lower:
                return response
        
        return "🤖 Soy AntiBot de AntiHumo News. Puedo ayudarte a entender noticias específicas o explicarte sobre nuestro sitio. ¿Tienes alguna noticia en mente?"
    
    def generar_respuesta(self, pregunta: str, noticia_id: Optional[int] = None, user_ip: str = "desconocida") -> Dict[str, Any]:
        """Genera una respuesta contextual basada en la noticia o contexto general."""
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
            
            if random.random() < 0.1:
                self.limpiar_cache_antiguo()
            
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
            
            prompt_final = f"""{contexto}

**PREGUNTA DEL USUARIO:** {pregunta}

**RESPONDE AHORA** (en español, breve y objetivo):"""
            
            respuesta = self.llamar_gemini_api(prompt_final)
            
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


chatbot_service = ChatBotService()
print("✅ ChatBot Service con Gemini 2.5 Flash (30 preguntas/día) inicializado correctamente")