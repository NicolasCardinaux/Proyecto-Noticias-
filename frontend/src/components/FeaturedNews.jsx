import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // Usaremos axios para consistencia
import '../styles/FeaturedNews.css'; 

function FeaturedNews() {
  const [techNews, setTechNews] = useState([]);
  const [businessNews, setBusinessNews] = useState([]);
  const [currentBusinessIndex, setCurrentBusinessIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFeaturedNews = async () => {
      try {
        // Apuntamos al backend de Flask
        // ASUMIMOS que el endpoint /api/noticias devuelve todas las noticias
        // ordenadas por fecha de forma descendente (más recientes primero).
        const response = await axios.get('http://localhost:5000/api/noticias');
        const newsData = response.data;

        // Noticias de TECNOLOGÍA (las dos más recientes)
        const technology = newsData
          .filter(n => n.categoria?.toLowerCase() === 'tecnología')
          .slice(0, 2);
        
        // Noticias de NEGOCIOS (las cinco más recientes para el carrusel)
        const business = newsData
          .filter(n => n.categoria?.toLowerCase() === 'negocios')
          .slice(0, 5); // 👈 **CAMBIO CLAVE: Limitado a 5 noticias**

        setTechNews(technology);
        setBusinessNews(business);

      } catch (err) {
        console.error("Error al cargar noticias destacadas:", err);
      } finally {
        setLoading(false);
      }
    };

    // Esta llamada se realiza al montar el componente, por lo que cargará 
    // las 5 noticias más recientes (según el orden del backend) cada vez que 
    // el usuario acceda a esta página.
    fetchFeaturedNews();
  }, []);

  // --- LÓGICA DE CLIC CORREGIDA ---
  const handleCardClick = async (noticia) => {
    if (!noticia || !noticia.id) return;
    try {
      // Registramos el clic
      await axios.post(`http://localhost:5000/api/noticias/${noticia.id}/click`);
    } catch (err) {
      console.error("Error al registrar el clic:", err);
    }
    // Navegamos usando el ID de la base de datos
    navigate(`/noticia/${noticia.id}`);
  };

  const handleNext = (e) => {
    e.stopPropagation();
    // Verifica que haya noticias antes de calcular el índice
    if (businessNews.length > 0) {
      setCurrentBusinessIndex((prev) => (prev + 1) % businessNews.length);
    }
  };

  const handlePrev = (e) => {
    e.stopPropagation();
    // Verifica que haya noticias antes de calcular el índice
    if (businessNews.length > 0) {
      setCurrentBusinessIndex((prev) => (prev - 1 + businessNews.length) % businessNews.length);
    }
  };
  
  if (loading || (techNews.length === 0 && businessNews.length === 0)) {
    return null;
  }

  return (
    <div className="featured-news-container">
      {/* --- TARJETAS DE TECNOLOGÍA (VERTICALES) --- */}
      {techNews.map((noticia) => (
        <div key={noticia.id} className="news-card static-card" onClick={() => handleCardClick(noticia)}>
          <img src={noticia.imagen} alt={noticia.titulo} className="card-image" />
          <div className="text-overlay">
            <h3>{noticia.titulo}</h3>
            <p>{noticia.resumen.substring(0, 90)}...</p>
          </div>
        </div>
      ))}

      {/* --- CARRUSEL DE NEGOCIOS (Limitado a 5 noticias) --- */}
      {businessNews.length > 0 && (
        <div className="news-card slider-card">
          <div className="slider-wrapper" style={{ transform: `translateX(-${currentBusinessIndex * 100}%)` }}>
            {businessNews.map((noticia) => (
              <div key={noticia.id} className="slider-item" onClick={() => handleCardClick(noticia)}>
                <img src={noticia.imagen} alt={noticia.titulo} className="card-image" />
                <div className="text-overlay">
                  <h3>{noticia.titulo}</h3>
                  <p>{noticia.resumen.substring(0, 100)}...</p>
                </div>
              </div>
            ))}
          </div>
          <button onClick={handlePrev} className="slider-control prev" aria-label="Noticia Anterior">&lt;</button>
          <button onClick={handleNext} className="slider-control next" aria-label="Noticia Siguiente">&gt;</button>
          <div className="slider-dots">
            {businessNews.map((_, index) => (
              <span
                key={`dot-${index}`}
                className={`dot ${index === currentBusinessIndex ? 'active' : ''}`}
                onClick={(e) => { e.stopPropagation(); setCurrentBusinessIndex(index); }}
                aria-label={`Ir a la noticia ${index + 1}`}
              ></span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FeaturedNews;