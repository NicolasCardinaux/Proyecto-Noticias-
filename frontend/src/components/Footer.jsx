import React from "react";
import { Link, useNavigate } from "react-router-dom";
import '../styles/Footer.css';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { 
  faMapMarkerAlt, 
  faEnvelope, 
  faPhone,
  faUsers,
  faAddressBook,
  faFolder
} from "@fortawesome/free-solid-svg-icons";
import { 
  faInstagram, 
  faFacebook, 
  faXTwitter,
  faLinkedin,
  faYoutube,
  faTiktok
} from "@fortawesome/free-brands-svg-icons";
import ParticlesBackground from './ParticlesBackground';
import Icono from '../imagenes/Icono.png';

function Footer() {
  const navigate = useNavigate();

  const handleScrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSectionNavigate = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      const headerHeight = 80;
      const elementPosition = element.offsetTop - headerHeight;
      window.scrollTo({
        top: elementPosition,
        behavior: 'smooth'
      });
    } else {
      navigate('/');
      setTimeout(() => {
        const delayedElement = document.getElementById(sectionId);
        if (delayedElement) {
          const delayedPosition = delayedElement.offsetTop - headerHeight;
          window.scrollTo({
            top: delayedPosition,
            behavior: 'smooth'
          });
        }
      }, 300);
    }
  };

  // Función para Quiénes Somos
  const handleQuienesSomos = (e) => {
    e.preventDefault();
    navigate('/quienes-somos');
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
  };

  // FUNCIÓN CORREGIDA para Contacto
  const handleContacto = (e) => {
    e.preventDefault();
    navigate('/contacto');
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
  };

  const sections = [
    { id: 'noticias-populares', label: 'Noticias Populares' },
    { id: 'clima-actual', label: 'Clima Actual' },
    { id: 'ultimas-noticias', label: 'Últimas Noticias' },
    { id: 'mundo-futbol', label: 'Mundo Fútbol' },
    { id: 'noticias-interes', label: 'Noticias de Interés' },
    { id: 'mundo-inversion', label: 'Mundo Inversión' },
    { id: 'salud-ciencia', label: 'Salud y Ciencia' },
    { id: 'ventana-universo', label: 'Ventana al Universo' },
    { id: 'entretenimiento-deportes', label: 'Entretenimiento' },
    { id: 'frase-dia', label: 'Frase del Día' }
  ];

  const categorias = [
    { value: 'Negocios', label: 'Negocios' },
    { value: 'Entretenimiento', label: 'Entretenimiento' },
    { value: 'Salud', label: 'Salud' },
    { value: 'Ciencia', label: 'Ciencia' },
    { value: 'Deportes', label: 'Deportes' },
    { value: 'Tecnología', label: 'Tecnología' }
  ];

  const redesSociales = [
    { icon: faFacebook, url: 'https://facebook.com', color: '#1877F2', name: 'Facebook' },
    { icon: faXTwitter, url: 'https://x.com', color: '#000000', name: 'X (Twitter)' },
    { icon: faInstagram, url: 'https://instagram.com', color: '#E4405F', name: 'Instagram' },
    { icon: faLinkedin, url: 'https://linkedin.com', color: '#0077B5', name: 'LinkedIn' },
    { icon: faYoutube, url: 'https://youtube.com', color: '#FF0000', name: 'YouTube' },
    { icon: faTiktok, url: 'https://tiktok.com', color: '#000000', name: 'TikTok' }
  ];

  return (
    <footer className="footer relative overflow-hidden">
      <ParticlesBackground className="footer-particles" />
      <div className="footer__overlay"></div>
      <div className="footer__main relative z-10">
        <div className="footer__container">
          {/* Sección Logo y Descripción */}
          <div className="footer__section footer__brand-section">
            <div className="footer__brand">
              <div className="footer__logo-container">
                <img src={Icono} alt="Icono AntiHumo" className="footer__logo-icon" />
                <span className="footer__brand-name">AntiHumo News</span>
              </div>
              <p className="footer__description">
                Tu portal de noticias confiable. Ofrecemos información veraz y actualizada 
                sobre los temas más relevantes del momento.
              </p>
              <div className="footer__contact-info">
                <div className="footer__contact-item">
                  <FontAwesomeIcon icon={faMapMarkerAlt} className="footer__contact-icon" />
                  <span>Buenos Aires, Argentina</span>
                </div>
                <div className="footer__contact-item">
                  <FontAwesomeIcon icon={faEnvelope} className="footer__contact-icon" />
                  <span>contacto@antihumonews.com</span>
                </div>
                <div className="footer__contact-item">
                  <FontAwesomeIcon icon={faPhone} className="footer__contact-icon" />
                  <span>+54 11 1234-5678</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sección Navegación Rápida */}
          <div className="footer__section">
            <h3 className="footer__section-title">Navegación Rápida</h3>
            <div className="footer__quick-links">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => handleSectionNavigate(section.id)}
                  className="footer__quick-link"
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sección Categorías */}
          <div className="footer__section">
            <h3 className="footer__section-title">
              Categorías
            </h3>
            <div className="footer__categories">
              {categorias.map((categoria) => (
                <Link 
                  key={categoria.value} 
                  to={`/category/${categoria.value}`} 
                  className="footer__category-link"
                >
                  {categoria.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Sección Información */}
          <div className="footer__section">
            <h3 className="footer__section-title">Información</h3>
            <div className="footer__info-links">
              {/* Botón Quiénes Somos */}
              <button onClick={handleQuienesSomos} className="footer__info-link">
                <FontAwesomeIcon icon={faUsers} className="footer__info-icon" />
                <span>Quiénes Somos</span>
              </button>
              
              {/* BOTÓN CONTACTO CORREGIDO */}
              <button onClick={handleContacto} className="footer__info-link">
                <FontAwesomeIcon icon={faAddressBook} className="footer__info-icon" />
                <span>Contacto</span>
              </button>
              
              <div className="footer__info-description">
                <p>Conoce más sobre nuestra misión y visión como medio de comunicación.</p>
              </div>
            </div>
          </div>

          {/* Sección Redes Sociales */}
          <div className="footer__section footer__social-section">
            <h3 className="footer__section-title">Síguenos</h3>
            <div className="footer__social-grid">
              {redesSociales.map((red, index) => (
                <a
                  key={index}
                  href={red.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer__social-square"
                  style={{ '--social-color': red.color }}
                  title={red.name}
                >
                  <FontAwesomeIcon icon={red.icon} className="footer__social-icon" />
                </a>
              ))}
            </div>
            <div className="footer__social-text">
              <p>Síguenos en nuestras redes sociales para estar al día con las últimas noticias</p>
            </div>
          </div>
        </div>

        {/* Newsletter */}
        <div className="footer__newsletter-container">
          <div className="footer__newsletter">
            <div className="footer__newsletter-content">
              <div className="footer__newsletter-info">
                <h4 className="footer__newsletter-title">Newsletter</h4>
                <p className="footer__newsletter-text">Recibe las noticias más importantes en tu email</p>
              </div>
              <div className="footer__newsletter-form">
                <input 
                  type="email" 
                  placeholder="Tu correo electrónico" 
                  className="footer__newsletter-input"
                />
                <button className="footer__newsletter-button">Suscribirse</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Línea separadora */}
      <div className="footer__divider relative z-10"></div>

      {/* Footer inferior */}
      <div className="footer__bottom relative z-10">
        <div className="footer__bottom-container">
          <div className="footer__copyright">
            <p>&copy; 2025 AntiHumo News. Todos los derechos reservados.</p>
            <p>Proyecto desarrollado por Nicolás Cardinaux</p>
          </div>
          
          <div className="footer__legal-links">
            <Link to="/politica-privacidad" className="footer__legal-link">Política de Privacidad</Link>
            <Link to="/terminos-servicio" className="footer__legal-link">Términos de Servicio</Link>
            <Link to="/acerca-de" className="footer__legal-link">Acerca de</Link>
            <button onClick={handleScrollToTop} className="footer__back-to-top">
              Volver arriba ↑
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;