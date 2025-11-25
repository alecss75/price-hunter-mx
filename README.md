<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# 🦈 Price Hunter MX

Sistema de comparación de precios en tiempo real para el mercado mexicano.

## 📂 Estructura del Proyecto

```
price-hunter-mx/
├── frontend/          # Aplicación Angular
│   ├── src/          # Componentes, servicios, modelos
│   ├── angular.json
│   └── tsconfig.json
├── backend/           # API FastAPI + Scraper
│   ├── main.py       # API REST con streaming
│   ├── run_scraper.py # Script para GitHub Actions
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── scraper.yml # Automatización diaria
└── package.json       # Dependencias del proyecto
```

## 🚀 Inicio Rápido

### Frontend (Angular)
```bash
npm install
npm run dev
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
playwright install
python main.py
```

## 🤖 Automatización con GitHub Actions

El scraper se ejecuta automáticamente 2 veces al día (8 AM y 8 PM CDMX) usando GitHub Actions + Firestore.

### Configuración:
1. Crea un proyecto en Firebase
2. Descarga las credenciales (`ServiceAccountPriceHunterMx.json`)
3. En GitHub: Settings → Secrets → Actions → `FIREBASE_CREDENTIALS_JSON`
4. Pega el contenido del JSON en el secreto
5. Push al repositorio

## 🚢 Deploy en Firebase (Hosting + Cloud Run)

### 1️⃣ Setup Inicial
```bash
npm install -g firebase-tools
firebase login
```

### 2️⃣ Configurar Proyecto
Edita `.firebaserc` y reemplaza `YOUR_PROJECT_ID` con tu ID de Firebase.

### 3️⃣ Deploy Frontend
```bash
npm run build
firebase deploy --only hosting
```

### 4️⃣ Deploy Backend (Cloud Run)
```bash
cd backend
gcloud run deploy price-hunter-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_CREDENTIALS_JSON=""
```

Luego actualiza `frontend/src/services/product.service.ts` con la URL de Cloud Run.

### 5️⃣ Variables de Entorno Cloud Run
En Cloud Console → Cloud Run → tu servicio → Variables:
- `FIREBASE_CREDENTIALS_JSON`: (déjalo vacío, Cloud Run usa credenciales implícitas)

## 🔑 Variables de Entorno (Local)

Crea `.env.local` con:
```
GEMINI_API_KEY=tu_api_key_aqui
```

Firebase config: `frontend/src/firebase.config.ts` (ya configurado si llenaste tus credenciales)
