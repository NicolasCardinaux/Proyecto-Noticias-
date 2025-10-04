import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ParticlesBackground from './ParticlesBackground';
import '../styles/quienesSomos.css';

function QuienesSomos() {
  const navigate = useNavigate();
  const topRef = useRef(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleGoHome = () => {
    navigate('/');
  };

  const animateNumbers = () => {
    const counters = document.querySelectorAll('.stat-number');
    counters.forEach(counter => {
      const target = +counter.getAttribute('data-target');
      const increment = target / 100;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          clearInterval(timer);
          current = target;
        }
        counter.textContent = Math.floor(current) + (target === 24 ? '/7' : target === 0 ? '%' : '+');
      }, 20);
    });
  };

  useEffect(() => {
    animateNumbers();
  }, []);

  return (
    <div className="quienes-somos" ref={topRef}>
      <ParticlesBackground />
      <div className="relative z-10 min-h-screen bg-transparent flex flex-col">
        
        {}
        <div className="container mx-auto pt-24 px-4">
          <button 
            onClick={handleGoHome}
            className="back-home-btn mb-8 newspaper-btn"
          >
            Volver a Portada
          </button>
        </div>

        {}
        <div className="newspaper-container">
          
          {}
          <header className="newspaper-header">
            <div className="newspaper-masthead">
              <div className="masthead-decoration">
                <div className="decoration-left">✦</div>
                <div className="decoration-center">EDICIÓN ESPECIAL</div>
                <div className="decoration-right">✦</div>
              </div>
              
              <div className="newspaper-title">
                <h1 className="main-title">
                  <span className="title-part-1">AntiHumo</span>
                  <span className="title-part-2">News</span>
                </h1>
                <div className="title-underline"></div>
              </div>

              <div className="header-subtitle">
                <span className="subtitle-text">QUIÉNES SOMOS</span>
              </div>

              <div className="newspaper-metadata">
                <div className="metadata-item">
                  <strong>EDICIÓN:</strong> ESPECIAL
                </div>
                <div className="metadata-item">
                  <strong>PROPÓSITO:</strong> CLARIDAD INFORMATIVA
                </div>
                <div className="metadata-item">
                  <strong>ESLOGAN:</strong> INFORMACIÓN SIN HUMO
                </div>
              </div>
            </div>
            
            <div className="header-divider">
              <div className="divider-ornament">✦</div>
            </div>
          </header>

          {}
          <div className="newspaper-body">
            
            {}
            <div className="newspaper-column">
              {}
              <article className="news-article main-article breaking-news">
                <div className="article-badge">EXCLUSIVO</div>
                <h2 className="article-title">
                  Nuestra Misión Revolucionaria
                </h2>
                <div className="article-content">
                  <p className="lead-paragraph">
                    En <span className="highlight">AntiHumo News</span>, hemos declarado la guerra 
                    a la <span className="underline-single">desinformación digital</span>. 
                    Nuestra cruzada: eliminar el "humo" informativo que nubla la verdad.
                  </p>
                  
                  <div className="mission-statement">
                    <p>
                      <strong>Transformamos el caos informativo en claridad pura.</strong> 
                      Donde otros ven noticias, nosotros vemos oportunidades para 
                      <span className="text-emphasis"> iluminar mentes</span>.
                    </p>
                  </div>

                  <div className="feature-highlight">
                    <h4>INNOVACIÓN EN TRES PASOS CLAVE:</h4>
                    <div className="innovation-steps">
                      <div className="step">
                        <div className="step-number">1</div>
                        <div className="step-content">
                          <strong>Filtrado Inteligente Avanzado</strong>
                          <span>Tecnología IA que detecta y elimina contenido irrelevante automáticamente</span>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">2</div>
                        <div className="step-content">
                          <strong>Síntesis Precisa y Contextual</strong>
                          <span>Extraemos la esencia fundamental manteniendo el contexto original</span>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">3</div>
                        <div className="step-content">
                          <strong>Entrega Inmediata y Verificada</strong>
                          <span>Información clara y contrastada disponible en tiempo real</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </article>

              {}
              <article className="news-article process-article">
                <h2 className="article-title">
                  Proceso Editorial Riguroso
                </h2>
                <div className="article-content">
                  <p>
                    Cada noticia pasa por un <span className="highlight">proceso de verificación</span> de cuatro etapas que garantiza la máxima calidad y precisión informativa.
                  </p>
                  
                  <div className="process-stages">
                    <div className="process-stage">
                      <div className="stage-header">
                        <div className="stage-number">01</div>
                        <h5>Recopilación Multi-fuente</h5>
                      </div>
                      <p>Agregamos información de fuentes confiables y verificadas</p>
                    </div>
                    <div className="process-stage">
                      <div className="stage-header">
                        <div className="stage-number">02</div>
                        <h5>Análisis Contextual</h5>
                      </div>
                      <p>Evaluamos el contexto y relevancia de cada información</p>
                    </div>
                    <div className="process-stage">
                      <div className="stage-header">
                        <div className="stage-number">03</div>
                        <h5>Síntesis Inteligente</h5>
                      </div>
                      <p>Extraemos los puntos clave eliminando redundancias</p>
                    </div>
                    <div className="process-stage">
                      <div className="stage-header">
                        <div className="stage-number">04</div>
                        <h5>Verificación Final</h5>
                      </div>
                      <p>Revisión humana para garantizar calidad y precisión</p>
                    </div>
                  </div>
                </div>
              </article>

              {}
              <article className="news-article team-article">
                <div className="article-badge">EQUIPO</div>
                <h2 className="article-title">
                  Los Guardianes de la Verdad
                </h2>
                <div className="article-content">
                  <p>
                    Detrás de AntiHumo News hay un equipo multidisciplinario comprometido 
                    con la excelencia periodística y la innovación tecnológica.
                  </p>
                  
                  <div className="team-grid">
                    <div className="team-member">
                      <div className="member-icon">👨‍💻</div>
                      <div className="member-info">
                        <strong>Expertos en IA</strong>
                        <span>Desarrollan algoritmos de filtrado inteligente</span>
                      </div>
                    </div>
                    <div className="team-member">
                      <div className="member-icon">📝</div>
                      <div className="member-info">
                        <strong>Periodistas Senior</strong>
                        <span>Verifican y contextualizan cada información</span>
                      </div>
                    </div>
                    <div className="team-member">
                      <div className="member-icon">🔍</div>
                      <div className="member-info">
                        <strong>Analistas de Datos</strong>
                        <span>Monitorean tendencias y patrones informativos</span>
                      </div>
                    </div>
                  </div>
                </div>
              </article>
            </div>

            {}
            <div className="newspaper-column">
              {}
              <article className="news-article featured-article difference-article">
                <div className="article-badge">INNOVACIÓN</div>
                <h2 className="article-title">
                  La Revolución AntiHumo
                </h2>
                <div className="article-content">
                  <div className="difference-grid">
                    <div className="difference-card">
                      <h4>PRECISIÓN QUIRÚRGICA</h4>
                      <p>Cada palabra es cuidadosamente seleccionada para máximo impacto informativo sin redundancias innecesarias</p>
                    </div>
                    <div className="difference-card">
                      <h4>VELOCIDAD EXTREMA</h4>
                      <p>Procesamos información más rápido que la velocidad de propagación de la desinformación en redes sociales</p>
                    </div>
                    <div className="difference-card">
                      <h4>TRANSPARENCIA TOTAL</h4>
                      <p>Mostramos nuestro proceso completo sin magia negra, solo tecnología transparente y verificable</p>
                    </div>
                    <div className="difference-card">
                      <h4>PROTECCIÓN AL USUARIO</h4>
                      <p>Tu tiempo y atención son nuestro bien más preciado y protegido contra el ruido digital</p>
                    </div>
                  </div>
                </div>
              </article>

              {}
              <article className="news-article quote-article philosophy-article">
                <blockquote className="newspaper-quote">
                  "En un mundo saturado de información vacía, el verdadero lujo 
                  no es tener más contenido, sino tener <span className="quote-highlight">menos pero mejor</span>. 
                  La claridad es el nuevo oro digital en la era de la sobreinformación."
                </blockquote>
                <div className="quote-author">
                  <div className="author-info">
                    <strong>Filosofía AntiHumo</strong>
                    <span>Manifiesto por la Claridad Digital</span>
                  </div>
                </div>
              </article>

              {}
              <div className="stats-box enhanced-stats">
                <h3 className="stats-title">
                  IMPACTO EN CIFRAS
                </h3>
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-number" data-target="150">0+</div>
                    <div className="stat-label">Fuentes analizadas diariamente</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number" data-target="24">0</div>
                    <div className="stat-label">Actualización continua</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number" data-target="0">0%</div>
                    <div className="stat-label">Contenido innecesario</div>
                  </div>
                </div>
              </div>

              {}
              <article className="news-article tech-article">
                <div className="article-badge">TECNOLOGÍA</div>
                <h2 className="article-title">
                  Herramientas de Vanguardia
                </h2>
                <div className="article-content">
                  <p>
                    Utilizamos tecnología de punta para garantizar la máxima calidad 
                    y velocidad en nuestro proceso informativo.
                  </p>
                  
                  <div className="tech-features">
                    <div className="tech-feature">
                      <span className="tech-icon">🤖</span>
                      <span>Algoritmos de IA propietarios</span>
                    </div>
                    <div className="tech-feature">
                      <span className="tech-icon">⚡</span>
                      <span>Procesamiento en tiempo real</span>
                    </div>
                    <div className="tech-feature">
                      <span className="tech-icon">🛡️</span>
                      <span>Sistemas de verificación múltiple</span>
                    </div>
                  </div>
                </div>
              </article>
            </div>

            {}
            <div className="newspaper-column">
              {}
              <article className="news-article values-article corporate-article">
                <h2 className="article-title">
                  Nuestro ADN Corporativo
                </h2>
                <div className="article-content">
                  <div className="values-showcase">
                    <div className="value-showcase-item">
                      <h4>TRANSPARENCIA RADICAL</h4>
                      <p>Mostramos cada paso de nuestro proceso sin secretos. Creemos en la verdad verificable como fundamento.</p>
                    </div>
                    <div className="value-showcase-item">
                      <h4>PRECISIÓN ABSOLUTA</h4>
                      <p>Cada dato verificado, cada palabra justificada. Cero aproximaciones o suposiciones en nuestro contenido.</p>
                    </div>
                    <div className="value-showcase-item">
                      <h4>EFICIENCIA EXTREMA</h4>
                      <p>Respetamos tu tiempo como el recurso más valioso. Información directa sin rodeos innecesarios.</p>
                    </div>
                    <div className="value-showcase-item">
                      <h4>EQUILIBRIO PERFECTO</h4>
                      <p>Múltiples perspectivas, una sola verdad: la información completa y contextualizada siempre.</p>
                    </div>
                  </div>
                </div>
              </article>

              {}
              <article className="news-article final-article commitment-article">
                <div className="article-badge">COMPROMISO</div>
                <h2 className="article-title">
                  Pacto con Nuestros Lectores
                </h2>
                <div className="article-content">
                  <div className="commitment-list">
                    <div className="commitment-item">
                      <span className="commitment-check">✓</span>
                      <span><strong>Nunca</strong> priorizaremos clicks sobre claridad informativa</span>
                    </div>
                    <div className="commitment-item">
                      <span className="commitment-check">✓</span>
                      <span><strong>Siempre</strong> mostraremos fuentes y metodología de verificación</span>
                    </div>
                    <div className="commitment-item">
                      <span className="commitment-check">✓</span>
                      <span><strong>Garantizamos</strong> cero contenido sensacionalista o engañoso</span>
                    </div>
                    <div className="commitment-item">
                      <span className="commitment-check">✓</span>
                      <span><strong>Protegemos</strong> tu atención como tesoro sagrado</span>
                    </div>
                  </div>

                  <div className="final-message">
                    <p>
                      <strong>No somos solo una plataforma de noticias.</strong> 
                      Somos un <span className="text-emphasis">movimiento por la claridad informativa</span>, 
                      una revolución silenciosa contra la saturación digital que contamina el debate público.
                    </p>
                  </div>

                  <div className="signature enhanced-signature">
                    <div className="signature-line"></div>
                    <div className="signature-text">
                      <span className="signature-main">EL EQUIPO DE ANTIHUMO NEWS</span>
                      <span className="signature-sub">Comprometidos con la Verdad</span>
                    </div>
                  </div>
                </div>
              </article>

              {}
              <div className="cta-box enhanced-cta">
                <h3>¿LISTO PARA EXPERIMENTAR LA DIFERENCIA?</h3>
                <p>Descubre la información sin ruido y sin humo</p>
                <button 
                  onClick={handleGoHome}
                  className="cta-button newspaper-btn enhanced-cta-button"
                >
                  <span className="cta-text">Explorar Noticias Claras</span>
                  <span className="cta-arrow">→</span>
                </button>
                <div className="cta-guarantee">
                  <span className="guarantee-icon">⭐</span>
                  <span>Garantía de calidad 100% verificada</span>
                </div>
              </div>

              {}
              <article className="news-article testimonials-article">
                <div className="article-badge">TESTIMONIOS</div>
                <h2 className="article-title">
                  Lo Que Dicen Nuestros Lectores
                </h2>
                <div className="article-content">
                  <div className="testimonials">
                    <div className="testimonial">
                      <p>"Finalmente una plataforma que respeta mi tiempo y mi inteligencia."</p>
                      <span className="testimonial-author">- Carlos M., Suscriptor</span>
                    </div>
                    <div className="testimonial">
                      <p>"La claridad de la información me ha ayudado a tomar mejores decisiones."</p>
                      <span className="testimonial-author">- Ana L., Lectora Frecuente</span>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>

          {}
          <footer className="newspaper-footer">
            <div className="footer-divider">
              <div className="footer-ornament">🞻🞻🞻</div>
            </div>
            <div className="footer-info">
              <div className="footer-section">
                <strong>AntiHumo News</strong>
                <span>Información Clara Sin Humo</span>
              </div>
              <div className="footer-section">
                <strong>Edición Digital</strong>
                <span>Comprometidos con la Verdad</span>
              </div>
              <div className="footer-section">
                <strong>100% Verificado</strong>
                <span>Libre de Desinformación</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default QuienesSomos;