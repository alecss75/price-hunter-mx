# 🚀 Deploy Backend en Render.com (Gratis)

## Pasos:

### 1. Crear cuenta
- Ve a https://render.com
- Signup con tu cuenta de GitHub

### 2. Nuevo Web Service
- Click **New +** → **Web Service**
- Conecta tu repositorio `price-hunter-mx`

### 3. Configuración del servicio:
```
Name: price-hunter-backend
Region: Oregon (US West)
Branch: main
Root Directory: backend
Runtime: Python 3
```

### 4. Build & Start Commands:
```
Build Command:
pip install -r requirements.txt && playwright install chromium

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 5. Plan:
- Selecciona **Free** (Auto-sleep después de 15 min sin uso)

### 6. Environment Variables:
Click **Environment** y agrega:
```
Key: FIREBASE_CREDENTIALS_JSON
Value: (pega el contenido completo de ServiceAccountPriceHunterMx.json)
```

### 7. Deploy:
- Click **Create Web Service**
- Espera ~5-10 min (primera vez instala Playwright)
- Anota la URL: `https://price-hunter-backend-xxxx.onrender.com`

### 8. Actualizar Frontend:
Edita `frontend/src/environments/environment.ts`:
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://price-hunter-backend-xxxx.onrender.com'
};
```

### 9. Re-deploy frontend:
```powershell
npm run deploy
```

## ✅ Listo
- Frontend: https://price-hunter-mx.web.app
- Backend: https://price-hunter-backend-xxxx.onrender.com
- Actions: Scraping automático 2x/día

## 💡 Nota sobre Free Tier
- Backend "duerme" después de 15 min sin requests
- Primera request después del sleep tarda ~30s (cold start)
- Requests subsecuentes son rápidas (~2-5s)
