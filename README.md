# Proyecto Noticias Resumidas - AntiHumo News

Un agregador de noticias argentinas y globales que usa IA para eliminar amarillismo y resumir al grano.

## 🌐 **Estado Actual: PRODUCCIÓN**

**Tu aplicación está 100% desplegada:**
- **Frontend**: Listo para Vercel
- **Backend**: Desplegado en Render (`https://proyecto-noticias-api.onrender.com`)
- **Base de datos**: Supabase configurada

## 🚀 **Instalación y Desarrollo**

### Backend (Ya en Producción)
```bash
cd backend

# Si necesitas desarrollo local:
python3 -m venv venv

# Activa el entorno:
source venv/bin/activate

pip install -r requirements.txt

# Configura .env con tus claves:
# SUPABASE_URL=tu_url
# SUPABASE_SERVICE_ROLE_KEY=tu_key  
# GNEWS_API_KEY=tu_key_gnews
# GEMINI_API_KEY=tu_key_gemini

# Ejecutar el crawler manualmente:
python procesar_y_guardar_db.py

# Iniciar servidor local:
python servidor_api.py
```

### Frontend (Listo para Producción)
```bash
cd frontend

npm install

# Configura .env con:
# VITE_API_URL=https://proyecto-noticias-api.onrender.com
# VITE_CLIMA_API_KEY=tu_key_clima
# VITE_NASA_API_KEY=tu_key_nasa
# VITE_GEO_API_KEY=tu_key_geo

# Desarrollo local:
npm run dev

# Build para producción:
npm run build
```

## 📁 **Estructura del Proyecto**

```
noticiasproyecto/
├── backend/
│   ├── servidor_api.py          # API Flask principal
│   ├── procesar_y_guardar_db.py # Crawler de noticias
│   ├── db.py                    # Conexión Supabase
│   └── requirements.txt         # Dependencias Python
├── frontend/
│   ├── src/components/          # Componentes React
│   ├── src/styles/              # Estilos CSS
│   ├── public/                  # Assets estáticos
│   └── package.json            # Dependencias Node
└── README.md
```

## 🔧 **Variables de Entorno Requeridas**

### Backend (.env)
```env
SUPABASE_URL=tu_url_supabase
SUPABASE_SERVICE_ROLE_KEY=tu_service_key
GNEWS_API_KEY=tu_gnews_key
GEMINI_API_KEY=tu_gemini_key
```

### Frontend (.env)
```env
VITE_API_URL=https://proyecto-noticias-api.onrender.com
VITE_CLIMA_API_KEY=tu_openweather_key
VITE_NASA_API_KEY=tu_nasa_key
VITE_GEO_API_KEY=tu_geo_key
```

## 🌟 **Características Principales**

- ✅ **Noticias en tiempo real** de múltiples fuentes
- ✅ **Resumen con IA** (Gemini) para eliminar amarillismo
- ✅ **Interfaz moderna** con Tailwind CSS y partículas
- ✅ **Clima global** y datos astronómicos (NASA)
- ✅ **Mercados financieros** en tiempo real
- ✅ **Datos deportivos** de fútbol
- ✅ **Totalmente responsive**

## 🚀 **Despliegue**

### Frontend en Vercel:
1. Conecta tu repositorio GitHub
2. Configura las variables de entorno en el dashboard
3. Deploy automático

### Backend en Render (✅ Ya desplegado):
- URL: `https://proyecto-noticias-api.onrender.com`
- Web Service con auto-deploy desde GitHub