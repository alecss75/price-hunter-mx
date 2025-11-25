import asyncio
import os
# Importamos tus funciones del main.py
# Asegúrate de que en main.py NO se ejecute uvicorn automáticamente al importar
from main import scrape_and_cache, get_tracked_queries_db

async def main():
    print("🚀 Iniciando Scraper Programado en GitHub Actions...")
    
    # Si usas credenciales de Firebase desde variable de entorno (para GitHub)
    # Asegúrate de que tu main.py sepa leer os.environ.get("FIREBASE_CREDENTIALS")
    # O usa el archivo json si lo generas al vuelo (ver paso 2)

    tracked_items = get_tracked_queries_db()
    if not tracked_items:
        print("⚠️ No hay productos rastreados en la base de datos.")
        return

    print(f"📋 Encontrados {len(tracked_items)} productos para actualizar.")

    for item in tracked_items:
        product = item["query"]
        print(f"\n--- Buscando: {product} ---")
        # Usamos tu función que ya guarda en Firestore
        await scrape_and_cache(product)
    
    print("\n✅ Todo terminado. Apagando.")

if __name__ == "__main__":
    asyncio.run(main())
