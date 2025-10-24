import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/EntertainmentSportsNews.css';
import noImagePlaceholder from '../imagenes/no-image.png';


const API_BASE_URL = import.meta.env.VITE_API_URL;

function EntertainmentSportsNews() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchEntertainmentSportsNews = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/noticias`);
        const allNews = response.data;
        
        const allFilteredNews = allNews.filter(
          (noticia) => 
            noticia.categoria && 
            (noticia.categoria.toLowerCase() === 'entretenimiento' || noticia.categoria.toLowerCase() === 'deportes')
        );

        setPosts(allFilteredNews);
      } catch (err) {
        setError('No se pudieron cargar las noticias de Entretenimiento y Deportes.');
        console.error('Error fetching entertainment and sports news:', err);
      }
    };

    fetchEntertainmentSportsNews();
  }, []);

  const handlePostClick = (noticia) => {
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

  if (error) {
    return <div className="text-center text-[#8a0009] p-4">{error}</div>;
  }

  if (posts.length === 0) {
    return null;
  }

  return (
    <div className="entertainment-sports-container">
      <div className="entertainment-sports-header">
        <h2 className="entertainment-sports-title">Entretenimiento y Deportes</h2>
        <div className="entertainment-sports-navigation-buttons">
          <button onClick={scrollLeft} className="entertainment-sports-nav-button">
            &lt;
          </button>
          <button onClick={scrollRight} className="entertainment-sports-nav-button">
            &gt;
          </button>
        </div>
      </div>
      <div className="entertainment-sports-carousel" ref={scrollRef}>
        {posts.map((post) => (
          <div key={post.id} className="entertainment-sports-card" onClick={() => handlePostClick(post)}>
            <div className="entertainment-sports-image-container">
              <img
                src={post.imagen}
                alt={post.titulo}
                className="entertainment-sports-image"
                onError={(e) => {
                  e.target.src = noImagePlaceholder;
                }}
              />
              {}
              <div className="entertainment-sports-category-badge">
                {post.categoria}
              </div>
              <div className="entertainment-sports-image-overlay"></div>
            </div>
            <div className="entertainment-sports-content">
              <h3 className="entertainment-sports-title-card">{post.titulo}</h3>
              <p className="entertainment-sports-summary">{post.resumen.substring(0, 90)}...</p>
              <div className="entertainment-sports-meta">
                <span className="entertainment-sports-source">{post.fuente}</span>
                <span className="entertainment-sports-date">{new Date(post.fecha).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default EntertainmentSportsNews;