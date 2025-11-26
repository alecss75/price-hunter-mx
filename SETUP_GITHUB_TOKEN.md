# Configuración del Botón "Actualizar Ahora"

Este botón dispara manualmente el workflow de GitHub Actions para actualizar todos los precios rastreados sin esperar al cron programado.

## Pasos para configurar:

### 1. Crear un Personal Access Token (PAT) en GitHub

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
2. Click en **"Generate new token (classic)"**
3. Dale un nombre descriptivo: `price-hunter-workflow-trigger`
4. Selecciona el scope: **`repo`** (acceso completo al repositorio)
   - Marca la checkbox de `repo` (esto incluye todos los sub-permisos necesarios)
5. Click en **"Generate token"**
6. **¡COPIA EL TOKEN AHORA!** No podrás verlo de nuevo.

### 2. Configurar el token en tu app

1. Abre `frontend/src/environments/environment.ts`
2. Reemplaza `'TU_GITHUB_PERSONAL_ACCESS_TOKEN_AQUI'` con tu token real
3. **⚠️ IMPORTANTE:** Este archivo ya está en `.gitignore` para que NO se suba a GitHub

### 3. Probar el botón

1. Haz build y deploy de tu frontend:
   ```powershell
   cd frontend
   npm run build
   npm run deploy
   ```

2. En la app desplegada, haz click en **"Actualizar Ahora"**
3. Deberías ver una alerta de confirmación
4. Ve a GitHub → Actions para ver el workflow ejecutándose

## Seguridad

- ✅ El archivo `environment.ts` está en `.gitignore` 
- ✅ El token solo está en tu máquina local y en el build desplegado
- ⚠️ Si compartes el código fuente, asegúrate de NO incluir `environment.ts`
- ⚠️ Si el token se expone, revócalo inmediatamente desde GitHub Settings

## Alternativa más segura (opcional)

Para producción real, considera:
1. Crear un backend endpoint que valide la sesión del usuario
2. Desde ese backend, disparar el workflow usando el token (almacenado como variable de entorno)
3. Así el token nunca está en el cliente
