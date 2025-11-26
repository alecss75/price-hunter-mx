import asyncio
import os
# Importamos tus funciones del main.py
# Asegúrate de que en main.py NO se ejecute uvicorn automáticamente al importar
from main import scrape_and_cache, scrape_store_options, get_tracked_queries_db

async def scrape_product(item):
    """Scrapea un producto y sus opciones de comparación"""
    product = item["query"]
    print(f"\n--- Buscando: {product} ---")
    await scrape_and_cache(product)
    
    print(f"\n🔍 Buscando opciones de comparación para: {product}")
    await scrape_store_options(product)

async def main():
    print("🚀 Iniciando Scraper Programado en GitHub Actions...")
    
    tracked_items = get_tracked_queries_db()
    if not tracked_items:
        print("⚠️ No hay productos rastreados en la base de datos.")
        return

    print(f"📋 Encontrados {len(tracked_items)} productos para actualizar.")
    
    # Scraping en lotes de 3 para balance entre velocidad y seguridad
    batch_size = 3
    total_batches = (len(tracked_items) + batch_size - 1) // batch_size
    
    for i in range(0, len(tracked_items), batch_size):
        batch_num = (i // batch_size) + 1
        batch = tracked_items[i:i + batch_size]
        
        print(f"\n🔄 Procesando lote {batch_num}/{total_batches} ({len(batch)} productos en paralelo)")
        await asyncio.gather(*[scrape_product(item) for item in batch])
    
    print("\n✅ Todo terminado. Apagando.")

if __name__ == "__main__":
    asyncio.run(main())
