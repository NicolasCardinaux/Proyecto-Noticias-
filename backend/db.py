import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import random

load_dotenv()



SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 
SUPABASE_KEY_ANON = os.getenv("SUPABASE_KEY_ANON") 

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_KEY_ANON:
    raise ValueError("❌ Faltan SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY o SUPABASE_KEY_ANON en .env")


try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente Supabase (Service Role) configurado")
except Exception as e:
    print(f"❌ Error creando cliente Supabase (Service Role): {e}")
    raise


try:
    supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_KEY_ANON)
    print("✅ Cliente Supabase (Anon Key) configurado")
except Exception as e:
    print(f"❌ Error creando cliente Supabase (Anon Key): {e}")
    supabase_anon = None


def _handle_response(response):
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
    return response.data if hasattr(response, 'data') else response



def get_noticias(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las noticias ordenadas por fecha descendente."""
    try:

        client = supabase_anon if supabase_anon else supabase
        query = client.table("noticias").select("*").order("fecha", desc=True)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Error obteniendo noticias: {e}")
        return []

def get_latest_noticia_by_category(categoria_slug: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la última noticia de una categoría específica (ej: 'negocios').
    Esta es la función nueva para el ChatBot.
    """
    try:
        client = supabase_anon if supabase_anon else supabase
        
        response = client.table("noticias").select(
            "id, titulo, resumen, categoria, fecha, url, fuente"
        ).eq(
            "categoria", categoria_slug
        ).order(
            "fecha", desc=True
        ).limit(1).execute()
        
        return _handle_response(response)[0] if _handle_response(response) else None
            
    except Exception as e:
        print(f"❌ Error en get_latest_noticia_by_category para {categoria_slug}: {e}")
        return None

def get_popular_posts(limit: int = 5, exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene posts populares ordenados por clics."""
    try:
        client = supabase_anon if supabase_anon else supabase
        query = client.table("noticias").select("*").order("clics", desc=True).limit(limit)
        if exclude_id:
            query = query.neq("id", exclude_id)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Error obteniendo posts populares: {e}")
        return []

def get_random_posts(limit: int = 4) -> List[Dict[str, Any]]:
    """Obtiene noticias aleatorias - VERSIÓN OPTIMIZADA."""
    try:
        client = supabase_anon if supabase_anon else supabase
        try:
            response = client.table("noticias").select("*").order("random()").limit(limit).execute()
            return _handle_response(response)
        except:
            sample_size = min(limit * 3, 50)
            response = client.table("noticias").select("*").order("fecha", desc=True).limit(sample_size).execute()
            noticias = _handle_response(response)
            if not noticias:
                return []
            random.shuffle(noticias)
            return noticias[:limit]
    except Exception as e:
        print(f"❌ Error obteniendo posts aleatorios: {e}")
        return []

def get_latest_by_category() -> List[Dict[str, Any]]:
    """Obtiene la última noticia de cada categoría."""
    try:
        noticias = get_noticias()
        latest = {}
        for noticia in noticias:
            categoria = noticia.get("categoria") or "Sin categoría"
            if categoria not in latest and len(latest) < 6:
                latest[categoria] = noticia
        return list(latest.values())
    except Exception as e:
        print(f"❌ Error obteniendo últimas por categoría: {e}")
        return []

def get_related_posts(categoria: str, exclude_id: Optional[int] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Obtiene noticias relacionadas por categoría."""
    try:
        client = supabase_anon if supabase_anon else supabase
        query = client.table("noticias").select("*").eq("categoria", categoria).order("fecha", desc=True).limit(limit)
        if exclude_id:
            query = query.neq("id", exclude_id)
        response = query.execute()
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Error obteniendo posts relacionados: {e}")
        return []

def get_posts_by_source(fuente: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene noticias por fuente."""
    try:
        client = supabase_anon if supabase_anon else supabase
        response = client.table("noticias").select("*").eq("fuente", fuente).order("fecha", desc=True).limit(limit).execute()
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Error obteniendo posts por fuente: {e}")
        return []

def get_categories() -> List[str]:
    """Obtiene todas las categorías disponibles."""
    try:
        client = supabase_anon if supabase_anon else supabase
        response = client.table("noticias").select("categoria").execute()
        categorias = _handle_response(response)
        return list(set([cat["categoria"] for cat in categorias if cat["categoria"]]))
    except Exception as e:
        print(f"❌ Error obteniendo categorías: {e}")
        return []

def get_sources() -> List[str]:
    """Obtiene todas las fuentes disponibles."""
    try:
        client = supabase_anon if supabase_anon else supabase
        response = client.table("noticias").select("fuente").execute()
        fuentes = _handle_response(response)
        return list(set([src["fuente"] for src in fuentes if src["fuente"]]))
    except Exception as e:
        print(f"❌ Error obteniendo fuentes: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Obtiene estadísticas generales."""
    try:
        client = supabase_anon if supabase_anon else supabase
        total_response = client.table("noticias").select("id", count="exact").execute()
        total_noticias = len(total_response.data)
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
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {"total_noticias": 0, "total_clics": 0, "noticias_hoy": 0}

def search_noticias(query: str, tipo: str = "titulo") -> List[Dict[str, Any]]:
    """Busca noticias por término."""
    try:
        client = supabase_anon if supabase_anon else supabase
        if tipo == "fuente":
            response = client.table("noticias").select("*").ilike("fuente", f"%{query}%").order("fecha", desc=True).execute()
        elif tipo == "categoria":
            response = client.table("noticias").select("*").ilike("categoria", f"%{query}%").order("fecha", desc=True).execute()
        else:
            response = client.table("noticias").select("*").ilike("titulo", f"%{query}%").order("fecha", desc=True).execute()
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Error buscando noticias: {e}")
        return []



def insert_noticia(noticia: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una nueva noticia con manejo elegante de duplicados."""
    try:
        response = supabase.table("noticias").insert(noticia).execute()
        return _handle_response(response)
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg or "23505" in error_msg:
            raise Exception("Noticia duplicada") from e
        else:
            raise e

def noticia_existe(titulo: str, url: str) -> bool:
    """Verifica si una noticia ya existe por título o URL."""
    try:
        client = supabase_anon if supabase_anon else supabase
        titulo_hash = generar_hash_titulo(titulo)
        response = client.table("noticias").select("id").or_(f"url.eq.{url},titulo_hash.eq.{titulo_hash}").execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"❌ Error verificando existencia: {e}")
        return False

def obtener_urls_existentes() -> set:
    """Obtiene todas las URLs existentes en la base de datos."""
    try:
        client = supabase_anon if supabase_anon else supabase
        response = client.table("noticias").select("url").execute()
        return {item["url"] for item in response.data}
    except Exception as e:
        print(f"❌ Error obteniendo URLs existentes: {e}")
        return set()

def increment_clics(noticia_id: int) -> bool:
    """Incrementa el contador de clics de una noticia - VERSIÓN ATÓMICA."""
    try:
        try:

            response = supabase.rpc("increment_clics", {"nid": noticia_id}).execute()
            _handle_response(response)
            return True
        except:

            response = supabase_anon.table("noticias").select("clics").eq("id", noticia_id).execute()
            if not response.data:
                return False
            current_clics = response.data[0].get("clics", 0)
            new_clics = current_clics + 1
            update_response = supabase.table("noticias").update({"clics": new_clics}).eq("id", noticia_id).execute()
            return True
    except Exception as e:
        print(f"❌ Error incrementando clics: {e}")
        return False

def delete_old_noticias(max_months: int = 6) -> bool:
    """Elimina noticias más antiguas que X meses."""
    try:
        fecha_limite = (datetime.now() - timedelta(days=30 * max_months)).date().isoformat()
        print(f"🗑️  Buscando noticias anteriores a: {fecha_limite} ({max_months} meses)")
        count_response = supabase.table("noticias").select("id", count="exact").lt("fecha", fecha_limite).execute()
        total_a_eliminar = count_response.count or 0
        if total_a_eliminar == 0:
            print("✅ No hay noticias antiguas para eliminar")
            return True
        stats_antes = get_stats()
        delete_response = supabase.table("noticias").delete().lt("fecha", fecha_limite).execute()
        deleted_count = len(delete_response.data) if delete_response.data else 0
        stats_despues = get_stats()
        print(f"✅ Eliminadas {deleted_count} noticias con más de {max_months} meses")
        print(f"📊 Estadísticas: {stats_antes['total_noticias']} → {stats_despues['total_noticias']} noticias")
        return True
    except Exception as e:
        print(f"❌ Error eliminando noticias antiguas: {e}")
        return False



def get_cached_apod_translation(apod_date: str, user_ip: str) -> Optional[Dict[str, Any]]:
    """Obtiene la traducción del APOD del caché."""
    try:
        client = supabase_anon if supabase_anon else supabase
        response = client.table("apod_translation_cache").select("*").eq("apod_date", apod_date).eq("user_ip", user_ip).execute()
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


def generar_hash_titulo(titulo: str) -> str:
    """Genera un hash único del título para detectar duplicados."""
    return hashlib.md5(titulo.strip().lower().encode('utf-8')).hexdigest()

def inicializar_db():
    """Función de inicialización completa."""
    print("✅ Base de datos Supabase configurada correctamente.")
    stats = get_stats()
    print(f"📊 Estado inicial: {stats['total_noticias']} noticias, {stats['total_clics']} clics totales")



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
            print("  Se eliminarán en la próxima limpieza automática")
        else:
            print(f"\n✅ Todas las noticias tienen menos de 6 meses")
        return conteo
    except Exception as e:
        print(f"❌ Error analizando antigüedad: {e}")
        return None

def get_noticias_proximas_a_expirar(dias_umbral: int = 30):
    """Obtiene noticias que están próximas a cumplir 6 meses."""
    try:
        client = supabase_anon if supabase_anon else supabase
        fecha_umbral = (datetime.now() - timedelta(days=180 - dias_umbral)).date().isoformat()
        fecha_limite = (datetime.now() - timedelta(days=180)).date().isoformat()
        response = client.table("noticias").select("*").lt("fecha", fecha_umbral).gt("fecha", fecha_limite).order("fecha", desc=True).execute()
        noticias_proximas = _handle_response(response)
        if noticias_proximas:
            print(f"\n⚠️  NOTICIAS PRÓXIMAS A EXPIRAR (en los próximos {dias_umbral} días):")
            print("-" * 50)
            for noticia in noticias_proximas:
                dias_restantes = 180 - (datetime.now().date() - datetime.strptime(noticia['fecha'], "%Y-%m-%d").date()).days
                print(f"  📰 {noticia['titulo'][:60]}...")
                print(f"      📅 {noticia['fecha']} - Expira en: {dias_restantes} días")
                print()
        else:
            print(f"✅ No hay noticias próximas a expirar en los próximos {dias_umbral} días")
        return noticias_proximas
    except Exception as e:
        print(f"❌ Error obteniendo noticias próximas a expirar: {e}")
        return []

def monitor_estado_base_datos():
    """Monitoreo completo del estado de la base de datos."""
    print("🔍 MONITOREO COMPLETO DE LA BASE DE DATOS")
    print("=" * 60)
    stats = get_stats()
    print(f"📈 ESTADÍSTICAS GENERALES:")
    print(f"  • Total noticias: {stats['total_noticias']}")
    print(f"  • Total clics: {stats['total_clics']}")
    print(f"  • Noticias hoy: {stats['noticias_hoy']}")
    print("\n📊 DISTRIBUCIÓN POR ANTIGÜEDAD:")
    analizar_antiguedad_noticias()
    print("\n🔔 NOTICIAS PRÓXIMAS A EXPIRAR:")
    get_noticias_proximas_a_expirar(dias_umbral=30)
    ultimas = get_noticias(limit=3)
    if ultimas:
        print("\n🆕 ÚLTIMAS NOTICIAS AGREGADAS:")
        for i, noticia in enumerate(ultimas, 1):
            print(f"  {i}. {noticia['titulo'][:70]}...")
            print(f"      📅 {noticia['fecha']} | 📊 {noticia.get('clics', 0)} clics")
    print("\n" + "=" * 60)
    print("✅ MONITOREO COMPLETADO")

if __name__ == "__main__":
    monitor_estado_base_datos()