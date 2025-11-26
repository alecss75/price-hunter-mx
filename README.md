# 🦈 Price Hunter MX

Sistema de comparación de precios en tiempo real para el mercado mexicano con arquitectura **100% serverless**.

## 🏗️ Arquitectura

- **Frontend:** Angular 20 en Firebase Hosting
- **Scraping:** GitHub Actions (cada 2 horas)
- **Base de datos:** Firestore
- **Autenticación:** Firebase Auth (Google Sign-In)

Sin servidores backend persistentes - todo está automatizado y escalable.

## 📂 Estructura del Proyecto

```
price-hunter-mx/
├── frontend/          # Aplicación Angular
│   ├── src/          # Componentes, servicios, modelos
│   ├── angular.json
│   └── tsconfig.json
├── backend/           # Scripts de scraping
│   ├── main.py       # API FastAPI (solo desarrollo local)
│   ├── run_scraper.py # Script para GitHub Actions
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── scraper.yml # Automatización cada 2 horas
└── package.json       # Dependencias del proyecto
```

## 🚀 Inicio Rápido

### Frontend (Angular)
```bash
npm install
npm run dev
```

### Backend Local (FastAPI - Opcional para desarrollo)
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python main.py
```

## 🤖 Automatización con GitHub Actions

El scraper se ejecuta automáticamente **cada 2 horas** (12 veces al día) usando GitHub Actions + Firestore.

### Configuración:
1. Crea un proyecto en Firebase
2. Descarga las credenciales (`ServiceAccountPriceHunterMx.json`)
3. En GitHub: Settings → Secrets → Actions → `FIREBASE_CREDENTIALS_JSON`
4. Pega el contenido del JSON en el secreto
5. Push al repositorio

## 🚢 Deploy

### Frontend (Firebase Hosting)
```bash
npm run build
npm run deploy
```

O simplemente:
```bash
npm run deploy
```

URL en producción: https://price-hunter-mx.web.app

## 🔑 Configuración Firebase

1. Crea proyecto en [Firebase Console](https://console.firebase.google.com)
2. Habilita:
   - **Authentication** → Google Sign-In
   - **Firestore Database** → Modo producción
   - **Hosting**
3. Copia las credenciales a `frontend/src/firebase.config.ts`
4. Configura Security Rules en Firestore:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Usuarios solo pueden leer/escribir sus propios datos
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Cache de precios - lectura pública, escritura solo para servidor
    match /cached_results/{document=**} {
      allow read: if true;
      allow write: if false;
    }
    
    // Opciones de comparación - lectura pública
    match /store_options/{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

## ✨ Funcionalidades

- ✅ Scraping automático de 4 tiendas mexicanas
- ✅ Comparación de precios en tiempo real
- ✅ Historial de precios
- ✅ Opciones de comparación (hasta 10 alternativas)
- ✅ Autenticación con Google
- ✅ Listas privadas por usuario
- ✅ Sincronización en tiempo real con Firestore
- ✅ Actualización automática cada 2 horas vía GitHub Actions

## 🛠️ Tecnologías

**Frontend:**
- Angular 20
- TailwindCSS
- Firebase JS SDK
- RxJS

**Backend/Scraping:**
- Python 3.10+
- FastAPI (dev only)
- Playwright
- Firebase Admin SDK

**Infraestructura:**
- Firebase Hosting
- Firestore
- GitHub Actions
