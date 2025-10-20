import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import random
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
SUPABASE_KEY_ANON = os.getenv("SUPABASE_KEY_ANON") 

if not SUPABASE_URL:
    raise ValueError("❌ Faltan SUPABASE_URL en las variables de entorno")

supabase = None
supabase_anon = None

try:
    if SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Cliente Supabase (Service Role) configurado")
    else:
        logger.warning("⚠️ SUPABASE_KEY no encontrada")
except Exception as e:
    logger.error(f"❌ Error creando cliente Supabase (Service Role): {e}")

try:
    if SUPABASE_KEY_ANON:
        supabase_anon = create_client(SUPABASE_URL, SUPABASE_KEY_ANON)
        logger.info("✅ Cliente Supabase (Anon Key) configurado")
    else:
        logger.warning("⚠️ SUPABASE_KEY_ANON no encontrada")
except Exception as e:
    logger.error(f"❌ Error creando cliente Supabase (Anon Key): {e}")


_client = supabase_anon if supabase_anon else supabase

def _get_client(use_service_role: bool = False) -> Optional[Client]:
    """
    Obtiene el cliente de Supabase apropiado.
    
    Args:
        use_service_role: Si es True, usa el cliente con permisos de servicio
                         (para escrituras). Si es False, usa cliente anónimo (lecturas).
    
    Returns:
        Cliente de Supabase o None si no hay clientes disponibles
    """
    if use_service_role:
        return supabase if supabase else _client
    else:
        return supabase_anon if supabase_anon else _client

def _handle_response(response):
    """Maneja las respuestas de Supabase de forma consistente"""
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
    return response.data if hasattr(response, 'data') else response

def _safe_execute_query(operation: str, query_func, *args, **kwargs):
    """Ejecuta una consulta de forma segura con manejo de errores"""
    try:
        return query_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"❌ Error en {operation}: {e}")
        return None

# ==================== FUNCIONES PRINCIPALES MEJORADAS ====================

