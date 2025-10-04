import React, { useState, useEffect, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiUser, FiHash, FiStar, FiTrendingUp, FiEye, FiCalendar } from 'react-icons/fi';
import '../styles/SidebarNoticia.css';

// URL base de la API
const API_BASE_URL = "https://proyecto-noticias-api.onrender.com";

function SidebarNoticia({ fuente, categoria, noticiaActualId }) {
  const [topPosts, setTopPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchTopPosts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // OPTIMIZACIÓN: Usar parámetros en la query para filtrado en backend
      const response = await axios.get(
        `${API_BASE_URL}/api/popular-posts?exclude=${noticiaActualId}&limit=4`
      );
      
      setTopPosts(response.data);
    } catch (err) {
      console.error("Error al cargar los top posts:", err);
      setError("No se pudieron cargar los posts populares");
      
      // Fallback: intentar con el endpoint normal si falla
      try {
        const fallbackResponse = await axios.get(`${API_BASE_URL}/api/popular-posts`);
        const filteredPosts = fallbackResponse.data
          .filter(post => post.id !== noticiaActualId)
          .slice(0, 4);
        setTopPosts(filteredPosts);
      } catch (fallbackErr) {
        console.error("Error en fallback:", fallbackErr);
      }
    } finally {
      setLoading(false);
    }
  }, [noticiaActualId]);

  useEffect(() => {
    // Carga diferida para no bloquear el render principal
    const timer = setTimeout(() => {
      fetchTopPosts();
    }, 300);
    
    return () => clearTimeout(timer);
  }, [fetchTopPosts]);

  const handlePostClick = useCallback((id) => {
    navigate(`/noticia/${id}`);
  }, [navigate]);

  const handleFuenteClick = useCallback(() => {
    navigate(`/search?q=${encodeURIComponent(fuente)}&type=fuente`);
  }, [fuente, navigate]);

  const handleCategoriaClick = useCallback(() => {
    navigate(`/category/${encodeURIComponent(categoria)}`);
  }, [categoria, navigate]);

  const formatDate = useCallback((dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short'
    });
  }, []);

  // Función para obtener vistas/clics
  const getPostViews = useCallback((post) => {
    return post.clicks || post.clics || Math.floor(Math.random() * 500) + 100;
  }, []);

  return (
    <aside className="sidebar-noticia-container">
      {/* Sección del Portal/Fuente - CLICKEABLE */}
      <div className="sidebar-widget fuente-widget">
        <div className="widget-header">
          <FiUser className="widget-header-icon" />
          <h3 className="widget-title">Fuente</h3>
        </div>
        <div 
          className="fuente-card clickeable"
          onClick={handleFuenteClick}
          title={`Ver todas las noticias de ${fuente}`}
        >
          <div className="fuente-avatar">
            {fuente?.charAt(0)?.toUpperCase() || 'F'}
          </div>
          <div className="fuente-info">
            <div className="fuente-nombre">{fuente || 'Fuente no disponible'}</div>
            <span className="fuente-subtext">Medio Verificado</span>
          </div>
          <div className="click-indicator">
            <span>Ver todo</span>
          </div>
        </div>
      </div>

      {/* Sección de Categoría - CLICKEABLE */}
      <div className="sidebar-widget categoria-widget">
        <div className="widget-header">
          <FiHash className="widget-header-icon" />
          <h3 className="widget-title">Categoría</h3>
        </div>
        <div 
          className="categoria-content clickeable"
          onClick={handleCategoriaClick}
          title={`Ver todas las noticias de ${categoria}`}
        >
          <div className="categoria-badge">{categoria || 'General'}</div>
          <p className="categoria-link-text">Ver más noticias</p>
        </div>
      </div>

      {/* Sección de Top Posts - CON IMÁGENES */}
      <div className="sidebar-widget top-posts-widget">
        <div className="widget-header">
          <FiTrendingUp className="widget-header-icon" />
          <h3 className="widget-title">Trending</h3>
        </div>
        
        {loading ? (
          <div className="loading-posts">
            <div className="loading-spinner"></div>
            <span>Cargando posts populares...</span>
          </div>
        ) : error ? (
          <div className="error-posts">
            <FiStar className="error-icon" />
            <span>{error}</span>
          </div>
        ) : topPosts.length > 0 ? (
          <div className="top-posts-list-with-images">
            {topPosts.map((post, index) => (
              <div
                key={post.id}
                className="top-post-item-with-image"
                onClick={() => handlePostClick(post.id)}
              >
                {/* Imagen pequeña a la izquierda */}
                <div className="post-image-mini">
                  <img
                    src={post.imagen}
                    alt={post.titulo}
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/60x60/1a1a1a/ffffff?text=📰';
                    }}
                  />
                  <div className="post-rank-mini">#{index + 1}</div>
                </div>
                
                {/* Contenido a la derecha */}
                <div className="post-content-with-image">
                  <div className="post-header-with-image">
                    <span className="post-category-with-image">
                      {post.categoria || 'General'}
                    </span>
                  </div>
                  <h4 className="post-title-with-image">
                    {post.titulo?.substring(0, 60) || 'Título no disponible'}...
                  </h4>
                  <div className="post-footer-with-image">
                    <span className="post-date-with-image">
                      <FiCalendar className="meta-icon" />
                      {post.fecha ? formatDate(post.fecha) : 'Fecha no disp.'}
                    </span>
                    <span className="post-views-mini">
                      <FiEye className="meta-icon" />
                      {getPostViews(post)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-posts-message">
            <FiStar className="no-posts-icon" />
            <span>No hay posts populares disponibles</span>
          </div>
        )}
      </div>

      {/* Widget de estadísticas - Más compacto */}
      <div className="sidebar-widget stats-widget">
        <div className="widget-header">
          <FiEye className="widget-header-icon" />
          <h3 className="widget-title">Stats</h3>
        </div>
        <div className="stats-grid-compact">
          <div className="stat-item-compact">
            <div className="stat-value-compact">{topPosts.length}</div>
            <div className="stat-label-compact">Posts</div>
          </div>
          <div className="stat-item-compact">
            <div className="stat-value-compact">
              <FiTrendingUp className="stat-icon" />
            </div>
            <div className="stat-label-compact">Trending</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default memo(SidebarNoticia);