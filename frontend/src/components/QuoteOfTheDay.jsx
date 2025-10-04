import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/QuoteOfTheDay.css";

// URL base de la API
const API_BASE_URL = import.meta.env.VITE_API_URL;

function QuoteOfTheDay() {
  const [frase, setFrase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuote = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/frase-del-dia`);
        setFrase(response.data);
      } catch (err) {
        console.error(err);
        setError("No se pudo cargar la frase del día.");
      } finally {
        setLoading(false);
      }
    };

    fetchQuote();
  }, []);

  if (loading) {
    return (
      <div className="quote-section">
        <div className="quote-container-loading">
          <div className="quote-title-container">
            <h2 className="quote-section-title">Frase del Día</h2>
            <div className="title-underline"></div>
          </div>
          <div className="loading-text">Cargando frase del día...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quote-section">
        <div className="quote-container-error">
          <div className="quote-title-container">
            <h2 className="quote-section-title">Frase del Día</h2>
            <div className="title-underline"></div>
          </div>
          <div className="error-text">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="quote-section">
      <div className="quote-container">
        <div className="quote-title-container">
          <h2 className="quote-section-title">Frase del Día</h2>
          <div className="title-underline"></div>
        </div>
        
        <blockquote className="quote-blockquote">
          <div className="quote-text-container">
            <p className="quote-text">"{frase?.texto}"</p>
          </div>
          <footer className="quote-author">— {frase?.autor}</footer>
        </blockquote>
        
        <div className="quote-decoration">
          <div className="decoration-circle circle-1"></div>
          <div className="decoration-circle circle-2"></div>
          <div className="decoration-circle circle-3"></div>
        </div>
      </div>
    </div>
  );
}

export default QuoteOfTheDay;