def get_noticias(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las noticias ordenadas por fecha descendente."""
    client = _get_client(use_service_role=False)
    if not client:
        logger.error("❌ No hay cliente de Supabase disponible")
        return []
    
    try:
        query = client.table("noticias").select("*").order("fecha", desc=True)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        logger.error(f"❌ Error obteniendo noticias: {e}")
        return []

def get_latest_noticia_by_category(categoria_slug: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la última noticia de una categoría específica - VERSIÓN MEJORADA.
    """
    client = _get_client(use_service_role=False)
    if not client:
        logger.error("❌ No hay cliente de Supabase disponible")
        return None
    
    try:

        mapeo_categorias = {
            "negocios": "Negocios",
            "entretenimiento": "Entretenimiento", 
            "salud": "Salud",
            "ciencia": "Ciencia",
            "deportes": "Deportes",
            "tecnologia": "Tecnología",
            "tecnología": "Tecnología",
            "general": "General"
        }
        

        categoria_normalizada = categoria_slug.lower().strip()
        categoria_bd = mapeo_categorias.get(categoria_normalizada, categoria_slug)
        
        logger.info(f"🔍 Buscando última noticia de categoría: '{categoria_slug}' -> '{categoria_bd}'")
        

        response = client.table("noticias").select(
            "id, titulo, resumen, categoria, fecha, url, fuente, imagen, clics"
        ).eq(
            "categoria", categoria_bd
        ).order(
            "fecha", desc=True
        ).limit(1).execute()
        
        resultado = _handle_response(response)
        
        if resultado and len(resultado) > 0:
            noticia = resultado[0]
            logger.info(f"✅ Última noticia encontrada en {categoria_bd}: {noticia['titulo'][:60]}...")
            return noticia
        else:
            logger.warning(f"⚠️ No se encontraron noticias en categoría: {categoria_bd}")
            

            if categoria_bd != "General":
                logger.info(f"🔄 Intentando fallback a categoría General...")
                response_fallback = client.table("noticias").select(
                    "id, titulo, resumen, categoria, fecha, url, fuente, imagen, clics"
                ).eq(
                    "categoria", "General"
                ).order(
                    "fecha", desc=True
                ).limit(1).execute()
                
                resultado_fallback = _handle_response(response_fallback)
                if resultado_fallback and len(resultado_fallback) > 0:
                    noticia_fallback = resultado_fallback[0]
                    logger.info(f"✅ Fallback exitoso: Noticia general encontrada")
                    return noticia_fallback
            
            return None
            
    except Exception as e:
        logger.error(f"❌ Error en get_latest_noticia_by_category para {categoria_slug}: {e}")
        return None

def get_popular_posts(limit: int = 5, exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene posts populares ordenados por clics."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        query = client.table("noticias").select("*").order("clics", desc=True).limit(limit)
        if exclude_id:
            query = query.neq("id", exclude_id)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        logger.error(f"❌ Error obteniendo posts populares: {e}")
        return []

def get_random_posts(limit: int = 4) -> List[Dict[str, Any]]:
    """Obtiene noticias aleatorias - VERSIÓN OPTIMIZADA."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:

        try:
            response = client.table("noticias").select("*").order("random()").limit(limit).execute()
            resultado = _handle_response(response)
            if resultado:
                return resultado
        except Exception:
            logger.info("🔄 Usando método alternativo para posts aleatorios...")
        

        sample_size = min(limit * 3, 50)
        response = client.table("noticias").select("*").order("fecha", desc=True).limit(sample_size).execute()
        noticias = _handle_response(response)
        if not noticias:
            return []
        
        random.shuffle(noticias)
        return noticias[:limit]
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo posts aleatorios: {e}")
        return []

def get_latest_by_category() -> List[Dict[str, Any]]:
    """Obtiene la última noticia de cada categoría."""
    try:
        noticias = get_noticias(limit=50)
        latest = {}
        
        for noticia in noticias:
            categoria = noticia.get("categoria") or "Sin categoría"
            if categoria not in latest:
                latest[categoria] = noticia
                if len(latest) >= 6:  
                    break
        
        return list(latest.values())
    except Exception as e:
        logger.error(f"❌ Error obteniendo últimas por categoría: {e}")
        return []

def get_related_posts(categoria: str, exclude_id: Optional[int] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Obtiene noticias relacionadas por categoría."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        query = client.table("noticias").select("*").eq("categoria", categoria).order("fecha", desc=True).limit(limit)
        if exclude_id:
            query = query.neq("id", exclude_id)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        logger.error(f"❌ Error obteniendo posts relacionados: {e}")
        return []

def get_posts_by_source(fuente: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene noticias por fuente."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        response = client.table("noticias").select("*").eq("fuente", fuente).order("fecha", desc=True).limit(limit).execute()
        return _handle_response(response)
    except Exception as e:
        logger.error(f"❌ Error obteniendo posts por fuente: {e}")
        return []

def get_categories() -> List[str]:
    """Obtiene todas las categorías disponibles."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        response = client.table("noticias").select("categoria").execute()
        categorias = _handle_response(response)

        categorias_unicas = list(set([cat["categoria"] for cat in categorias if cat["categoria"]]))
        return sorted(categorias_unicas)
    except Exception as e:
        logger.error(f"❌ Error obteniendo categorías: {e}")
        return []

def get_sources() -> List[str]:
    """Obtiene todas las fuentes disponibles."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        response = client.table("noticias").select("fuente").execute()
        fuentes = _handle_response(response)

        fuentes_unicas = list(set([src["fuente"] for src in fuentes if src["fuente"]]))
        return sorted(fuentes_unicas)
    except Exception as e:
        logger.error(f"❌ Error obteniendo fuentes: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Obtiene estadísticas generales."""
    client = _get_client(use_service_role=False)
    if not client:
        return {"total_noticias": 0, "total_clics": 0, "noticias_hoy": 0}
    
    try:

        total_response = client.table("noticias").select("id", count="exact").execute()
        total_noticias = total_response.count or 0
        

        clics_response = client.table("noticias").select("clics").execute()
        total_clics = sum(noticia.get("clics", 0) for noticia in clics_response.data)
        

        hoy = datetime.now().date().isoformat()
        hoy_response = client.table("noticias").select("id").eq("fecha", hoy).execute()
        noticias_hoy = len(hoy_response.data)
        
        return {
            "total_noticias": total_noticias,
            "total_clics": total_clics,
            "noticias_hoy": noticias_hoy
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return {"total_noticias": 0, "total_clics": 0, "noticias_hoy": 0}

def search_noticias(query: str, tipo: str = "titulo") -> List[Dict[str, Any]]:
    """Busca noticias por término."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        if tipo == "fuente":
            response = client.table("noticias").select("*").ilike("fuente", f"%{query}%").order("fecha", desc=True).execute()
        elif tipo == "categoria":
            response = client.table("noticias").select("*").ilike("categoria", f"%{query}%").order("fecha", desc=True).execute()
        else:
            response = client.table("noticias").select("*").ilike("titulo", f"%{query}%").order("fecha", desc=True).execute()
        return _handle_response(response)
    except Exception as e:
        logger.error(f"❌ Error buscando noticias: {e}")
        return []

# ==================== FUNCIONES DE ESCRITURA (SERVICE ROLE) ====================

def insert_noticia(noticia: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una nueva noticia con manejo elegante de duplicados."""
    client = _get_client(use_service_role=True)
    if not client:
        raise Exception("❌ No hay cliente de servicio disponible para escritura")
    
    try:
        response = client.table("noticias").insert(noticia).execute()
        logger.info(f"✅ Noticia insertada: {noticia['titulo'][:50]}...")
        return _handle_response(response)
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg or "23505" in error_msg:
            logger.warning(f"⚠️ Noticia duplicada: {noticia['titulo'][:50]}...")
            raise Exception("Noticia duplicada") from e
        else:
            logger.error(f"❌ Error insertando noticia: {e}")
            raise e

def noticia_existe(titulo: str, url: str) -> bool:
    """Verifica si una noticia ya existe por título o URL."""
    client = _get_client(use_service_role=False)
    if not client:
        return False
    
    try:
        titulo_hash = generar_hash_titulo(titulo)
        response = client.table("noticias").select("id").or_(f"url.eq.{url},titulo_hash.eq.{titulo_hash}").execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"❌ Error verificando existencia: {e}")
        return False

def obtener_urls_existentes() -> set:
    """Obtiene todas las URLs existentes en la base de datos."""
    client = _get_client(use_service_role=False)
    if not client:
        return set()
    
    try:
        response = client.table("noticias").select("url").execute()
        return {item["url"] for item in response.data if item["url"]}
    except Exception as e:
        logger.error(f"❌ Error obteniendo URLs existentes: {e}")
        return set()

def increment_clics(noticia_id: int) -> bool:
    """Incrementa el contador de clics de una noticia - VERSIÓN ATÓMICA."""
    client = _get_client(use_service_role=True)
    if not client:
        return False
    
    try:

        try:
            response = client.rpc("increment_clics", {"nid": noticia_id}).execute()
            if response.data:
                logger.info(f"✅ Clic incrementado para noticia {noticia_id} (RPC)")
                return True
        except Exception as rpc_error:
            logger.warning(f"⚠️ RPC no disponible, usando método alternativo: {rpc_error}")
        

        response = client.table("noticias").select("clics").eq("id", noticia_id).execute()
        if not response.data:
            return False
        
        current_clics = response.data[0].get("clics", 0)
        new_clics = current_clics + 1
        
        update_response = client.table("noticias").update({"clics": new_clics}).eq("id", noticia_id).execute()
        logger.info(f"✅ Clic incrementado para noticia {noticia_id}: {current_clics} → {new_clics}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error incrementando clics: {e}")
        return False

def eliminar_noticia_por_id(noticia_id: int) -> bool:
    """Elimina una noticia específica por ID de la base de datos."""
    client = _get_client(use_service_role=True)
    if not client:
        logger.error("❌ No hay cliente de servicio disponible para eliminar")
        return False
    
    try:

        response_info = client.table("noticias").select("titulo").eq("id", noticia_id).execute()
        titulo = response_info.data[0]['titulo'][:50] + "..." if response_info.data else "Desconocido"
        

        response = client.table("noticias").delete().eq("id", noticia_id).execute()
        deleted_count = len(response.data) if response.data else 0
        
        if deleted_count > 0:
            logger.info(f"🗑️  Noticia eliminada: ID {noticia_id} - '{titulo}'")
            return True
        else:
            logger.warning(f"⚠️ No se encontró noticia con ID {noticia_id} para eliminar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error eliminando noticia {noticia_id}: {e}")
        return False

def delete_old_noticias(max_months: int = 6) -> bool:
    """Elimina noticias más antiguas que X meses."""
    client = _get_client(use_service_role=True)
    if not client:
        return False
    
    try:
        fecha_limite = (datetime.now() - timedelta(days=30 * max_months)).date().isoformat()
        logger.info(f"🗑️  Buscando noticias anteriores a: {fecha_limite} ({max_months} meses)")
        

        count_response = client.table("noticias").select("id", count="exact").lt("fecha", fecha_limite).execute()
        total_a_eliminar = count_response.count or 0
        
        if total_a_eliminar == 0:
            logger.info("✅ No hay noticias antiguas para eliminar")
            return True
        
        stats_antes = get_stats()
        

        delete_response = client.table("noticias").delete().lt("fecha", fecha_limite).execute()
        deleted_count = len(delete_response.data) if delete_response.data else 0
        
        stats_despues = get_stats()
        
        logger.info(f"✅ Eliminadas {deleted_count} noticias con más de {max_months} meses")
        logger.info(f"📊 Estadísticas: {stats_antes['total_noticias']} → {stats_despues['total_noticias']} noticias")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error eliminando noticias antiguas: {e}")
        return False

# ==================== FUNCIONES APOD (CACHÉ) ====================

def get_cached_apod_translation(apod_date: str, user_ip: str) -> Optional[Dict[str, Any]]:
    """Obtiene la traducción del APOD del caché."""
    client = _get_client(use_service_role=False)
    if not client:
        return None
    
    try:
        response = client.table("apod_translation_cache").select("*").eq("apod_date", apod_date).eq("user_ip", user_ip).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"❌ Error obteniendo caché APOD: {e}")
        return None

def save_apod_translation(apod_date: str, content_hash: str, translated_title: str, 
                         translated_explanation: str, user_ip: str) -> bool:
    """Guarda la traducción del APOD en el caché."""
    client = _get_client(use_service_role=True)
    if not client:
        return False
    
    try:
        data = {
            "apod_date": apod_date,
            "content_hash": content_hash,
            "translated_title": translated_title,
            "translated_explanation": translated_explanation,
            "user_ip": user_ip,
            "created_at": datetime.now().isoformat()
        }

        response = client.table("apod_translation_cache").insert(data).execute()
        logger.info(f"✅ Traducción APOD guardada en caché para {user_ip}")
        return True
    except Exception as e:
        logger.error(f"❌ Error guardando caché APOD: {e}")
        return False

# ==================== FUNCIONES UTILITARIAS ====================

def generar_hash_titulo(titulo: str) -> str:
    """Genera un hash único del título para detectar duplicados."""
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()

def inicializar_db():
    """Función de inicialización completa."""
    logger.info("✅ Base de datos Supabase configurada correctamente.")
    
    # Verificar conexión
    try:
        stats = get_stats()
        logger.info(f"📊 Estado inicial: {stats['total_noticias']} noticias, {stats['total_clics']} clics totales")
        return True
    except Exception as e:
        logger.error(f"❌ Error verificando estado de la BD: {e}")
        return False

# ==================== FUNCIONES DE MONITOREO Y DIAGNÓSTICO ====================

def analizar_antiguedad_noticias() -> Dict[str, int]:
    """Analiza la distribución de noticias por antigüedad."""
    try:
        from collections import Counter
        
        noticias = get_noticias()
        if not noticias:
            logger.info("📊 No hay noticias para analizar")
            return {}
        
        hoy = datetime.now().date()
        categorias_antiguedad = []
        
        for noticia in noticias:
            try:
                fecha_noticia = datetime.strptime(noticia['fecha'], "%Y-%m-%d").date()
                dias_diferencia = (hoy - fecha_noticia).days
                meses_diferencia = dias_diferencia // 30
                
                if meses_diferencia < 1:
                    categoria = "Menos de 1 mes"
                elif meses_diferencia < 3:
                    categoria = "1-3 meses"
                elif meses_diferencia < 6:
                    categoria = "3-6 meses"
                elif meses_diferencia < 12:
                    categoria = "6-12 meses"
                else:
                    categoria = "Más de 1 año"
                    
                categorias_antiguedad.append(categoria)
            except Exception as e:
                categorias_antiguedad.append("Fecha inválida")
        
        conteo = Counter(categorias_antiguedad)
        
        logger.info("📊 DISTRIBUCIÓN POR ANTIGÜEDAD:")
        logger.info("-" * 40)
        for categoria, cantidad in conteo.most_common():
            porcentaje = (cantidad / len(noticias)) * 100
            logger.info(f"   {categoria}: {cantidad} noticias ({porcentaje:.1f}%)")
        
        total = len(noticias)
        mas_de_6_meses = sum(1 for cat in categorias_antiguedad if cat in ["6-12 meses", "Más de 1 año"])
        
        if mas_de_6_meses > 0:
            logger.info(f"⚠️  {mas_de_6_meses} noticias ({mas_de_6_meses/total*100:.1f}%) tienen más de 6 meses")
        else:
            logger.info(f"✅ Todas las noticias tienen menos de 6 meses")
            
        return dict(conteo)
        
    except Exception as e:
        logger.error(f"❌ Error analizando antigüedad: {e}")
        return {}

def get_noticias_proximas_a_expirar(dias_umbral: int = 30) -> List[Dict[str, Any]]:
    """Obtiene noticias que están próximas a cumplir 6 meses."""
    client = _get_client(use_service_role=False)
    if not client:
        return []
    
    try:
        fecha_umbral = (datetime.now() - timedelta(days=180 - dias_umbral)).date().isoformat()
        fecha_limite = (datetime.now() - timedelta(days=180)).date().isoformat()
        
        response = client.table("noticias").select("*").lt("fecha", fecha_umbral).gt("fecha", fecha_limite).order("fecha", desc=True).execute()
        noticias_proximas = _handle_response(response)
        
        if noticias_proximas:
            logger.info(f"⚠️  {len(noticias_proximas)} noticias próximas a expirar (en {dias_umbral} días)")
        else:
            logger.info(f"✅ No hay noticias próximas a expirar en {dias_umbral} días")
            
        return noticias_proximas
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo noticias próximas a expirar: {e}")
        return []

def monitor_estado_base_datos():
    """Monitoreo completo del estado de la base de datos."""
    logger.info("🔍 MONITOREO COMPLETO DE LA BASE DE DATOS")
    logger.info("=" * 60)
    
    stats = get_stats()
    logger.info(f"📈 ESTADÍSTICAS GENERALES:")
    logger.info(f"  • Total noticias: {stats['total_noticias']}")
    logger.info(f"  • Total clics: {stats['total_clics']}")
    logger.info(f"  • Noticias hoy: {stats['noticias_hoy']}")
    
    logger.info("\n📊 DISTRIBUCIÓN POR ANTIGÜEDAD:")
    analizar_antiguedad_noticias()
    
    logger.info("\n🔔 NOTICIAS PRÓXIMAS A EXPIRAR:")
    get_noticias_proximas_a_expirar(dias_umbral=30)
    
    ultimas = get_noticias(limit=3)
    if ultimas:
        logger.info("\n🆕 ÚLTIMAS NOTICIAS AGREGADAS:")
        for i, noticia in enumerate(ultimas, 1):
            logger.info(f"  {i}. {noticia['titulo'][:70]}...")
            logger.info(f"      📅 {noticia['fecha']} | 📊 {noticia.get('clics', 0)} clics")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ MONITOREO COMPLETADO")



if __name__ == "__main__":

    monitor_estado_base_datos()
else:

    inicializar_db()