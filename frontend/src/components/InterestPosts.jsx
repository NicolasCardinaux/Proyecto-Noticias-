import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/InterestPosts.css';

function InterestPosts() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRandomPosts = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://localhost:5000/api/random-posts');
        
        if (response.data && response.data.length > 0) {
          setPosts(response.data);
        } else {
          setError('No hay noticias de interés disponibles.');
        }
      } catch (err) {
        console.error('Error fetching random posts:', err);
        setError('No se pudieron cargar las noticias de interés.');
      } finally {
        setLoading(false);
      }
    };

    fetchRandomPosts();
  }, []);

  const handlePostClick = (noticia) => {
    if (noticia && noticia.id) {
      axios.post(`http://localhost:5000/api/noticias/${noticia.id}/click`)
        .catch(err => console.error('Error al registrar el clic:', err));
      navigate(`/noticia/${noticia.id}`);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Fecha no disponible';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Fecha inválida';
      }
      const options = { year: 'numeric', month: 'long', day: 'numeric' };
      return date.toLocaleDateString('es-AR', options);
    } catch {
      return 'Fecha no disponible';
    }
  };

  // Mostrar loading
  if (loading) {
    return (
      <div className="interest-posts-container">
        <div className="interest-posts-header">
          <h2 className="interest-posts-title">Noticias de Interés</h2>
        </div>
        <div className="loading-message">Cargando noticias...</div>
      </div>
    );
  }

  // No mostrar nada si hay error o no hay posts
  if (error || posts.length === 0) {
    return null;
  }

  return (
    <div className="interest-posts-container">
      <div className="interest-posts-header">
        <h2 className="interest-posts-title">Noticias de Interés</h2>
      </div>
      <div className="interest-posts-grid">
        {posts.map((post) => (
          <div key={post.id} className="interest-post-card" onClick={() => handlePostClick(post)}>
            <div className="interest-post-image-container">
              <img
                src={post.imagen || 'https://via.placeholder.com/200x200/1a1a1a/ffffff?text=Sin+Imagen'}
                alt={post.titulo}
                className="interest-post-image"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/200x200/1a1a1a/ffffff?text=Sin+Imagen';
                }}
              />
              <div className="interest-post-image-overlay"></div>
            </div>
            <div className="interest-post-content">
              <h3 className="interest-post-title-card">{post.titulo}</h3>
              <p className="interest-post-summary">
                {post.resumen ? `${post.resumen.substring(0, 100)}...` : 'Resumen no disponible'}
              </p>
              <div className="interest-post-meta">
                <span className="interest-post-date">{formatDate(post.fecha)}</span>
                <span className="interest-post-category">{post.categoria || 'General'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default InterestPosts;