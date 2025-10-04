import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/HealthScienceNews.css';

function HealthScienceNews() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchHealthScienceNews = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/noticias');
        const allNews = response.data;
        
        const allFilteredNews = allNews.filter(
          (noticia) => 
            noticia.categoria && 
            (noticia.categoria.toLowerCase() === 'salud' || noticia.categoria.toLowerCase() === 'ciencia')
        );

        setPosts(allFilteredNews);
      } catch (err) {
        setError('No se pudieron cargar las noticias de Salud y Ciencia.');
        console.error('Error fetching health and science news:', err);
      }
    };

    fetchHealthScienceNews();
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
    <div className="health-science-container">
      <div className="health-science-header">
        <h2 className="health-science-title">Salud y Ciencia</h2>
        <div className="health-science-navigation-buttons">
          <button onClick={scrollLeft} className="health-science-nav-button">
            &lt;
          </button>
          <button onClick={scrollRight} className="health-science-nav-button">
            &gt;
          </button>
        </div>
      </div>
      <div className="health-science-carousel" ref={scrollRef}>
        {posts.map((post) => (
          <div key={post.id} className="health-science-card" onClick={() => handlePostClick(post)}>
            <div className="health-science-image-container">
              <img
                src={post.imagen}
                alt={post.titulo}
                className="health-science-image"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/400x200.png?text=Sin+Imagen';
                }}
              />
              {/* Badge de categoría agregado */}
              <div className="health-science-category-badge">
                {post.categoria}
              </div>
              <div className="health-science-image-overlay"></div>
            </div>
            <div className="health-science-content">
              <h3 className="health-science-title-card">{post.titulo}</h3>
              <p className="health-science-summary">{post.resumen.substring(0, 90)}...</p>
              <div className="health-science-meta">
                <span className="health-science-source">{post.fuente}</span>
                <span className="health-science-date">{new Date(post.fecha).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default HealthScienceNews;