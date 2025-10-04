import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import '../styles/NoticiasRelacionadas.css';

// URL base de la API
const API_BASE_URL = import.meta.env.VITE_API_URL;

function NoticiasRelacionadas({ categoriaActual, noticiaActualId }) {
  const [noticiasRelacionadas, setNoticiasRelacionadas] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchNoticiasRelacionadas = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/noticias`);
        const todasNoticias = response.data;
        
        // Filtrar noticias de la misma categoría, excluyendo la actual
        const relacionadas = todasNoticias.filter(noticia => 
          noticia.categoria && 
          noticia.categoria.toLowerCase() === categoriaActual.toLowerCase() &&
          noticia.id !== noticiaActualId
        );
        
        setNoticiasRelacionadas(relacionadas);
      } catch (err) {
        console.error('Error fetching related news:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNoticiasRelacionadas();
  }, [categoriaActual, noticiaActualId]);

  const handleNoticiaClick = (noticia) => {
    navigate(`/noticia/${noticia.id}`);
  };

  const scrollLeft = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: -400, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: 400, behavior: 'smooth' });
    }
  };

  if (loading) {
    return (
      <div className="noticias-relacionadas-container">
        <div className="noticias-relacionadas-loading">
          Cargando noticias relacionadas...
        </div>
      </div>
    );
  }

  if (noticiasRelacionadas.length === 0) {
    return null;
  }

  return (
    <div className="noticias-relacionadas-container">
      <div className="noticias-relacionadas-header">
        <h2 className="noticias-relacionadas-title">
          Noticias Relacionadas
        </h2>
        <div className="noticias-relacionadas-subtitle">
          Más contenido de {categoriaActual}
        </div>
        
        {/* Botones de navegación */}
        <div className="noticias-relacionadas-navigation">
          <button 
            onClick={scrollLeft} 
            className="nav-button nav-button-left"
            aria-label="Noticias anteriores"
          >
            <FiChevronLeft />
          </button>
          <button 
            onClick={scrollRight} 
            className="nav-button nav-button-right"
            aria-label="Siguientes noticias"
          >
            <FiChevronRight />
          </button>
        </div>
      </div>
      
      {/* Contenedor horizontal scrollable */}
      <div className="noticias-relacionadas-scroll-container">
        <div 
          className="noticias-relacionadas-scroll" 
          ref={scrollRef}
        >
          {noticiasRelacionadas.map((noticia) => (
            <div 
              key={noticia.id} 
              className="noticia-relacionada-card"
              onClick={() => handleNoticiaClick(noticia)}
            >
              <div className="noticia-relacionada-image-container">
                <img
                  src={noticia.imagen}
                  alt={noticia.titulo}
                  className="noticia-relacionada-image"
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/300x200/1a1a1a/ffffff?text=Imagen+No+Disponible';
                  }}
                />
                <div className="noticia-relacionada-overlay"></div>
                <div className="noticia-relacionada-category">
                  {noticia.categoria}
                </div>
              </div>
              
              <div className="noticia-relacionada-content">
                <h3 className="noticia-relacionada-title">
                  {noticia.titulo}
                </h3>
                <p className="noticia-relacionada-summary">
                  {noticia.resumen.substring(0, 120)}...
                </p>
                
                <div className="noticia-relacionada-meta">
                  <span className="noticia-relacionada-date">
                    {new Date(noticia.fecha).toLocaleDateString('es-AR', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}
                  </span>
                  <span className="noticia-relacionada-fuente">
                    {noticia.fuente}
                  </span>
                </div>
              </div>
              
              <div className="noticia-relacionada-hover-effect"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default NoticiasRelacionadas;