import React, { useState } from 'react';

const SafeImage = ({ 
  src, 
  alt, 
  className = "",
  ...props 
}) => {
  const [hasError, setHasError] = useState(false);


  const getFallbackImage = () => {
    return `data:image/svg+xml;base64,${btoa(`
      <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#1f2937"/>
        <text x="50%" y="45%" font-family="Arial, sans-serif" font-size="16" 
              fill="#9ca3af" text-anchor="middle" font-weight="bold">📰 AntiHumo News</text>
        <text x="50%" y="60%" font-family="Arial, sans-serif" font-size="12" 
              fill="#6b7280" text-anchor="middle">Imagen no disponible</text>
      </svg>
    `)}`;
  };


  const getProxiedImageUrl = (url) => {
    if (!url) return getFallbackImage();
    

    if (url.includes('data:image/svg+xml')) return url;
    

    let secureUrl = url;
    if (url.startsWith('http://')) {
      secureUrl = url.replace('http://', 'https://');
    }
    
    try {

      const encodedUrl = encodeURIComponent(secureUrl);
      return `https://images.weserv.nl/?url=${encodedUrl}&w=800&h=400&fit=cover&output=webp&q=80`;
    } catch (error) {
      return getFallbackImage();
    }
  };


  const handleError = () => {
    if (!hasError) {
      setHasError(true); 
    }
  };


  const urlToRender = hasError ? getFallbackImage() : getProxiedImageUrl(src);

  return (
    <img
      src={urlToRender}
      alt={alt || "Imagen de noticia"}
      className={`object-cover ${className}`}
      onError={handleError}
      loading="lazy"
      {...props}
    />
  );
};

export default SafeImage;