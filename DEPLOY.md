# Pasos para deploy completo en Firebase (Hosting + Cloud Run)

## 🔧 Pre-requisitos
1. Tener una cuenta de Google Cloud con facturación habilitada (para Cloud Run)
2. `firebase-tools` instalado: `npm install -g firebase-tools`
3. `gcloud` CLI instalado: https://cloud.google.com/sdk/docs/install

## 🏗️ Setup Inicial

### 1. Firebase Login
```powershell
firebase login
```

### 2. Configurar Proyecto
Edita `.firebaserc` y reemplaza `YOUR_PROJECT_ID` con tu ID real de Firebase.

### 3. Habilitar APIs en Google Cloud
```powershell
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## 🚀 Deploy Frontend (Firebase Hosting)

```powershell
# Build Angular app
npm run build

# Deploy a Firebase Hosting
firebase deploy --only hosting
```

Tu app estará en: `https://YOUR_PROJECT_ID.web.app`

## 🐳 Deploy Backend (Cloud Run)

```powershell
cd backend

# Deploy usando Dockerfile (Cloud Build automático)
gcloud run deploy price-hunter-backend `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --platform managed `
  --memory 1Gi `
  --timeout 300
```

Anota la URL que te devuelva (ej: `https://price-hunter-backend-xxx-uc.a.run.app`).

## 🔗 Conectar Frontend con Backend

Edita `frontend/src/services/product.service.ts` y reemplaza:
```typescript
const url = `http://localhost:8000/...`
```
por:
```typescript
const url = `https://price-hunter-backend-xxx-uc.a.run.app/...`
```

Luego re-deploya el frontend:
```powershell
npm run deploy
```

## 🔐 Deploy Firestore Rules

```powershell
firebase deploy --only firestore:rules
```

## 🔄 GitHub Actions (Scraper Automático)

Ya configurado en `.github/workflows/scraper.yml`. Solo asegúrate de:
1. Tener el secreto `FIREBASE_CREDENTIALS_JSON` en GitHub.
2. El workflow corre 2x/día y actualiza precios en Firestore.

## 📊 Monitoreo

- **Logs del backend**: Cloud Console → Cloud Run → Logs
- **Firestore data**: Firebase Console → Firestore Database
- **Frontend analytics**: Firebase Console → Analytics (si lo habilitas)

## 💰 Costos Estimados (Uso personal)

- **Firebase Hosting**: Gratis (hasta 10 GB/mes)
- **Firestore**: Gratis (50k lecturas/día)
- **Cloud Run**: ~$0-5/mes (con sleep automático entre requests)
- **GitHub Actions**: Gratis (2000 min/mes)

**Total**: ~$0-5/mes para uso personal.
