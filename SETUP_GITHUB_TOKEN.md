# Actualización de Precios con GitHub Actions

El sistema actualiza precios **automáticamente** mediante GitHub Actions sin necesidad de configuración adicional.

## Arquitectura Segura (Sin Token en Frontend)

El sistema funciona así:
1. **Frontend (Angular)** → Firebase Hosting + Firestore para datos
2. **GitHub Actions** → Scraping automático cada 4 horas
3. **Tus amigos** → Solo ven precios, no pueden disparar actualizaciones

### Ventajas:
✅ **100% seguro** - sin tokens expuestos en el código  
✅ **100% gratis** - sin necesidad de tarjeta de crédito  
✅ **6 actualizaciones diarias** automáticas (cada 4 horas)  
✅ **Tus amigos pueden usar la app** sin riesgos de seguridad

---

## Frecuencia de Actualización Automática

El scraper corre **6 veces al día** automáticamente:
- 🕐 6:00 PM CDMX
- 🕐 10:00 PM CDMX
- 🕐 2:00 AM CDMX
- 🕐 6:00 AM CDMX
- 🕐 10:00 AM CDMX
- 🕐 2:00 PM CDMX

---

## Actualización Manual (Opcional)

Si necesitas forzar una actualización inmediata:

### Desde tu celular:
1. Abre **GitHub.com** en el navegador
2. Ve a tu repositorio `price-hunter-mx`
3. Click en **"Actions"** (en el menú superior)
4. Click en **"Daily Price Scraper"** (en la lista de workflows)
5. Click en **"Run workflow"** → **"Run workflow"**
6. ¡Listo! El scraper se ejecutará en ~2 minutos

### Desde tu PC:
Mismo proceso en GitHub.com

---

## Uso de la App

### Para ti y tus amigos:
1. Abrir https://price-hunter-mx.web.app
2. **Iniciar sesión con Google** (para guardar productos)
3. **Agregar productos** que quieren rastrear
4. **Ver precios actualizados** automáticamente cada 4 horas

### Control de acceso:
- ✅ Cualquiera puede ver precios
- ✅ Solo usuarios logueados pueden agregar/eliminar productos
- ✅ Cada usuario ve solo sus productos rastreados
- ✅ Solo tú puedes disparar el scraper manualmente desde GitHub

---

## Seguridad

✅ **Cero tokens en el código** del frontend  
✅ **Tus amigos no pueden** disparar actualizaciones  
✅ **GitHub Actions es privado** - solo tú tienes acceso  
✅ **Firebase Auth** protege los datos de cada usuario

---

## Troubleshooting

### ¿Por qué no hay botón "Actualizar Ahora"?
→ Para evitar exponer tokens de GitHub. Solo tú puedes actualizar manualmente desde GitHub.com

### ¿Cómo sé si se actualizó?
→ Ve a GitHub → Actions → verás el historial de ejecuciones

### ¿Puedo cambiar la frecuencia?
→ Sí, edita `.github/workflows/scraper.yml` y modifica los horarios `cron`
