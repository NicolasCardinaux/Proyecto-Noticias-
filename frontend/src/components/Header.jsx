import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/header.css';
import Icono from '../imagenes/Icono.png';

function Header() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('');
  const navigate = useNavigate();

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

  const handleSearch = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
    }
  };

  const handleSearchClick = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
    }
  };

  const goToHome = () => {
    navigate('/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSectionNavigate = (sectionId) => {
    setActiveSection(sectionId);
    
    // Si ya estamos en el home, hacer scroll a la sección
    if (window.location.pathname === '/') {
      const element = document.getElementById(sectionId);
      if (element) {
        const headerHeight = 80;
        const elementPosition = element.offsetTop - headerHeight;
        window.scrollTo({
          top: elementPosition,
          behavior: 'smooth'
        });
      }
    } else {
      // Si no estamos en el home, redirigir al home y luego hacer scroll
      navigate('/');
      // Esperar a que la página cargue y luego hacer scroll
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          const headerHeight = 80;
          const elementPosition = element.offsetTop - headerHeight;
          window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
          });
        }
      }, 300);
    }
  };

  const handleSectionChange = (e) => {
    const sectionId = e.target.value;
    if (sectionId) {
      handleSectionNavigate(sectionId);
    }
  };

  return (
    <header className="header text-white p-4 shadow-lg fixed w-full z-50">
      <div className="container mx-auto flex items-center justify-between">
        {/* Logo + menú */}
        <div className="flex items-center space-x-8">
          {/* Contenedor para el icono y el texto del logo */}
          <div className="flex items-center logo-container">
            <img
              src={Icono}
              alt="Icono de la app"
              className="logo-icon mr-4"
              onClick={goToHome}
            />
            <h1
              className="text-3xl font-extrabold text-[#b3000c] text-3d cursor-pointer"
              onClick={goToHome}
            >
              AntiHumo News
            </h1>
          </div>
          
          {/* Navegación rápida */}
          <select
            value={activeSection}
            onChange={handleSectionChange}
            className="navigation-select p-3 rounded-full border appearance-none focus:outline-none focus:ring-2 focus:ring-[#b3000c]"
          >
            <option value="" className="bg-[#5c0006] text-white">
              Navegación rápida
            </option>
            {sections.map((section) => (
              <option
                key={section.id}
                value={section.id}
                className="bg-[#5c0006] text-white"
              >
                {section.label}
              </option>
            ))}
          </select>

          {/* Enlaces */}
          <a href="/contacto" className="text-lg font-extrabold">
            Contacto
          </a>
          <Link to="/quienes-somos" className="text-lg font-extrabold">
            Quiénes Somos
          </Link>
        </div>

        {/* Barra de búsqueda */}
        <div className="relative flex items-center">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearch}
            placeholder="Buscar noticias..."
            className="bg-[#2e0003] text-white p-3 rounded-full w-80 focus:outline-none focus:ring-2 focus:ring-[#b3000c] pl-12 border border-[#5c0006]"
          />
          <button
            onClick={handleSearchClick}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 bg-[#b3000c] text-white p-2 rounded-full hover:bg-[#8a0009] focus:outline-none focus:ring-2 focus:ring-[#b3000c]"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;