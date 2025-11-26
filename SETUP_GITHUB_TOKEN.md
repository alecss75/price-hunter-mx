# Configuración del Botón "Actualizar Ahora"

Este botón dispara manualmente el workflow de GitHub Actions para actualizar todos los precios rastreados sin esperar al cron programado.

## Arquitectura Segura

El botón funciona de la siguiente manera:
1. **Usuario hace clic** → Frontend obtiene el Firebase Auth token del usuario actual
2. **Frontend → Backend** → Envía petición a `/trigger-scraper` con el token de Firebase
3. **Backend valida** → Verifica que el token sea válido con Firebase Admin SDK
4. **Backend → GitHub** → Dispara el workflow usando el GitHub token almacenado de forma segura
5. **GitHub Actions** → Ejecuta el scraper y actualiza Firestore

### Ventajas de esta arquitectura:
✅ **GitHub token nunca llega al navegador** (100% seguro)  
✅ **Solo usuarios autenticados** pueden disparar el workflow  
✅ **Sin configuración en el frontend** - todo funciona de inmediato  
✅ **Funciona desde cualquier dispositivo** (celular, tablet, etc.)

## Configuración del Backend (Render)

### 1. Crear un Personal Access Token (PAT) en GitHub

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
2. Click en **"Generate new token (classic)"**
3. Dale un nombre descriptivo: `price-hunter-workflow-trigger`
4. Selecciona el scope: **`repo`** (acceso completo al repositorio)
   - Marca la checkbox de `repo` (esto incluye todos los sub-permisos necesarios)
5. Click en **"Generate token"**
6. **¡COPIA EL TOKEN AHORA!** No podrás verlo de nuevo.

### 2. Configurar variables de entorno en Render

1. Ve a tu servicio en Render.com
2. Click en **"Environment"** en el menú izquierdo
3. Agrega las siguientes variables:
   - **Key:** `GITHUB_TOKEN`  
     **Value:** `ghp_tu_token_copiado_aqui`
   - **Key:** `GITHUB_REPO`  
     **Value:** `alecss75/price-hunter-mx`
4. Click en **"Save Changes"**
5. Render redesplegará automáticamente

### 3. Probar el botón

1. Haz deploy del frontend actualizado:
   ```powershell
   cd frontend
   npm run build
   npm run deploy
   ```

2. En la app desplegada:
   - **Inicia sesión con Google** (requerido)
   - Haz click en **"Actualizar Ahora"** (botón verde)
   - Deberías ver una alerta de confirmación
3. Ve a GitHub → Actions para ver el workflow ejecutándose

## Seguridad

✅ **GitHub token está seguro** en variables de entorno de Render  
✅ **Solo usuarios autenticados** pueden disparar el workflow  
✅ **Token de Firebase se valida** en cada petición  
✅ **Sin secretos en el código fuente** del frontend

## Troubleshooting

### "Usuario no autenticado"
→ Necesitas iniciar sesión con Google antes de usar el botón

### "GitHub token no configurado en el servidor"
→ Verifica que agregaste `GITHUB_TOKEN` en las variables de entorno de Render

### "Token inválido o expirado"
→ Tu sesión de Firebase expiró, cierra sesión y vuelve a entrar
