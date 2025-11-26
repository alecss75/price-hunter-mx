# Configuración del Botón "Actualizar Ahora"

Este botón dispara manualmente el workflow de GitHub Actions para actualizar todos los precios rastreados sin esperar al cron programado.

## Arquitectura Simplificada (Sin Backend)

El sistema funciona así:
1. **Frontend (Angular)** → Firebase Hosting + Firestore para datos
2. **GitHub Actions** → Scraping automático cada 4 horas + manual bajo demanda
3. **Botón "Actualizar Ahora"** → Dispara GitHub Actions directamente desde el navegador

### Ventajas:
✅ **100% gratis** - sin necesidad de tarjeta de crédito  
✅ **Simple** - solo Firebase + GitHub Actions  
✅ **6 actualizaciones diarias** automáticas (cada 4 horas)  
✅ **Actualización manual** cuando quieras con un click

### Trade-off:
⚠️ **GitHub token visible en el código JS** del frontend (aceptable para proyecto personal)

---

## Configuración

### 1. Crear un Personal Access Token (PAT) en GitHub

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
2. Click en **"Generate new token (classic)"**
3. Dale un nombre descriptivo: `price-hunter-workflow-trigger`
4. Selecciona el scope: **`repo`** (acceso completo al repositorio)
   - Marca la checkbox de `repo` (incluye todos los sub-permisos)
5. Click en **"Generate token"**
6. **¡COPIA EL TOKEN AHORA!** No podrás verlo de nuevo (ejemplo: `ghp_xxxxxxxxxxxx`)

### 2. Configurar el token en tu app

1. Abre `frontend/src/environments/environment.ts`
2. Reemplaza el valor vacío con tu token:
   ```typescript
   githubToken: 'ghp_tu_token_copiado_aqui',
   ```
3. **⚠️ IMPORTANTE:** Este archivo está en `.gitignore` para que NO se suba a GitHub

### 3. Deploy del frontend

```powershell
cd frontend
npm run build
npm run deploy
```

### 4. Probar el botón

1. Abre tu app en https://price-hunter-mx.web.app
2. Haz click en **"Actualizar Ahora"** (botón verde)
3. Deberías ver una alerta de confirmación
4. Ve a GitHub → Actions para ver el workflow ejecutándose

---

## Frecuencia de Actualización

### Automática (GitHub Actions cron):
El scraper corre **6 veces al día** automáticamente:
- 6:00 PM CDMX
- 10:00 PM CDMX
- 2:00 AM CDMX
- 6:00 AM CDMX
- 10:00 AM CDMX
- 2:00 PM CDMX

### Manual (Botón en la app):
Click en "Actualizar Ahora" cuando quieras forzar una actualización inmediata.

---

## Seguridad

⚠️ **El token estará visible** si alguien inspecciona el código JavaScript de tu app  

### Esto es aceptable porque:
- Es un proyecto personal (no público con usuarios desconocidos)
- El token solo permite disparar workflows de tu propio repo
- Puedes revocar el token en cualquier momento desde GitHub

### Si el token se expone:
1. Ve a GitHub → Settings → Developer settings → Personal access tokens
2. Encuentra tu token y click en **"Delete"**
3. Genera uno nuevo y actualiza `environment.ts`
4. Redeploy el frontend

---

## Troubleshooting

### "Token no configurado"
→ Verifica que agregaste el token en `frontend/src/environments/environment.ts`

### "Error 401" al disparar
→ Tu token es inválido o expiró. Genera uno nuevo en GitHub

### El workflow no aparece en Actions
→ Espera 1-2 minutos, GitHub puede tardar en procesarlo

### ¿Cómo sé si funcionó?
→ Ve a GitHub → tu repo → Actions → verás "Daily Price Scraper" ejecutándose
