import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import NoticiasList from './components/NoticiasList';
import NoticiaDetalle from './components/NoticiaDetalle';
import QuienesSomos from './components/QuienesSomos';
import AllNews from './components/AllNews';
import Contacto from './components/Contacto'; // Asegúrate de importar el componente
import './index.css';

function App() {
  return (
    <Router>
      <div className="App bg-[#0a192f] min-h-screen flex flex-col">
        <Header />
        <main className="flex-grow pt-20">
          <Routes>
            <Route path="/" element={<NoticiasList />} />
            <Route path="/category/:category" element={<NoticiasList />} />
            <Route path="/noticia/:id" element={<NoticiaDetalle />} />
            <Route path="/search" element={<NoticiasList />} />
            <Route path="/quienes-somos" element={<QuienesSomos />} />
            <Route path="/all-news" element={<AllNews />} />
            <Route path="/contacto" element={<Contacto />} /> {/* Ruta de contacto */}
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;