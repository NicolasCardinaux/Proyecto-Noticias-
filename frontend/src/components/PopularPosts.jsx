import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/PopularPosts.css';

function PopularPosts() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchPopularPosts = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/popular-posts');
        setPosts(response.data);
      } catch (err) {
        setError('No se pudieron cargar los posts populares.');
        console.error('Error fetching popular posts:', err);
      }
    };

    fetchPopularPosts();
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
    <div className="popular-posts-container">
      <div className="popular-posts-header">
        <h2 className="popular-posts-title">Noticias Populares</h2>
        <div className="navigation-buttons">
          <button onClick={scrollLeft} className="nav-button">
            &lt;
          </button>
          <button onClick={scrollRight} className="nav-button">
            &gt;
          </button>
        </div>
      </div>
      <div className="posts-carousel" ref={scrollRef}>
        {posts.map((post) => (
          <div key={post.id} className="post-card" onClick={() => handlePostClick(post)}>
            <div className="post-image-container">
              <img
                src={post.imagen}
                alt={post.titulo}
                className="post-image"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/400x200.png?text=Sin+Imagen';
                }}
              />
              {/* Badge de categoría agregado */}
              <div className="post-category-badge">
                {post.categoria}
              </div>
              <div className="post-image-overlay"></div>
            </div>
            <div className="post-content">
              <h3 className="post-title-card">{post.titulo}</h3>
              <p className="post-summary">{post.resumen.substring(0, 90)}...</p>
              <div className="post-meta">
                <span className="post-source">{post.fuente}</span>
                <span className="post-date">{new Date(post.fecha).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PopularPosts;