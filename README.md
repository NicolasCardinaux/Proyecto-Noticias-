# Proyecto Noticias Resumidas

Un agregador de noticias argentinas y globales que usa IA para eliminar amarillismo y resumir al grano.

## Instalación

### Backend
1. `cd backend`
2. `python -m venv venv`
3. Activa: `venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Unix)
4. `pip install -r requirements.txt`
5. Configura .env en la raíz
6. Genera datos: `python procesar_noticias.py`
7. Inicia: `uvicorn app:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. Instala Tailwind: `npm install -D tailwindcss postcss autoprefixer` y `npx tailwindcss init -p`
4. `npm run dev`

Accede a http://localhost:5173