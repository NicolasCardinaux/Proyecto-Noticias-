# db.py - Conexión a Supabase con eliminación automática a los 6 meses
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import random

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en .env")

# Cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def _handle_response(response):
    """Maneja respuestas de Supabase y lanza excepciones si hay errores."""
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
    return response.data if hasattr(response, 'data') else response

# --- Funciones para noticias ---
def get_noticias(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las noticias ordenadas por fecha descendente."""
    query = supabase.table("noticias").select("*").order("fecha", desc=True)
    if limit:
        query = query.limit(limit)
    response = query.execute()
    return _handle_response(response)

def get_popular_posts(limit: int = 5, exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene posts populares ordenados por clics."""
    query = supabase.table("noticias").select("*").order("clics", desc=True).limit(limit)
    if exclude_id:
        query = query.neq("id", exclude_id)
    response = query.execute()
    return _handle_response(response)

def get_random_posts(limit: int = 4) -> List[Dict[str, Any]]:
    """Obtiene noticias aleatorias - VERSIÓN CORREGIDA."""
    try:
        # Estrategia eficiente: obtener un sample y mezclar en Python
        sample_size = min(limit * 3, 50)  # Obtener 3x el límite, máximo 50
        
        response = supabase.table("noticias").select("*").order("fecha", desc=True).limit(sample_size).execute()
        noticias = _handle_response(response)
        
        if not noticias:
            return []
            
        # Mezclar aleatoriamente
        random.shuffle(noticias)
        
        return noticias[:limit]
        
    except Exception as e:
        print(f"❌ Error obteniendo posts aleatorios: {e}")
        # Fallback seguro
        try:
            all_noticias = get_noticias(limit=20)
            random.shuffle(all_noticias)
            return all_noticias[:limit]
        except:
            return []

def get_latest_by_category() -> List[Dict[str, Any]]:
    """Obtiene la última noticia de cada categoría."""
    noticias = get_noticias()
    latest = {}
    for noticia in noticias:
        categoria = noticia.get("categoria") or "Sin categoría"
        if categoria not in latest and len(latest) < 6:
            latest[categoria] = noticia
    return list(latest.values())

def get_related_posts(categoria: str, exclude_id: Optional[int] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Obtiene noticias relacionadas por categoría."""
    query = supabase.table("noticias").select("*").eq("categoria", categoria).order("fecha", desc=True).limit(limit)
    if exclude_id:
        query = query.neq("id", exclude_id)
    response = query.execute()
    return _handle_response(response)

def get_posts_by_source(fuente: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene noticias por fuente."""
    response = supabase.table("noticias").select("*").eq("fuente", fuente).order("fecha", desc=True).limit(limit).execute()
    return _handle_response(response)

def get_categories() -> List[str]:
    """Obtiene todas las categorías disponibles."""
    response = supabase.table("noticias").select("categoria").execute()
    categorias = _handle_response(response)
    return list(set([cat["categoria"] for cat in categorias if cat["categoria"]]))

def get_sources() -> List[str]:
    """Obtiene todas las fuentes disponibles."""
    response = supabase.table("noticias").select("fuente").execute()
    fuentes = _handle_response(response)
    return list(set([src["fuente"] for src in fuentes if src["fuente"]]))

def get_stats() -> Dict[str, Any]:
    """Obtiene estadísticas generales."""
    # Total de noticias
    total_response = supabase.table("noticias").select("id", count="exact").execute()
    total_noticias = len(total_response.data)
    
    # Total de clics
    clics_response = supabase.table("noticias").select("clics").execute()
    total_clics = sum(noticia["clics"] or 0 for noticia in clics_response.data)
    
    # Noticias de hoy
    hoy = datetime.now().date().isoformat()
    hoy_response = supabase.table("noticias").select("id").eq("fecha", hoy).execute()
    noticias_hoy = len(hoy_response.data)
    
    return {
        "total_noticias": total_noticias,
        "total_clics": total_clics,
        "noticias_hoy": noticias_hoy
    }

def search_noticias(query: str, tipo: str = "titulo") -> List[Dict[str, Any]]:
    """Busca noticias por término."""
    if tipo == "fuente":
        response = supabase.table("noticias").select("*").ilike("fuente", f"%{query}%").order("fecha", desc=True).execute()
    elif tipo == "categoria":
        response = supabase.table("noticias").select("*").ilike("categoria", f"%{query}%").order("fecha", desc=True).execute()
    else:  # título por defecto
        response = supabase.table("noticias").select("*").ilike("titulo", f"%{query}%").order("fecha", desc=True).execute()
    return _handle_response(response)

# --- Operaciones de escritura ---
def insert_noticia(noticia: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una nueva noticia con manejo elegante de duplicados."""
    try:
        response = supabase.table("noticias").insert(noticia).execute()
        return _handle_response(response)
    except Exception as e:
        # Manejar específicamente el error de duplicado
        error_msg = str(e)
        if "duplicate key" in error_msg or "23505" in error_msg:
            raise Exception("Noticia duplicada") from e
        else:
            raise e

def noticia_existe(titulo: str, url: str) -> bool:
    """Verifica si una noticia ya existe por título o URL."""
    titulo_hash = generar_hash_titulo(titulo)
    response = supabase.table("noticias").select("id").or_(f"url.eq.{url},titulo_hash.eq.{titulo_hash}").execute()
    return len(response.data) > 0

def obtener_urls_existentes() -> set:
    """Obtiene todas las URLs existentes en la base de datos."""
    response = supabase.table("noticias").select("url").execute()
    return {item["url"] for item in response.data}

def increment_clics(noticia_id: int) -> bool:
    """Incrementa el contador de clics de una noticia."""
    try:
        # Usar la función RPC que creamos en Supabase
        response = supabase.rpc("increment_clics", {"nid": noticia_id}).execute()
        _handle_response(response)
        return True
    except Exception as e:
        print(f"❌ Error incrementando clics: {e}")
        # Fallback: actualización directa
        try:
            noticia = supabase.table("noticias").select("clics").eq("id", noticia_id).single().execute()
            current_clics = noticia.data.get("clics", 0) if noticia.data else 0
            response = supabase.table("noticias").update({"clics": current_clics + 1}).eq("id", noticia_id).execute()
            return True
        except Exception as e2:
            print(f"❌ Error en fallback de clics: {e2}")
            return False

def delete_old_noticias(max_months: int = 6) -> bool:
    """Elimina noticias más antiguas que X meses (por defecto 6 meses)."""
    try:
        # Calcular la fecha límite (hoy - X meses)
        fecha_limite = (datetime.now() - timedelta(days=30 * max_months)).strftime("%Y-%m-%d")
        
        print(f"🗑️  Buscando noticias anteriores a: {fecha_limite} ({max_months} meses)")
        
        # Primero, contar cuántas noticias se van a eliminar
        count_response = supabase.table("noticias").select("id", count="exact").lt("fecha", fecha_limite).execute()
        total_a_eliminar = count_response.count or 0
        
        if total_a_eliminar == 0:
            print("✅ No hay noticias antiguas para eliminar")
            return True
        
        # Obtener estadísticas antes de eliminar
        stats_antes = get_stats()
        
        # Eliminar noticias más antiguas que la fecha límite
        delete_response = supabase.table("noticias").delete().lt("fecha", fecha_limite).execute()
        
        deleted_count = len(delete_response.data) if delete_response.data else 0
        
        # Obtener estadísticas después
        stats_despues = get_stats()
        
        print(f"✅ Eliminadas {deleted_count} noticias con más de {max_months} meses")
        print(f"📊 Estadísticas: {stats_antes['total_noticias']} → {stats_despues['total_noticias']} noticias")
        
        return True
        
    except Exception as e:
        print(f"❌ Error eliminando noticias antiguas: {e}")
        return False

def analizar_antiguedad_noticias():
    """Analiza la distribución de noticias por antigüedad."""
    try:
        from collections import Counter
        
        noticias = get_noticias()
        if not noticias:
            print("📊 No hay noticias para analizar")
            return
        
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
        
        # Contar por categoría
        conteo = Counter(categorias_antiguedad)
        
        print("📊 DISTRIBUCIÓN POR ANTIGÜEDAD:")
        print("-" * 40)
        for categoria, cantidad in conteo.most_common():
            porcentaje = (cantidad / len(noticias)) * 100
            print(f"   {categoria}: {cantidad} noticias ({porcentaje:.1f}%)")
            
        total = len(noticias)
        mas_de_6_meses = sum(1 for cat in categorias_antiguedad if cat in ["6-12 meses", "Más de 1 año"])
        
        if mas_de_6_meses > 0:
            print(f"\n⚠️  {mas_de_6_meses} noticias ({mas_de_6_meses/total*100:.1f}%) tienen más de 6 meses")
            print("   Se eliminarán en la próxima limpieza automática")
        else:
            print(f"\n✅ Todas las noticias tienen menos de 6 meses")
            
        return conteo
            
    except Exception as e:
        print(f"❌ Error analizando antigüedad: {e}")
        return None

def cleanup_noticias_automatico():
    """Función de limpieza automática que se puede llamar desde el cron job."""
    print("🔧 INICIANDO LIMPIEZA AUTOMÁTICA DE NOTICIAS")
    print("=" * 50)
    
    # Primero analizar el estado actual
    analizar_antiguedad_noticias()
    
    print("\n" + "=" * 50)
    
    # Luego ejecutar la limpieza
    resultado = delete_old_noticias(max_months=6)
    
    print("\n" + "=" * 50)
    
    # Mostrar estado final
    if resultado:
        print("🎯 LIMPIEZA COMPLETADA")
        stats_final = get_stats()
        print(f"📈 Estado final: {stats_final['total_noticias']} noticias en la base de datos")
    else:
        print("❌ LIMPIEZA FALLÓ")
    
    return resultado

# --- Funciones para caché APOD ---
def get_cached_apod_translation(apod_date: str, user_ip: str) -> Optional[Dict[str, Any]]:
    """Obtiene la traducción del APOD del caché."""
    try:
        response = supabase.table("apod_translation_cache").select("*").eq("apod_date", apod_date).eq("user_ip", user_ip).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Error obteniendo caché APOD: {e}")
        return None

def save_apod_translation(apod_date: str, content_hash: str, translated_title: str, translated_explanation: str, user_ip: str) -> bool:
    """Guarda la traducción del APOD en el caché."""
    try:
        data = {
            "apod_date": apod_date,
            "content_hash": content_hash,
            "translated_title": translated_title,
            "translated_explanation": translated_explanation,
            "user_ip": user_ip
        }
        response = supabase.table("apod_translation_cache").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ Error guardando caché APOD: {e}")
        return False

# --- Utilidades ---
def generar_hash_titulo(titulo: str) -> str:
    """Genera un hash único del título para detectar duplicados."""
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()

def inicializar_db():
    """Función de inicialización (para compatibilidad con código existente)."""
    print("✅ Base de datos Supabase configurada correctamente.")
    
    # Mostrar estado inicial
    stats = get_stats()
    print(f"📊 Estado inicial: {stats['total_noticias']} noticias, {stats['total_clics']} clics totales")
    
    # Analizar antigüedad
    analizar_antiguedad_noticias()

# Función para ver noticias próximas a expirar
def get_noticias_proximas_a_expirar(dias_umbral: int = 30):
    """Obtiene noticias que están próximas a cumplir 6 meses."""
    try:
        fecha_umbral = (datetime.now() - timedelta(days=180 - dias_umbral)).strftime("%Y-%m-%d")
        fecha_limite = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        response = supabase.table("noticias").select("*").lt("fecha", fecha_umbral).gt("fecha", fecha_limite).order("fecha", desc=True).execute()
        
        noticias_proximas = _handle_response(response)
        
        if noticias_proximas:
            print(f"\n⚠️  NOTICIAS PRÓXIMAS A EXPIRAR (en los próximos {dias_umbral} días):")
            print("-" * 50)
            for noticia in noticias_proximas:
                dias_restantes = 180 - (datetime.now().date() - datetime.strptime(noticia['fecha'], "%Y-%m-%d").date()).days
                print(f"   📰 {noticia['titulo'][:60]}...")
                print(f"      Fecha: {noticia['fecha']} - Expira en: {dias_restantes} días")
                print()
        else:
            print(f"✅ No hay noticias próximas a expirar en los próximos {dias_umbral} días")
            
        return noticias_proximas
        
    except Exception as e:
        print(f"❌ Error obteniendo noticias próximas a expirar: {e}")
        return []

# Función para monitoreo continuo
def monitor_estado_base_datos():
    """Monitoreo completo del estado de la base de datos."""
    print("🔍 MONITOREO COMPLETO DE LA BASE DE DATOS")
    print("=" * 60)
    
    # Estadísticas generales
    stats = get_stats()
    print(f"📈 ESTADÍSTICAS GENERALES:")
    print(f"   • Total noticias: {stats['total_noticias']}")
    print(f"   • Total clics: {stats['total_clics']}")
    print(f"   • Noticias hoy: {stats['noticias_hoy']}")
    
    print("\n📊 DISTRIBUCIÓN POR ANTIGÜEDAD:")
    analizar_antiguedad_noticias()
    
    print("\n🔔 NOTICIAS PRÓXIMAS A EXPIRAR:")
    get_noticias_proximas_a_expirar(dias_umbral=30)
    
    # Últimas noticias agregadas
    ultimas = get_noticias(limit=3)
    if ultimas:
        print("\n🆕 ÚLTIMAS NOTICIAS AGREGADAS:")
        for i, noticia in enumerate(ultimas, 1):
            print(f"   {i}. {noticia['titulo'][:70]}...")
            print(f"      📅 {noticia['fecha']} | 📊 {noticia.get('clics', 0)} clics")
    
    print("\n" + "=" * 60)
    print("✅ MONITOREO COMPLETADO")

if __name__ == "__main__":
    # Si ejecutan el archivo directamente, mostrar el estado
    monitor_estado_base_datos()