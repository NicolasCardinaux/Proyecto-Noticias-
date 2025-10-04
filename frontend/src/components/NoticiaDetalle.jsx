import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { FiArrowLeft, FiExternalLink, FiCalendar, FiTag, FiGlobe } from "react-icons/fi";
import ParticlesBackground from "./ParticlesBackground";
import Breadcrumb from "./Breadcrumb";
import NoticiasRelacionadas from "./NoticiasRelacionadas";
import SidebarNoticia from "./SidebarNoticia";
import "../styles/noticiaDetalle.css";

// URL base de la API
const API_BASE_URL = import.meta.env.VITE_API_URL;

function NoticiaDetalle() {
  const { id } = useParams();
  const [noticia, setNoticia] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // SOLUCIÓN: Forzar scroll al top cuando se carga el componente
  useEffect(() => {
    // Scroll inmediato al top cuando se monta el componente
    window.scrollTo(0, 0);
    
    // Opcional: Scroll suave como alternativa
    // window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [id]); // Se ejecuta cada vez que cambia el ID de la noticia

  useEffect(() => {
    const fetchNoticia = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/noticias`);
        const noticias = response.data;
        const noticiaEncontrada = noticias.find(
          (n) => n.id === parseInt(id)
        );

        if (noticiaEncontrada) {
          setNoticia(noticiaEncontrada);
        } else {
          setError("Noticia no encontrada");
        }
      } catch (err) {
        setError("Error al cargar la noticia");
        console.error(err);
      }
    };

    fetchNoticia();
  }, [id]);

  // También puedes agregar esto para manejar el caso de carga
  useEffect(() => {
    if (noticia) {
      // Asegurar scroll al top cuando la noticia está cargada
      window.scrollTo(0, 0);
    }
  }, [noticia]);

  if (error) {
    return (
      <div className="noticia-detalle-container">
        <div className="text-center p-8">
          <div className="error-state">
            {error}
            <button onClick={() => navigate("/")} className="btn btn-secondary mt-4">
              <FiArrowLeft className="btn-icon" />
              Volver al Inicio
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!noticia) {
    return (
      <div className="noticia-detalle-container">
        <div className="cargando">Cargando noticia...</div>
      </div>
    );
  }

  return (
    <div className="noticia-detalle-container">
      <ParticlesBackground />
      <div className="particles-overlay"></div>
      
      <div className="relative z-5 flex justify-center p-4 md:p-8">
        {/* Contenedor principal que ocupa el 80% */}
        <div className="w-full md:w-4/5">
          <div className="container mx-auto">
            <Breadcrumb categoria={noticia.categoria} titulo={noticia.titulo} />

            {/* Título */}
            <h1 className="noticia-titulo">
              {noticia.titulo}
            </h1>

            {/* Contenedor de imagen */}
            <div className="imagen-container">
              <img
                src={noticia.imagen}
                alt={noticia.titulo}
                className="imagen-principal"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/1200x600/1a1a1a/ffffff?text=Imagen+No+Disponible';
                }}
              />
            </div>

            {/* Metadatos */}
            <div className="metadatos-container">
              <div className="metadatos-grid">
                <div className="metadato-item">
                  <FiCalendar className="metadato-label" />
                  <span className="metadato-label">Fecha de Publicación</span>
                  <span className="metadato-valor">
                    {new Date(noticia.fecha).toLocaleDateString("es-AR", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </div>
                
                <div className="metadato-item">
                  <FiTag className="metadato-label" />
                  <span className="metadato-label">Categoría</span>
                  <span className="metadato-valor">{noticia.categoria}</span>
                </div>
                
                <div className="metadato-item">
                  <FiGlobe className="metadato-label" />
                  <span className="metadato-label">Fuente</span>
                  <span className="metadato-valor">{noticia.fuente}</span>
                </div>
              </div>
            </div>

            {/* Contenido */}
            <div className="contenido-noticia">
              <p>{noticia.resumen}</p>
            </div>
          </div>
        </div>
        
        {/* Sidebar en el 20% derecho - Versión mejorada */}
        <div className="hidden md:block md:w-1/5 sidebar-right-container">
          <SidebarNoticia 
            fuente={noticia.fuente}
            categoria={noticia.categoria}
            noticiaActualId={noticia.id}
          />
        </div>
      </div>

      {/* Componente de Noticias Relacionadas - Ocupa 100% del ancho */}
      <NoticiasRelacionadas 
        categoriaActual={noticia.categoria} 
        noticiaActualId={noticia.id} 
      />

      {/* Botones de acción - Ocupan 100% del ancho con contenedor interno al 80% */}
      <div className="botones-accion-container">
        <div className="botones-accion">
          <a
            href={noticia.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            <FiExternalLink className="btn-icon" />
            Leer Noticia Original
          </a>
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary"
          >
            <FiArrowLeft className="btn-icon" />
            Volver al Inicio
          </button>
        </div>
      </div>
    </div>
  );
}

export default NoticiaDetalle;