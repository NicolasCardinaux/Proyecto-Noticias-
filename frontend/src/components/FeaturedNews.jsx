import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; 
import '../styles/FeaturedNews.css'; 


const API_BASE_URL = import.meta.env.VITE_API_URL;

function FeaturedNews() {
  const [techNews, setTechNews] = useState([]);
  const [businessNews, setBusinessNews] = useState([]);
  const [currentBusinessIndex, setCurrentBusinessIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFeaturedNews = async () => {
      try {

        const response = await axios.get(`${API_BASE_URL}/api/noticias`);
        const newsData = response.data;


        const technology = newsData
          .filter(n => n.categoria?.toLowerCase() === 'tecnología')
          .slice(0, 2);
        

        const business = newsData
          .filter(n => n.categoria?.toLowerCase() === 'negocios')
          .slice(0, 5); 

        setTechNews(technology);
        setBusinessNews(business);

      } catch (err) {
        console.error("Error al cargar noticias destacadas:", err);
      } finally {
        setLoading(false);
      }
    };


    fetchFeaturedNews();
  }, []);


  const handleCardClick = async (noticia) => {
    if (!noticia || !noticia.id) return;
    try {

      await axios.post(`${API_BASE_URL}/api/noticias/${noticia.id}/click`);
    } catch (err) {
      console.error("Error al registrar el clic:", err);
    }

    navigate(`/noticia/${noticia.id}`);
  };

  const handleNext = (e) => {
    e.stopPropagation();

    if (businessNews.length > 0) {
      setCurrentBusinessIndex((prev) => (prev + 1) % businessNews.length);
    }
  };

  const handlePrev = (e) => {
    e.stopPropagation();

    if (businessNews.length > 0) {
      setCurrentBusinessIndex((prev) => (prev - 1 + businessNews.length) % businessNews.length);
    }
  };
  
  if (loading || (techNews.length === 0 && businessNews.length === 0)) {
    return null;
  }

  return (
    <div className="featured-news-container">
      {}
      {techNews.map((noticia) => (
        <div key={noticia.id} className="news-card static-card" onClick={() => handleCardClick(noticia)}>
          <img src={noticia.imagen} alt={noticia.titulo} className="card-image" />
          <div className="text-overlay">
            <h3>{noticia.titulo}</h3>
            <p>{noticia.resumen.substring(0, 90)}...</p>
          </div>
        </div>
      ))}

      {}
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