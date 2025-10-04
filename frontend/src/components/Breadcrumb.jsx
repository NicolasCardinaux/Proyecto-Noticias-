import React from "react";
import { useNavigate } from "react-router-dom";
import "../styles/breadcrumb.css";

const Breadcrumb = ({ categoria, titulo }) => {
  const navigate = useNavigate();

  const handleHomeClick = () => {
    navigate("/");
  };

  const handleCategoriaClick = () => {
    // Navega directamente a la categoría usando tu ruta existente
    navigate(`/category/${encodeURIComponent(categoria)}`);
  };

  return (
    <div className="breadcrumb-wrapper">
      <nav className="breadcrumb">
        <span className="crumb" onClick={handleHomeClick}>
          Home
        </span>
        <span className="separator">›</span>
        <span className="crumb" onClick={handleCategoriaClick}>
          {categoria}
        </span>
        <span className="separator">›</span>
        <span className="crumb active">{titulo}</span>
      </nav>
    </div>
  );
};

export default Breadcrumb;