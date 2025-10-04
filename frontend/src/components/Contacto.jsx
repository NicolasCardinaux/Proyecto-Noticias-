import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ParticlesBackground from './ParticlesBackground';
import '../styles/contacto.css';

function Contacto() {
  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    tema: '',
    mensaje: '',
    archivo: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (name === 'archivo') {
      setFormData(prev => ({
        ...prev,
        archivo: files[0] || null
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simular envío del formulario
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitMessage('¡Mensaje enviado correctamente! Te contactaremos pronto.');
      setFormData({
        nombre: '',
        email: '',
        tema: '',
        mensaje: '',
        archivo: null
      });
      
      // Limpiar mensaje después de 5 segundos
      setTimeout(() => {
        setSubmitMessage('');
      }, 5000);
    }, 2000);
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div className="contacto-page">
      <ParticlesBackground />
      <div className="relative z-10 min-h-screen bg-transparent flex flex-col">
        <div className="contacto-container">
          {/* Header de la sección */}
          <div className="section-header">
            <h1 className="section-title">
              Contáctanos
            </h1>
            <p className="section-subtitle">
              ¿Tienes alguna pregunta, sugerencia o quieres colaborar con nosotros?
            </p>
            <div className="section-divider"></div>
          </div>

          <div className="contacto-content">
            {/* Información de contacto */}
            <div className="contacto-info">
              <h2 className="info-title">Información de Contacto</h2>
              
              <div className="info-item">
                <div className="info-icon">
                  <svg fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                  </svg>
                </div>
                <div className="info-text">
                  <h3>Email</h3>
                  <p>contacto@antihumonews.com</p>
                </div>
              </div>

              <div className="info-item">
                <div className="info-icon">
                  <svg fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                  </svg>
                </div>
                <div className="info-text">
                  <h3>Ubicación</h3>
                  <p>Buenos Aires, Argentina</p>
                </div>
              </div>

              <div className="info-item">
                <div className="info-icon">
                  <svg fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 15.5c-1.25 0-2.45-.2-3.57-.57-.35-.11-.74-.03-1.02.24l-2.2 2.2c-2.83-1.44-5.15-3.75-6.59-6.59l2.2-2.21c.28-.26.36-.65.25-1C8.7 6.45 8.5 5.25 8.5 4c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1 0 9.39 7.61 17 17 17 .55 0 1-.45 1-1v-3.5c0-.55-.45-1-1-1zM12 3v10l3-3h6V3h-9z"/>
                  </svg>
                </div>
                <div className="info-text">
                  <h3>Teléfono</h3>
                  <p>+54 11 1234-5678</p>
                </div>
              </div>

              <div className="info-hours">
                <h3>Horarios de Atención</h3>
                <p>Lunes a Viernes: 9:00 - 18:00</p>
                <p>Sábados: 10:00 - 14:00</p>
              </div>
            </div>

            {/* Formulario de contacto */}
            <div className="contacto-form-container">
              <form onSubmit={handleSubmit} className="contacto-form">
                <div className="form-group">
                  <label htmlFor="nombre" className="form-label">
                    Nombre Completo *
                  </label>
                  <input
                    type="text"
                    id="nombre"
                    name="nombre"
                    value={formData.nombre}
                    onChange={handleChange}
                    required
                    className="form-input"
                    placeholder="Ingresa tu nombre completo"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email" className="form-label">
                    Email *
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="form-input"
                    placeholder="tu@email.com"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="tema" className="form-label">
                    Tema *
                  </label>
                  <select
                    id="tema"
                    name="tema"
                    value={formData.tema}
                    onChange={handleChange}
                    required
                    className="form-select"
                  >
                    <option value="">Selecciona un tema</option>
                    <option value="consulta">Consulta General</option>
                    <option value="sugerencia">Sugerencia</option>
                    <option value="colaboracion">Colaboración</option>
                    <option value="publicidad">Publicidad</option>
                    <option value="reporte">Reportar Problema</option>
                    <option value="otros">Otros</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="mensaje" className="form-label">
                    Mensaje *
                  </label>
                  <textarea
                    id="mensaje"
                    name="mensaje"
                    value={formData.mensaje}
                    onChange={handleChange}
                    required
                    rows="6"
                    className="form-textarea"
                    placeholder="Escribe tu mensaje aquí..."
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="archivo" className="form-label">
                    Adjuntar Archivo (Opcional)
                  </label>
                  <input
                    type="file"
                    id="archivo"
                    name="archivo"
                    onChange={handleChange}
                    className="form-file"
                    accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"
                  />
                  <small className="file-hint">
                    Formatos aceptados: JPG, PNG, PDF, DOC (Máx. 5MB)
                  </small>
                </div>

                {submitMessage && (
                  <div className={`submit-message ${submitMessage.includes('correctamente') ? 'success' : 'error'}`}>
                    {submitMessage}
                  </div>
                )}

                <div className="form-actions">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="submit-btn"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="loading-spinner"></div>
                        Enviando...
                      </>
                    ) : (
                      'Enviar Mensaje'
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleBackToHome}
                    className="back-btn"
                  >
                    &larr; Volver al Inicio
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Contacto;