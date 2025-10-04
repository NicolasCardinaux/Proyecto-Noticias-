/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#121212',     // Negro mate para fondo principal
        'dark-card': '#1a1a1a',   // Gris muy oscuro para tarjetas e inputs
        'dark-border': '#2a2a2a', // Borde tenue
        'text-primary': '#f5f5f5', // Blanco suave para texto principal
        'text-secondary': '#d1d5db', // Gris claro para texto secundario
        'accent': '#3b82f6',       // Azul para botones/enlaces
      },
    },
  },
  plugins: [],
}
