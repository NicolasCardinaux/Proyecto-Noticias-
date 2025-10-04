import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../styles/NasaDataWidget.css';
import NasaFondo from '../imagenes/Nasa.jpg';

const SECTIONS = ['Imagen Astronómica del Día', 'Últimas Fotos desde Marte', 'Asteroides Cercanos', 'Eventos Naturales en la Tierra'];
const NASA_API_KEY = import.meta.env.VITE_NASA_API_KEY;

// Función para traducir APOD usando el nuevo endpoint con caché
const translateApodWithCache = async (apodData) => {
    if (!apodData || !apodData.title || !apodData.explanation) {
        return apodData;
    }

    try {
        const response = await axios.post('http://localhost:5000/api/translate-apod', {
            title: apodData.title,
            explanation: apodData.explanation,
            date: apodData.date || new Date().toISOString().split('T')[0]
        });

        const { translatedTitle, translatedExplanation, fromCache } = response.data;
        
        console.log(`✅ APOD traducido (desde caché: ${fromCache})`);
        
        return {
            ...apodData,
            title: translatedTitle,
            explanation: translatedExplanation
        };
    } catch (error) {
        console.error('❌ Error traduciendo APOD:', error);
        // En caso de error, devolver el original
        return apodData;
    }
};

function NasaDataWidget() {
    const [data, setData] = useState({ apod: null, mars: null, asteroids: null, eonet: null });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [currentMarsIndex, setCurrentMarsIndex] = useState(null);
    const [currentApodIndex, setCurrentApodIndex] = useState(null);
    const scrollRef = useRef(null);
    const [isTranslating, setIsTranslating] = useState(false);

    useEffect(() => {
        const fetchAllData = async () => {
            setLoading(true);
            setError(null);
            
            if (!NASA_API_KEY) {
                setError("La clave de la API de la NASA no está configurada.");
                setLoading(false);
                return;
            }

            try {
                const today = new Date().toISOString().split('T')[0];
                const [apodRes, marsRes, asteroidsRes, eonetRes] = await Promise.all([
                    axios.get(`https://api.nasa.gov/planetary/apod?api_key=${NASA_API_KEY}`),
                    axios.get(`https://api.nasa.gov/mars-photos/api/v1/rovers/perseverance/latest_photos?api_key=${NASA_API_KEY}`),
                    axios.get(`https://api.nasa.gov/neo/rest/v1/feed?start_date=${today}&api_key=${NASA_API_KEY}`),
                    axios.get('https://eonet.gsfc.nasa.gov/api/v2.1/events?limit=20&status=open')
                ]);

                const nearEarthObjects = asteroidsRes.data.near_earth_objects;
                const asteroidsList = Object.values(nearEarthObjects).flat().sort((a, b) => a.close_approach_data[0].epoch_date_close_approach - b.close_approach_data[0].epoch_date_close_approach);

                // Primero establecer los datos originales
                const originalData = {
                    apod: apodRes.data,
                    mars: marsRes.data.latest_photos.slice(0, 12),
                    asteroids: asteroidsList,
                    eonet: eonetRes.data.events,
                };

                setData(originalData);

                // Luego traducir el APOD (solo si no está en caché)
                if (apodRes.data) {
                    setIsTranslating(true);
                    const translatedApod = await translateApodWithCache(apodRes.data);
                    setData(prev => ({ ...prev, apod: translatedApod }));
                    setIsTranslating(false);
                }

            } catch (err) {
                console.error("Error fetching NASA data:", err);
                setError("No se pudieron cargar los datos del espacio.");
            } finally {
                setLoading(false);
            }
        };

        fetchAllData();
    }, []);

    // Resto del componente se mantiene igual...
    useEffect(() => {
        const handleScroll = () => {
            if (scrollRef.current) {
                const { scrollLeft, clientWidth } = scrollRef.current;
                const index = Math.round(scrollLeft / clientWidth);
                if (index !== currentIndex) setCurrentIndex(index);
            }
        };
        const scrollContainer = scrollRef.current;
        scrollContainer?.addEventListener('scroll', handleScroll, { passive: true });
        return () => scrollContainer?.removeEventListener('scroll', handleScroll);
    }, [currentIndex]);

    const scroll = (direction) => {
        if (scrollRef.current) {
            const { clientWidth } = scrollRef.current;
            const newIndex = direction === 'left'
                ? Math.max(currentIndex - 1, 0)
                : Math.min(currentIndex + 1, SECTIONS.length - 1);

            scrollRef.current.scrollTo({ left: newIndex * clientWidth, behavior: 'smooth' });
            setCurrentIndex(newIndex);
        }
    };

    // Funciones para el modal de Marte
    const handleMarsPhotoClick = (index) => {
        setCurrentMarsIndex(index);
    };

    const showPrevMarsPhoto = () => {
        if (data.mars) {
            setCurrentMarsIndex((prev) => 
                prev === 0 ? data.mars.length - 1 : prev - 1
            );
        }
    };

    const showNextMarsPhoto = () => {
        if (data.mars) {
            setCurrentMarsIndex((prev) => 
                prev === data.mars.length - 1 ? 0 : prev + 1
            );
        }
    };

    const closeMarsModal = () => {
        setCurrentMarsIndex(null);
    };

    // Funciones para el modal de APOD (solo imagen)
    const handleApodImageClick = () => {
        setCurrentApodIndex(0);
    };

    const closeApodModal = () => {
        setCurrentApodIndex(null);
    };

    return (
        <div className="nasa-widget-container">
            <div className="nasa-background" style={{ backgroundImage: `url(${NasaFondo})` }}></div>
            <div className="container mx-auto px-4 py-8 relative z-10">
                
                <div className="nasa-header">
                    <h2 className="nasa-title">Ventana al Universo</h2>
                    <div className="nasa-title-underline"></div>
                    <div className="nasa-nav-buttons">
                        <button onClick={() => scroll('left')} className="nasa-nav-button">&lt;</button>
                        <button onClick={() => scroll('right')} className="nasa-nav-button">&gt;</button>
                    </div>
                </div>

                {!loading && !error && (
                    <h3 className="nasa-section-title">{SECTIONS[currentIndex]}</h3>
                )}

                {loading && <p className="nasa-message">Explorando el cosmos...</p>}
                {isTranslating && <p className="nasa-message">Traduciendo contenido...</p>}
                {error && <p className="nasa-message error">{error}</p>}

                {!loading && !error && data.apod && (
                    <div className="nasa-carousel-container" ref={scrollRef}>
                        
                        {/* --- SECCIÓN APOD --- */}
                        <div className="nasa-slide">
                            <div className="nasa-card apod-card">
                                <img 
                                    src={data.apod.url} 
                                    alt={data.apod.title} 
                                    className="apod-image" 
                                    onClick={handleApodImageClick}
                                    style={{ cursor: 'pointer' }}
                                />
                                <div className="apod-content">
                                    <h4 className="apod-title">{data.apod.title}</h4>
                                    <p className="apod-explanation">{data.apod.explanation}</p>
                                </div>
                            </div>
                        </div>

                        {/* Resto de las secciones se mantienen igual */}
                        <div className="nasa-slide">
                            <div className="nasa-card">
                                <h3 className="nasa-card-title">Rover Perseverance</h3>
                                <div className="mars-grid">
                                    {data.mars?.map((photo, index) => (
                                        <img 
                                            key={photo.id} 
                                            src={photo.img_src} 
                                            alt={`Foto de Marte - ${photo.id}`} 
                                            className="mars-photo" 
                                            onClick={() => handleMarsPhotoClick(index)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="nasa-slide">
                            <div className="nasa-card">
                                <h3 className="nasa-card-title">Objetos Próximos a la Tierra</h3>
                                <div className="nasa-card-list">
                                    {data.asteroids?.map(a => (
                                        <div key={a.id} className="nasa-list-item">
                                            <div className="nasa-item-name">
                                                <span>{a.name}</span>
                                                {a.is_potentially_hazardous_asteroid && <span className="hazard-tag">¡Peligro Potencial!</span>}
                                            </div>
                                            <div className="nasa-item-details">
                                                <span>Ø {(a.estimated_diameter.meters.estimated_diameter_min.toFixed(0))} - {a.estimated_diameter.meters.estimated_diameter_max.toFixed(0)} m</span>
                                                <span className="passing-date">
                                                    Pasa el: {new Date(a.close_approach_data[0].epoch_date_close_approach).toLocaleDateString('es-ES')}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        
                        <div className="nasa-slide">
                            <div className="nasa-card">
                                <h3 className="nasa-card-title">Observatorio de la Tierra</h3>
                                <div className="nasa-card-list">
                                    {data.eonet?.map(e => (
                                        <div key={e.id} className="nasa-list-item">
                                            <span className="nasa-item-name">{e.title}</span>
                                            <span className="item-details-box">{e.categories[0].title}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                    </div>
                )}
            </div>

            {/* Modales se mantienen igual */}
            {currentApodIndex !== null && (
                <div className="apod-modal-overlay" onClick={closeApodModal}>
                    <div className="apod-modal-content" onClick={e => e.stopPropagation()}>
                        <button className="apod-modal-close-button" onClick={closeApodModal}>
                            <div className="close-icon-line line-1"></div>
                            <div className="close-icon-line line-2"></div>
                        </button>
                        <img 
                            src={data.apod.url} 
                            alt={data.apod.title} 
                            className="apod-modal-image" 
                        />
                    </div>
                </div>
            )}

            {currentMarsIndex !== null && (
                <div className="mars-modal-overlay" onClick={closeMarsModal}>
                    <div className="mars-modal-content" onClick={e => e.stopPropagation()}>
                        <button className="mars-modal-close-button" onClick={closeMarsModal}>
                            <div className="close-icon-line line-1"></div>
                            <div className="close-icon-line line-2"></div>
                        </button>
                        <button className="mars-nav-button left" onClick={showPrevMarsPhoto}>
                            &#10094;
                        </button>
                        <img 
                            src={data.mars[currentMarsIndex].img_src} 
                            alt={`Foto de Marte ampliada - ${data.mars[currentMarsIndex].id}`} 
                            className="mars-modal-image" 
                        />
                        <button className="mars-nav-button right" onClick={showNextMarsPhoto}>
                            &#10095;
                        </button>
                        <div className="mars-modal-details">
                            <p>Rover: {data.mars[currentMarsIndex].rover.name}</p>
                            <p>Cámara: {data.mars[currentMarsIndex].camera.full_name}</p>
                            <p>Fecha de toma: {data.mars[currentMarsIndex].earth_date}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default NasaDataWidget;