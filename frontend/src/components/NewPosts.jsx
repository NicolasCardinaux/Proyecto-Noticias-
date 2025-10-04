import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/NewPosts.css';

function NewPosts() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchLatestPosts = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/latest-by-category');
        setPosts(response.data);
      } catch (err) {
        setError('No se pudieron cargar las últimas noticias.');
        console.error('Error fetching latest posts:', err);
      }
    };

    fetchLatestPosts();
  }, []);

  const handlePostClick = (noticia) => {
    axios.post(`http://localhost:5000/api/noticias/${noticia.id}/click`)
      .catch(err => console.error('Error al registrar el clic:', err));
    navigate(`/noticia/${noticia.id}`);
  };

  // Función para ver todas las noticias (más recientes primero)
  const handleShowAll = () => {
    navigate('/?filter=latest');
  };

  if (error || posts.length === 0) {
    return null;
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Fecha no disponible';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'Fecha inválida';
    }
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('es-AR', options);
  };

  return (
    <div className="new-posts-container">
      <div className="new-posts-header">
        <h2 className="new-posts-title">Últimas Noticias</h2>
        <button className="show-all-button" onClick={handleShowAll}>
          Ver Todas &gt;
        </button>
      </div>
      <div className="new-posts-grid">
        {posts.map((post) => (
          <div key={post.id} className="post-item-card" onClick={() => handlePostClick(post)}>
            <div className="post-item-image-container">
              <img
                src={post.imagen}
                alt={post.titulo}
                className="post-item-image"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/200x200/1a1a1a/ffffff?text=Sin+Imagen';
                }}
              />
              {/* Solo overlay, sin badge rojo */}
              <div className="post-image-overlay"></div>
            </div>
            <div className="post-item-content">
              <h3 className="post-item-title">{post.titulo}</h3>
              <p className="post-item-summary">
                {post.resumen.substring(0, 100)}...
              </p>
              <div className="post-meta">
                <span className="post-date">{formatDate(post.fecha)}</span>
                <span className="post-category">{post.categoria}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NewPosts;