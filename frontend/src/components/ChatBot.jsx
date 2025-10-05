import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import '../styles/ChatBot.css';

const API_BASE_URL = import.meta.env.VITE_API_URL;

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [rateLimitInfo, setRateLimitInfo] = useState(null);
  const [showWelcomePopup, setShowWelcomePopup] = useState(false);
  const messagesEndRef = useRef(null);
  const location = useLocation();


  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcomePopup(true);
      
      const hideTimer = setTimeout(() => {
        setShowWelcomePopup(false);
      }, 5000);
      
      return () => clearTimeout(hideTimer);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);


  const getCurrentNoticiaId = () => {
    if (location.pathname.startsWith('/noticia/')) {
      const match = location.pathname.match(/\/noticia\/(\d+)/);
      return match ? parseInt(match[1]) : null;
    }
    return null;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const noticiaId = getCurrentNoticiaId();
      const welcomeMessage = noticiaId 
        ? "¡Hola! 🤖 Soy AntiBot, tu asistente de AntiHumo News. Puedo responder preguntas sobre **esta noticia específica** usando la información del resumen. ¿En qué puedo ayudarte? 📰"
        : "¡Hola! 🤖 Soy AntiBot, tu asistente de AntiHumo News. Puedo ayudarte a navegar por el sitio y encontrar información veraz sobre noticias. ¿En qué puedo asistirte? 🌐";
      
      setMessages([{
        id: 1,
        text: welcomeMessage,
        sender: 'bot',
        timestamp: new Date(),
        contextType: noticiaId ? 'noticia' : 'general'
      }]);
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const noticiaId = getCurrentNoticiaId();
      
      console.log(`📤 Enviando pregunta: "${inputMessage}" - Noticia ID: ${noticiaId}`);
      
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        pregunta: inputMessage,
        noticia_id: noticiaId
      });

      console.log('📥 Respuesta recibida:', response.data);

      if (response.data.rate_limit_info) {
        setRateLimitInfo(response.data.rate_limit_info);
      }

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.respuesta,
        sender: 'bot',
        timestamp: new Date(),
        contextType: response.data.tipo_contexto,
        noticiaId: response.data.noticia_id,
        success: response.data.exito,
        rateLimitInfo: response.data.rate_limit_info
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('❌ Error enviando mensaje:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: '❌ Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente en unos momentos. 🔄',
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setRateLimitInfo(null);
  };

  const getContextBadge = () => {
    const noticiaId = getCurrentNoticiaId();
    if (noticiaId) {
      return '📰 Modo Noticia';
    }
    return '🌐 Modo General';
  };

  return (
    <div className="chatbot-container">
      {}
      {showWelcomePopup && !isOpen && (
        <div className="welcome-popup">
          <div className="welcome-message">
            <span className="welcome-icon">🤖</span>
            <span className="welcome-text">
              ¡Hola! Estoy aquí para ayudarte en lo que necesites sobre noticias
            </span>
          </div>
        </div>
      )}

      {}
      {!isOpen && (
        <button 
          className="chatbot-toggle-btn"
          onClick={() => setIsOpen(true)}
          title="Abrir chat de ayuda AntiBot"
        >
          <span className="chat-icon">🤖</span>
          <span className="pulse-dot"></span>
        </button>
      )}

      {}
      {isOpen && (
        <div className="chatbot-window">
          {}
          <div className="chatbot-header">
            <div className="chatbot-title">
              <span className="bot-avatar">🤖</span>
              <div className="title-content">
                <h3>AntiBot Assistant</h3>
                <span className="context-badge">
                  {getContextBadge()}
                  {rateLimitInfo && ` | ${rateLimitInfo.contador_actual}/${rateLimitInfo.limite}`}
                </span>
              </div>
            </div>
            <div className="chatbot-actions">
              <button 
                onClick={clearChat} 
                title="Limpiar conversación"
                className="action-btn"
              >
                🗑️
              </button>
              <button 
                onClick={() => setIsOpen(false)} 
                title="Cerrar chat"
                className="action-btn close-btn"
              >
                ✕
              </button>
            </div>
          </div>

          {}
          <div className="chatbot-messages">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.sender} ${message.isError ? 'error' : ''}`}
              >
                <div className="message-content">
                  {message.text}
                  {message.contextType === 'noticia' && !message.isError && (
                    <div className="context-indicator">
                      📍 Respondiendo basado en la noticia actual
                    </div>
                  )}
                  {message.contextType === 'general' && !message.isError && (
                    <div className="context-indicator general">
                      🌐 Respondiendo en modo general
                    </div>
                  )}
                  {message.rateLimitInfo && !message.isError && (
                    <div className="rate-limit-indicator">
                      📊 Preguntas hoy: {message.rateLimitInfo.contador_actual}/{message.rateLimitInfo.limite}
                    </div>
                  )}
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString('es-ES', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message bot">
                <div className="message-content loading">
                  <div className="typing-indicator">
                    <span>AntiBot está pensando</span>
                    <div className="typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {}
          <div className="chatbot-input-container">
            <div className="input-wrapper">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  getCurrentNoticiaId() 
                    ? "Pregunta sobre esta noticia específica..." 
                    : "Escribe tu pregunta sobre noticias en AntiHumo News..."
                }
                disabled={isLoading}
                rows="1"
                maxLength="500"
              />
              <button 
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className={`send-btn ${isLoading ? 'loading' : ''}`}
                title="Enviar mensaje"
              >
                {isLoading ? '⏳' : '🚀'}
              </button>
            </div>
            <div className="input-hint">
              {getCurrentNoticiaId() 
                ? "💡 Pregunta sobre el contenido de esta noticia" 
                : "💡 Pregunta sobre noticias, categorías o navegación del sitio"
              }
              {rateLimitInfo && (
                <div className="rate-limit-hint">
                  📊 {rateLimitInfo.preguntas_restantes} preguntas restantes hoy
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBot;