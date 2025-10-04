import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/CategoryFilter.css';


import negociosImg from '../imagenes/negocios.jpg';
import entretenimientoImg from '../imagenes/entretenimiento.jpg';
import saludImg from '../imagenes/salud.jpg';
import cienciaImg from '../imagenes/ciencia.jpg';
import deportesImg from '../imagenes/deportes.jpg';
import tecnologiaImg from '../imagenes/tecnologia.jpg';
import vertodoImg from '../imagenes/vertodo.jpg'; 

const CategoryFilter = () => {
  const navigate = useNavigate();


  const categories = [
    { value: 'Negocios', label: 'Negocios' },
    { value: 'Entretenimiento', label: 'Entretenimiento' },
    { value: 'Salud', label: 'Salud' },
    { value: 'Ciencia', label: 'Ciencia' },
    { value: 'Deportes', label: 'Deportes' },
    { value: 'Tecnología', label: 'Tecnología' },
  ];


  const categoryImages = {
    Negocios: negociosImg,
    Entretenimiento: entretenimientoImg,
    Salud: saludImg,
    Ciencia: cienciaImg,
    Deportes: deportesImg,
    Tecnología: tecnologiaImg,
    'Ver Todas': vertodoImg, 
  };


  const handleCategoryClick = (category) => {
    if (category === 'Ver Todas') {
      navigate('/all-news');
    } else {
      navigate(`/category/${encodeURIComponent(category)}`);
    }
  };

  return (
    <div className="category-filter-container">
      {categories.map((category) => (
        <div
          key={category.value}
          className="category-item"
          style={{ backgroundImage: `url(${categoryImages[category.value]})` }}
          onClick={() => handleCategoryClick(category.value)}
          role="button"
          tabIndex="0"
          aria-label={`Ir a la categoría ${category.label}`}
        >
          <div className="category-overlay">
            <span className="category-label">#{category.label}</span>
          </div>
        </div>
      ))}
      
      {}
      <div
        className="category-item ver-todas-item"
        style={{ backgroundImage: `url(${vertodoImg})` }}
        onClick={() => handleCategoryClick('Ver Todas')}
        role="button"
        tabIndex="0"
        aria-label="Ver todas las noticias"
      >
        <div className="category-overlay ver-todas-overlay">
          <span className="category-label ver-todas-label">Ver Todas</span>
        </div>
      </div>
    </div>
  );
};

export default CategoryFilter;