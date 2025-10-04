import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/InterestPosts.css';

function InterestPosts() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRandomPosts = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/random-posts');
        setPosts(response.data);
      } catch (err) {
        setError('No se pudieron cargar las noticias de interés.');
        console.error('Error fetching random posts:', err);
      }
    };

    fetchRandomPosts();
  }, []);

  const handlePostClick = (noticia) => {
    axios.post(`http://localhost:5000/api/noticias/${noticia.id}/click`)
      .catch(err => console.error('Error al registrar el clic:', err));
    navigate(`/noticia/${noticia.id}`);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Fecha no disponible';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'Fecha inválida';
    }
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('es-AR', options);
  };
  
  if (error || posts.length === 0) {
    return null;
  }

  return (
    <div className="interest-posts-container">
      <div className="interest-posts-header">
        <h2 className="interest-posts-title">Noticias de Interés</h2>
        {/* Sin botón "Ver Todas" */}
      </div>
      <div className="interest-posts-grid">
        {posts.map((post) => (
          <div key={post.id} className="interest-post-card" onClick={() => handlePostClick(post)}>
            <div className="interest-post-image-container">
              <img
                src={post.imagen}
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
                {post.resumen.substring(0, 100)}...
              </p>
              <div className="interest-post-meta">
                <span className="interest-post-date">{formatDate(post.fecha)}</span>
                <span className="interest-post-category">{post.categoria}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default InterestPosts;