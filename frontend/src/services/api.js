import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // URL de tu backend FastAPI
  timeout: 10000, // Timeout de 10 segundos
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;