import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';


import ParticlesBackground from './ParticlesBackground';
import CategoryFilter from './CategoryFilter';
import '../styles/noticiasList.css';


import FeaturedNews from './FeaturedNews';
import PopularPosts from './PopularPosts';
import WeatherWidget from './WeatherWidget';
import NewPosts from './NewPosts';
import FootballDataWidget from './FootballDataWidget';
import InterestPosts from './InterestPosts';
import MundoInversion from './MundoInversion';
import HealthScienceNews from './HealthScienceNews';
import NasaDataWidget from './NasaDataWidget';
import EntertainmentSportsNews from './EntertainmentSportsNews';
import QuoteOfTheDay from './QuoteOfTheDay';


const API_BASE_URL = "https://proyecto-noticias-api.onrender.com";

function NoticiasList() {
  const [noticias, setNoticias] = useState([]);
  const [filteredNoticias, setFilteredNoticias] = useState([]);
  const [error, setError] = useState(null);
  const [filtroActivo, setFiltroActivo] = useState('mas-recientes'); 
  const { category } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('q');
  const filterType = searchParams.get('type');
  const filterLatest = searchParams.get('filter') === 'latest';

  useEffect(() => {
    fetchNoticias();
  }, []);

  useEffect(() => {
    if (noticias.length > 0) {
      aplicarFiltros();
    }
  }, [noticias, category, searchQuery, filterLatest, filterType, filtroActivo]); 

  const fetchNoticias = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/noticias`);
      setNoticias(response.data);
    } catch (err) {
      setError('Error al cargar las noticias');
      console.error('Error en fetchNoticias:', err);
    }
  };


  const aplicarFiltros = () => {
    let filtered = [...noticias];


    if (filterLatest) {

      filtered = filtered;
    }

    else if (searchQuery && filterType !== 'fuente') {
      const decodedQuery = decodeURIComponent(searchQuery).toLowerCase();
      filtered = filtered.filter(
        (noticia) =>
          noticia.titulo && noticia.titulo.toLowerCase().includes(decodedQuery)
      );
    }

    else if (searchQuery && filterType === 'fuente') {
      const decodedQuery = decodeURIComponent(searchQuery).toLowerCase();
      filtered = filtered.filter(
        (noticia) =>
          noticia.fuente &&
          noticia.fuente.toLowerCase().includes(decodedQuery)
      );
    }

    else if (category && category !== 'general') {
      const decodedCategory = decodeURIComponent(category);
      filtered = filtered.filter(
        (noticia) =>
          noticia.categoria &&
          noticia.categoria.toLowerCase() === decodedCategory.toLowerCase()
      );
    }

    else {
      filtered = []; 
    }


    if (filtered.length > 0) {
      switch (filtroActivo) {
        case 'mas-recientes':
          filtered.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
          break;
        
        case 'mas-populares':
          filtered.sort((a, b) => (b.clics || 0) - (a.clics || 0));
          break;
        
        case 'titulo-az':
          filtered.sort((a, b) => a.titulo?.localeCompare(b.titulo || ''));
          break;
        
        case 'titulo-za':
          filtered.sort((a, b) => b.titulo?.localeCompare(a.titulo || ''));
          break;
        
        default:
          filtered.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
      }
    }


    if (filtered.length === 0) {
      if (searchQuery) {
        if (filterType === 'fuente') {
          setError(`No se encontraron noticias de la fuente: ${searchQuery}`);
        } else {
          setError('No se encontraron noticias con ese título.');
        }
      } else if (category && category !== 'general') {
        setError('No se encontraron noticias para esta categoría');
      } else if (filterLatest) {
        setError('No se encontraron noticias.');
      } else {
        setError(null);
      }
    } else {
      setError(null);
    }

    setFilteredNoticias(filtered);
  };

  const handleClick = (noticia) => {
    axios.post(`${API_BASE_URL}/api/noticias/${noticia.id}/click`)
      .catch(err => console.error('Error al registrar el clic:', err));
    navigate(`/noticia/${noticia.id}`);
  };

  const handleClearFilters = () => {
    navigate('/');
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


  const getSectionTitle = () => {
    if (filterLatest) {
      return 'Todas las Noticias';
    } else if (searchQuery) {
      if (filterType === 'fuente') {
        return `Noticias de la Fuente: ${searchQuery}`;
      } else {
        return `Resultados para: "${searchQuery}"`;
      }
    } else if (category && category !== 'general') {

      const categoryName = category.charAt(0).toUpperCase() + category.slice(1);
      return `Noticias de ${categoryName}`;
    }
    return '';
  };


  const getSectionSubtitle = () => {
    if (filteredNoticias.length > 0) {
      const countText = `${filteredNoticias.length} noticia${filteredNoticias.length !== 1 ? 's' : ''} encontrada${filteredNoticias.length !== 1 ? 's' : ''}`;
      
      if (filterLatest) {
        return `${countText} - ${getFiltroText()}`;
      } else if (filterType === 'fuente') {
        return `${countText} de esta fuente - ${getFiltroText()}`;
      }
      return `${countText} - ${getFiltroText()}`;
    }
    return '';
  };

  return (
    <div className="noticias-list">
      <ParticlesBackground />
      <div className="relative z-10 min-h-screen bg-transparent flex flex-col">
        <CategoryFilter />

        {}
        {(!category || category === 'general') && !searchQuery && !filterLatest && (
          <>
            {}
            <div id="noticias-destacadas">
              <FeaturedNews />
            </div>
            
            {}
            <div id="noticias-populares">
              <PopularPosts />
            </div>
            
            <div className="container mx-auto my-8 px-4">
              {}
              <div id="clima-actual">
                <div className="flex flex-col items-center mb-8">
                  <h2 className="relative z-10 text-4xl md:text-5xl font-bold text-[#b3000c] uppercase tracking-widest text-3d">
                    Clima Actual
                  </h2>
                  <div className="mt-3 h-1 w-32 bg-gradient-to-r from-transparent via-[#b3000c] to-transparent"></div>
                </div>
                <WeatherWidget />
              </div>
              
              {}
              <div id="ultimas-noticias">
                <NewPosts />
              </div>
              
              {}
              <div id="mundo-futbol">
                <FootballDataWidget />
              </div>
              
              {}
              <div id="noticias-interes">
                <InterestPosts />
              </div>
              
              {}
              <div id="mundo-inversion">
                <MundoInversion /> 
              </div>
              
              {}
              <div id="salud-ciencia">
                <HealthScienceNews />
              </div>
              
              {}
              <div id="ventana-universo">
                <NasaDataWidget />
              </div>
              
              {}
              <div id="entretenimiento-deportes">
                <EntertainmentSportsNews />
              </div>
            </div>
            
            {}
            <div id="frase-dia">
              <QuoteOfTheDay />
            </div>
          </>
        )}

        {}
        {(searchQuery || (category && category !== 'general') || filterLatest) && (
          <div className="noticias-grid-container">
            {}
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

            {error && (
              <div className="error-state">
                {error}
              </div>
            )}

            {!error && filteredNoticias.length > 0 && (
              <>
                <div className="section-header">
                  <h1 className="section-title">
                    {getSectionTitle()}
                  </h1>
                  <p className="section-subtitle">
                    {getSectionSubtitle()}
                  </p>
                  <div className="section-divider"></div>
                  
                  {}
                  {(searchQuery || category || filterLatest) && (
                    <button 
                      onClick={handleClearFilters}
                      className="clear-filters-btn"
                    >
                      &larr; Volver a la vista general
                    </button>
                  )}
                </div>
                
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
              </>
            )}

            {!error && filteredNoticias.length === 0 && noticias.length > 0 && (
              <div className="error-state">
                No se encontraron noticias que coincidan con tu búsqueda.
              </div>
            )}
          </div>
        )}

        {}
        {!error && filteredNoticias.length === 0 && noticias.length === 0 && (
          <div className="loading-state">
            Cargando noticias...
          </div>
        )}
      </div>
    </div>
  );
}

export default NoticiasList;