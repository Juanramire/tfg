# Configurador de PCs con SPL y FlamaPy

Aplicación web para configurar PCs de forma inteligente, combinando un **Lineas de Productos SPL** (Software Product Lines) con razonamiento SAT a través de **FlamaPy** y generación de configuraciones asistida por IA (**Gemini**).

## App desplegada

**https://configurador-de-pc.onrender.com**

## Inicio rápido

### Con Docker Compose

```bash
# 1. Copiar y rellenar las variables de entorno
cp .env.example .env
# Editar .env: MONGO_URI, GEMINI_API_KEY, FRONTEND_URL

# 2. Levantar los servicios
docker compose up --build
```

- Frontend: http://localhost
- Backend API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs

### Desarrollo local

**Backend (Python 3.11+):**

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt
cp ../.env.example .env  # rellenar MONGO_URI y GEMINI_API_KEY
uvicorn main:app --reload
```

**Frontend (Node 18+):**

```bash
cd frontend
npm install
cp .env.example .env  # VITE_API_URL=http://localhost:8000
npm run dev
```

## Estructura del proyecto

```
tfg/
├── backend/                # API REST (FastAPI + FlamaPy)
│   ├── data/
│   │   ├── modelo.uvl      # Modelo de features (SPL)
│   │   └── catalogo.json   # Catálogo activo de productos
│   ├── models/             # Modelos Pydantic
│   ├── routes/             # Endpoints: /api/features, /api/productos, /api/configuracion
│   ├── services/           # FlamaPy, MongoDB, motor configurador, Gemini
│   └── tests/              # 55 tests (98% cobertura)
├── frontend/               # SPA (React + Vite)
│   └── src/
│       ├── pages/          # Landing, ConsultaIA, Configurador
│       ├── components/     # StepPerfil, StepComponente, StepResumen
│       ├── store/          # Estado global (Zustand)
│       └── services/       # api.js
├── docker-compose.yml
└── .env.example
```

## Tests

```bash
# Backend — suite completa (55 tests)
cd backend && pytest tests/

# Backend — con informe de cobertura
cd backend && pytest --cov=. --cov-report=term-missing

# Frontend — tests E2E con Playwright (15 tests)
cd frontend && npm run test:e2e
```
