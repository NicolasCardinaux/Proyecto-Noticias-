import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Componentes de Estructura y UI
import ParticlesBackground from './ParticlesBackground';
import CategoryFilter from './CategoryFilter';
import '../styles/noticiasList.css';

function AllNews() {
  const [noticias, setNoticias] = useState([]);
  const [filteredNoticias, setFilteredNoticias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtroActivo, setFiltroActivo] = useState('mas-recientes');
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllNoticias();
  }, []);

  useEffect(() => {
    if (noticias.length > 0) {
      aplicarFiltros();
    }
  }, [noticias, filtroActivo]);

  const fetchAllNoticias = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/api/noticias');
      setNoticias(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar todas las noticias');
      console.error('Error en fetchAllNoticias:', err);
    } finally {
      setLoading(false);
    }
  };

  const aplicarFiltros = () => {
    let noticiasFiltradas = [...noticias];

    // Ordenar según el filtro activo
    switch (filtroActivo) {
      case 'mas-recientes':
        noticiasFiltradas.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
        break;
      
      case 'mas-populares':
        noticiasFiltradas.sort((a, b) => (b.clics || 0) - (a.clics || 0));
        break;
      
      case 'titulo-az':
        noticiasFiltradas.sort((a, b) => a.titulo?.localeCompare(b.titulo || ''));
        break;
      
      case 'titulo-za':
        noticiasFiltradas.sort((a, b) => b.titulo?.localeCompare(a.titulo || ''));
        break;
      
      default:
        noticiasFiltradas.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
    }

    setFilteredNoticias(noticiasFiltradas);
  };

  const handleClick = (noticia) => {
    axios.post(`http://localhost:5000/api/noticias/${noticia.id}/click`)
      .catch(err => console.error('Error al registrar el clic:', err));
    navigate(`/noticia/${noticia.id}`);
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const getTotalNoticiasText = () => {
    return `${filteredNoticias.length} noticia${filteredNoticias.length !== 1 ? 's' : ''} en total`;
  };

  const getFiltroText = () => {
    const textos = {
      'mas-recientes': 'Más recientes primero',
      'mas-populares': 'Más populares (por clics)',
      'titulo-az': 'Orden A-Z',
      'titulo-za': 'Orden Z-A'
    };
    return textos[filtroActivo] || 'Más recientes primero';
  };

  return (
    <div className="noticias-list">
      <ParticlesBackground />
      <div className="relative z-10 min-h-screen bg-transparent flex flex-col">
        <CategoryFilter />
        
        <div className="noticias-grid-container">
          {/* Filtro a la izquierda */}
          <div className="filtro-left-container">
            <div className="filtro-group">
              <label htmlFor="orden-select" className="filtro-label">
                Ordenar por:
              </label>
              <select
                id="orden-select"
                value={filtroActivo}
                onChange={(e) => setFiltroActivo(e.target.value)}
                className="filtro-select"
              >
                <option value="mas-recientes">Más recientes</option>
                <option value="mas-populares">Más populares</option>
                <option value="titulo-az">Título A-Z</option>
                <option value="titulo-za">Título Z-A</option>
              </select>
            </div>
          </div>

          {/* Header de la sección Todas las Noticias - CENTRADO COMO ANTES */}
          <div className="section-header">
            <h1 className="section-title">
              Todas las Noticias
            </h1>
            <p className="section-subtitle">
              {getTotalNoticiasText()} - {getFiltroText()}
            </p>
            <div className="section-divider"></div>
            
            {/* Botón para volver al inicio */}
            <button 
              onClick={handleBackToHome}
              className="clear-filters-btn"
            >
              &larr; Volver al Inicio
            </button>
          </div>

          {/* Estados de carga y error */}
          {loading && (
            <div className="loading-state">
              Cargando todas las noticias...
            </div>
          )}

          {error && (
            <div className="error-state">
              {error}
            </div>
          )}

          {/* Grid de todas las noticias */}
          {!loading && !error && filteredNoticias.length > 0 && (
            <div className="noticias-grid">
              {filteredNoticias.map((noticia) => (
                <div
                  key={noticia.id}
                  className="noticia-card"
                  onClick={() => handleClick(noticia)}
                  data-category={noticia.categoria?.toLowerCase()}
                >
                  <div className="noticia-image-container">
                    <img
                      src={noticia.imagen}
                      alt={noticia.titulo}
                      className="noticia-image"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://via.placeholder.com/400x200/1a1a1a/ffffff?text=Imagen+No+Disponible';
                      }}
                    />
                    <div className="noticia-category-badge">
                      {noticia.categoria}
                    </div>
                    {filtroActivo === 'mas-populares' && noticia.clics > 0 && (
                      <div className="noticia-popular-badge">
                        {noticia.clics} clics
                      </div>
                    )}
                  </div>
                  <div className="noticia-content">
                    <h2 className="noticia-title">
                      {noticia.titulo}
                    </h2>
                    <p className="noticia-summary">
                      {noticia.resumen}
                    </p>
                    <div className="noticia-meta">
                      <span className="noticia-date">
                        {new Date(noticia.fecha).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </span>
                      <div className="noticia-meta-right">
                        {noticia.fuente && (
                          <span className="noticia-source">
                            {noticia.fuente}
                          </span>
                        )}
                        {filtroActivo !== 'mas-populares' && noticia.clics > 0 && (
                          <span className="noticia-clics">
                            {noticia.clics} clics
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!loading && !error && filteredNoticias.length === 0 && (
            <div className="error-state">
              No se encontraron noticias.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AllNews;