import re
import asyncio
import random
import os
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin
from contextlib import asynccontextmanager

import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

import firebase_admin
from firebase_admin import credentials, firestore

# --- HACK PARA RENDER: INSTALAR NAVEGADOR AL ARRANQUE ---
import sys
import subprocess
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser.close()
    print("✅ Navegador encontrado. Continuando...")
except Exception as e:
    print(f"⚠️ Navegador no encontrado ({e}). Instalando ahora...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install-deps"])
    print("✅ Navegador instalado correctamente.")
# -------------------------------------------------------

# --- INICIALIZACIÓN DE FIREBASE (IDEMPOTENTE) ---
try:
    if not firebase_admin._apps:
        # 1. Archivo local de credenciales
        if os.path.exists("ServiceAccountPriceHunterMx.json"):
            cred = credentials.Certificate("ServiceAccountPriceHunterMx.json")
            firebase_admin.initialize_app(cred)
        # 2. Variable de entorno (GitHub Actions / CI / Deploy)
        elif os.environ.get("FIREBASE_CREDENTIALS_JSON"):
            cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS_JSON"))
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # 3. Credenciales implícitas (Cloud Run / GCP runtime)
            firebase_admin.initialize_app()
        print("🔥 Firebase inicializado por primera vez.")
    else:
        print("ℹ️ Firebase ya inicializado; reutilizando app existente.")
    db = firestore.client()
    print("🔥 Firebase conectado exitosamente.")
except Exception as e:
    print(f"⚠️ Error conectando a Firebase: {e}")
    db = None

# --- BACKGROUND TASKS ---

async def scrape_and_cache(query_term: str):
    """
    Versión silenciosa de scrape_stream para el background worker.
    """
    print(f"🔄 [Background] Actualizando: {query_term}")
    playwright = None
    browser = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        results_for_cache = []
        for store in STORES:
            try:
                # Reutilizamos search_store (que es un generador)
                async for event in search_store(browser, store, query_term):
                    if event["type"] == "result":
                        result = event["data"]
                        if result['status'] == 'success':
                            results_for_cache.append(result)
            except Exception as e:
                print(f"❌ [Background] Error en {store['name']} para {query_term}: {e}")

        if results_for_cache:
            save_results_to_cache(query_term, results_for_cache)
            update_tracked_query_timestamp(query_term)
            print(f"✅ [Background] Guardados {len(results_for_cache)} resultados para {query_term}")
        else:
            print(f"⚠️ [Background] No se encontraron resultados para {query_term}")

    except Exception as e:
        print(f"💥 [Background] Error crítico para {query_term}: {e}")
    finally:
        if browser: await browser.close()
        if playwright: await playwright.stop()

async def background_scraper_task():
    """
    Tarea que corre infinitamente para actualizar precios.
    """
    while True:
        try:
            tracked = get_tracked_queries_db()
            if not tracked:
                print("💤 [Background] No hay queries rastreadas. Durmiendo 60s...")
                await asyncio.sleep(60)
                continue

            print(f"📋 [Background] Procesando {len(tracked)} queries...")
            for item in tracked:
                query = item["query"]
                # Verificar si necesita actualización (ej: más de 24 horas)
                last_update = item["last_updated"]
                needs_update = True
                if last_update:
                    try:
                        last_date = datetime.fromisoformat(last_update)
                        if datetime.now() - last_date < timedelta(hours=24):
                            needs_update = False
                    except: pass
                
                if needs_update:
                    await scrape_and_cache(query)
                    # Esperar un poco entre queries para no saturar
                    await asyncio.sleep(10) 
            
            # Esperar antes de la siguiente ronda completa
            print("💤 [Background] Ronda terminada. Durmiendo 1 hora...")
            await asyncio.sleep(3600) 

        except Exception as e:
            print(f"💥 [Background] Error en el loop principal: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Iniciar background task
    task = asyncio.create_task(background_scraper_task())
    yield
    # Shutdown: (Opcional) Cancelar tarea si fuera necesario
    # task.cancel()

app = FastAPI(title="price-hunter-backend", lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://price-hunter-mx.web.app",
    "https://price-hunter-mx.firebaseapp.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. BASE DE DATOS (Firestore) ---

def init_db():
    # Firestore no requiere inicialización de tablas
    pass

def add_tracked_query_db(query_term: str):
    if not db: return
    try:
        doc_ref = db.collection("tracked_queries").document(query_term.lower())
        doc_ref.set({
            "query_term": query_term.lower(),
            "last_updated": None
        }, merge=True)
    except Exception as e:
        print(f"Error adding tracked query: {e}")

def remove_tracked_query_db(query_term: str):
    if not db: return
    try:
        db.collection("tracked_queries").document(query_term.lower()).delete()
    except Exception as e:
        print(f"Error removing tracked query: {e}")

def get_tracked_queries_db():
    if not db: return []
    try:
        # Busca en TODAS las subcolecciones 'tracking' de todos los usuarios
        docs = db.collection_group('tracking').stream()
        unique_queries = {}

        for doc in docs:
            data = doc.to_dict() or {}
            q = data.get("query") or data.get("query_term") or doc.id
            lu = data.get("last_updated")

            # Normalizar last_updated a string ISO si viene como datetime/timestamp
            try:
                if isinstance(lu, datetime):
                    lu = lu.isoformat()
            except:
                pass

            if q:
                # Si ya existe el query, conservar el timestamp más antiguo para forzar actualización
                prev = unique_queries.get(q)
                if not prev:
                    unique_queries[q] = lu
                else:
                    try:
                        if prev and lu:
                            prev_dt = datetime.fromisoformat(prev) if isinstance(prev, str) else None
                            lu_dt = datetime.fromisoformat(lu) if isinstance(lu, str) else None
                            if prev_dt and lu_dt and lu_dt < prev_dt:
                                unique_queries[q] = lu
                    except:
                        # Si no se puede comparar, mantener el existente
                        pass

        return [{"query": q, "last_updated": lu} for q, lu in unique_queries.items()]
    except Exception as e:
        print(f"Error getting tracked queries (collection_group): {e}")
        return []

def update_tracked_query_timestamp(query_term: str):
    if not db: return
    try:
        # Actualiza el timestamp en TODAS las coincidencias dentro de 'users/*/tracking'
        docs = db.collection_group('tracking').where("query", "==", query_term).stream()
        batch = db.batch()
        for doc in docs:
            batch.update(doc.reference, {"last_updated": datetime.now().isoformat()})
        batch.commit()
    except Exception as e:
        print(f"Error updating timestamp (collection_group): {e}")

def get_cached_results(query_term: str, max_age_hours: int = 24) -> List[dict]:
    if not db: return []
    try:
        # En Firestore, guardaremos los resultados dentro de una subcolección o colección 'products'
        # Estructura: products/{query_term}/results/{store_name} o similar.
        # Para simplificar, usaremos una colección 'products' donde el ID es compuesto o buscamos por query_term
        
        # Opción: Colección 'cached_results', documento = query_term
        doc_ref = db.collection("cached_results").document(query_term.lower())
        doc = doc_ref.get()
        
        if not doc.exists:
            return []
            
        data = doc.to_dict()
        updated_at_str = data.get("updated_at")
        if not updated_at_str:
            return []
            
        updated_at = datetime.fromisoformat(updated_at_str)
        if datetime.now() - updated_at > timedelta(hours=max_age_hours):
            return [] # Expirado
            
        return data.get("results", [])
    except Exception as e:
        print(f"Error getting cached results: {e}")
        return []

def get_all_cached_products() -> List[dict]:
    if not db: return []
    try:
        results = []
        docs = db.collection("cached_results").stream()
        for doc in docs:
            data = doc.to_dict()
            query_term = data.get("query_term", doc.id).title()
            updated_at = data.get("updated_at")
            
            for r in data.get("results", []):
                results.append({
                    "query_term": query_term,
                    "name": r.get("name"),
                    "store": r.get("store"),
                    "price": r.get("price"),
                    "status": r.get("status"),
                    "url": r.get("url"),
                    "updated_at": updated_at
                })
        return results
    except Exception as e:
        print(f"Error getting all cached products: {e}")
        return []

def save_results_to_cache(query_term: str, results: List[dict]):
    if not db: return
    try:
        doc_ref = db.collection("cached_results").document(query_term.lower())
        doc_ref.set({
            "query_term": query_term.lower(),
            "updated_at": datetime.now().isoformat(),
            "results": results
        })
    except Exception as e:
        print(f"Error saving results to cache: {e}")

# --- 2. CONFIGURACIÓN DE TIENDAS (SELECTORES MEJORADOS) ---
STORES = [
    {
        "name": "Amazon México",
        "search_url": "https://www.amazon.com.mx/s?k={query}",
        "selectors": {
            "item": [
                # 1. Estándar
                "div[data-component-type='s-search-result']",
                # 2. Alternativo común
                "div.s-result-item[data-uuid]",
                # 3. LA OPCIÓN NUCLEAR: Cualquier cosa que tenga ID de producto (ASIN)
                "div[data-asin]:not([data-asin=''])"
            ],
            "title": [
                "h2 a span", 
                "span.a-size-medium", 
                "span.a-text-normal",
                "h2 span",
                "[data-cy='title-recipe'] h2 span",
                "[data-cy='title-recipe'] h2",
                "h2.a-text-normal"
            ],
            "link": [
                "h2 a", 
                "a.a-link-normal.s-underline-text",
                "a.a-link-normal"
            ],
            "price": [
                ".a-price .a-offscreen", 
                "span.a-price span.a-offscreen",
                ".a-price"
            ]
        }
    },
    {
        "name": "Mercado Libre",
        "search_url": "https://listado.mercadolibre.com.mx/{query}",
        "selectors": {
            # Array para soportar diseño viejo y diseño nuevo "Poly"
            "item": ["div.ui-search-result__wrapper", "li.ui-search-layout__item", "div.poly-card"],
            "title": [".ui-search-item__title", ".poly-component__title"],
            "link": ["a.ui-search-link", "a.poly-component__title"],
            "price": [
                ".ui-search-price__part .andes-money-amount__fraction", 
                ".poly-price__current .andes-money-amount__fraction",
                ".andes-money-amount__fraction"
            ]
        }
    },
    {
        "name": "Cyberpuerta",
        "search_url": "https://www.cyberpuerta.mx/index.php?cl=search&searchparam={query}",
        "selectors": {
            "item": "div.emproduct", 
            "title": "a.emproduct_right_title",
            "link": "a.emproduct_right_title",
            "price": "label.price",
            "no_results": ".oxwidget_headernotice_noproduct"
        }
    },
    {
        "name": "DDtech",
        "search_url": "https://ddtech.mx/buscar/{query}",
        "selectors": {
            "item": "div.product",
            "title": "h3 a",
            "link": "h3 a",
            "price": ".product-price",
            "no_results": "p.without-results"
        }
    }
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# --- MODELOS Y UTILIDADES ---
class ScrapeResult(BaseModel):
    name: str
    store: str
    price: float
    status: str
    url: str
    query_term: Optional[str] = None

class AnalysisRequest(BaseModel):
    productName: str
    priceHistory: List[dict] 

class AnalysisResponse(BaseModel):
    analysis: str

def clean_price(text_price: Optional[str]) -> float:
    if not text_price: return 0.0
    clean = text_price.replace("$", "").replace("MXN", "").replace(" ", "").strip().replace(",", "")
    try:
        return float(clean)
    except ValueError:
        import re
        match = re.search(r"(\d+(\.\d+)?)", clean)
        return float(match.group(1)) if match else 0.0

async def apply_stealth_manual(page):
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

def normalize_text(text: str) -> str:
    """
    Convierte 'RTX 5070TI' en 'rtx 5070 ti' para facilitar la búsqueda.
    Separa números de letras y quita caracteres raros.
    """
    if not text: return ""
    # 1. A minúsculas
    text = text.lower()
    # 2. Separar números de letras (ej: 5070ti -> 5070 ti)
    text = re.sub(r'(\d+)([a-z]+)', r'\1 \2', text)
    text = re.sub(r'([a-z]+)(\d+)', r'\1 \2', text)
    # 3. Quitar puntuación extra
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # 4. Quitar espacios dobles
    return " ".join(text.split())

SEMAPHORE = asyncio.Semaphore(3)

async def search_store(browser, store, query):
    async with SEMAPHORE:
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="es-MX",
            timezone_id="America/Mexico_City"
        )
        
        page = await context.new_page()
        await apply_stealth_manual(page)
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        search_url = store["search_url"].format(query=query.replace(" ", "+"))
        # Estructura base de respuesta (ahora incluirá 'candidates' para debug si quieres)
        result = {
            "name": query, 
            "store": store["name"], 
            "price": 0.0, 
            "status": "error", 
            "url": search_url,
            "query_term": query
        }

        try:
            await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

            # --- DEBUG TEMPORAL: GUARDAR HTML SIEMPRE ---
            # debug_dir = "debug_htmls"
            # os.makedirs(debug_dir, exist_ok=True)
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # safe_query = query.replace(" ", "_")
            # safe_store = store["name"].replace(" ", "_")
            # filename = f"{debug_dir}/{safe_store}_{safe_query}_{timestamp}.html"
            
            # try:
            #     content = await page.content()
            #     with open(filename, "w", encoding="utf-8") as f:
            #         f.write(content)
            #     print(f"📸 Snapshot guardado: {filename}")
            # except Exception as e:
            #     print(f"⚠️ No se pudo guardar snapshot: {e}")
            # -------------------------------------------

            # 1. Chequeo de "Sin resultados"
            if "no_results" in store["selectors"]:
                try:
                    if await page.locator(store["selectors"]["no_results"]).count() > 0:
                        if await page.locator(store["selectors"]["no_results"]).first.is_visible():
                            result["status"] = "not_found"
                            await context.close()
                            yield {"type": "result", "data": result}
                            return
                except: pass

            # 2. Determinar selector de items
            item_selector = store["selectors"]["item"]
            final_selector = None
            
            if isinstance(item_selector, list):
                for sel in item_selector:
                    count = await page.locator(sel).count()
                    if count > 0:
                        final_selector = sel
                        break
                if not final_selector: final_selector = item_selector[0]
            else:
                final_selector = item_selector

            # Esperar a que carguen los items
            try:
                await page.wait_for_selector(final_selector, timeout=10000)
            except:
                result["status"] = "not_found"
                await context.close()
                yield {"type": "result", "data": result}
                return

            # --- ESTRATEGIA DE SELECCIÓN MÚLTIPLE ---
            
            # Obtener todos los elementos (limitamos a los primeros 15 para no saturar)
            items = await page.locator(final_selector).all()
            yield {"type": "log", "message": f"🕷️ {store['name']}: Items crudos encontrados en DOM: {len(items)}"}
            
            candidates = []

            # --- PREPARACIÓN INTELIGENTE ---
            # Normalizamos la búsqueda del usuario (ej: "5070TI" -> "5070 ti")
            normalized_query = normalize_text(query)
            query_tokens = set(normalized_query.split()) # Usamos set para búsqueda rápida
            
            yield {"type": "log", "message": f"🔍 {store['name']}: Buscando tokens {query_tokens}..."}

            exact_matches = []
            partial_matches = []

            for i, item in enumerate(items[:15]):
                try:
                    # 1. Extraer Título
                    title = ""
                    title_sel_conf = store["selectors"]["title"]
                    title_sels = title_sel_conf if isinstance(title_sel_conf, list) else [title_sel_conf]
                    for ts in title_sels:
                        if await item.locator(ts).count() > 0:
                            title = await item.locator(ts).first.inner_text()
                            break
                    
                    if not title:
                        yield {"type": "log", "message": f"   ⚠️ {store['name']}: Item {i} sin título detectable."}
                        continue

                    # 2. Normalizar Título del Producto
                    normalized_title = normalize_text(title)
                    title_tokens = set(normalized_title.split())

                    # 3. COMPARACIÓN DE TOKENS (Matemática de conjuntos)
                    # ¿Cuántas palabras de la query están en el título?
                    # intersection recupera las palabras que existen en ambos lados
                    common_tokens = query_tokens.intersection(title_tokens)
                    match_count = len(common_tokens)
                    total_required = len(query_tokens)

                    # Umbral de aceptación:
                    # Aceptamos si coinciden TODAS las palabras (Exacto)
                    # O si falta máximo 1 palabra (Parcial) - Útil si "GeForce" no aparece o cosas así
                    is_exact = match_count == total_required
                    is_partial = match_count >= (total_required - 1) and total_required > 1

                    if not is_partial and not is_exact:
                        yield {"type": "log", "message": f"   ❌ {store['name']}: Descartado '{title[:20]}...' (Match: {match_count}/{total_required})"}
                        continue

                    # 4. Extraer Precio (Tu lógica existente)
                    price_text = ""
                    price_sel_conf = store["selectors"]["price"]
                    price_sels = price_sel_conf if isinstance(price_sel_conf, list) else [price_sel_conf]
                    for ps in price_sels:
                        if await item.locator(ps).count() > 0:
                            price_text = await item.locator(ps).first.inner_text()
                            if not price_text.strip(): price_text = await item.locator(ps).first.text_content()
                            if price_text.strip(): break
                    
                    final_price = clean_price(price_text)
                    if final_price > 500000: final_price /= 100
                    
                    if final_price > 50:
                        # 5. Link
                        link_href = ""
                        link_sel_conf = store["selectors"]["link"]
                        link_sels = link_sel_conf if isinstance(link_sel_conf, list) else [link_sel_conf]
                        for ls in link_sels:
                            if await item.locator(ls).count() > 0:
                                link_href = await item.locator(ls).first.get_attribute("href")
                                break
                        
                        full_url = link_href
                        if link_href and not link_href.startswith("http"):
                             base = "https://www.amazon.com.mx" if "amazon" in store["search_url"] else "https://www.cyberpuerta.mx"
                             full_url = urljoin(base, link_href)

                        candidate = {
                            "name": title.strip(),
                            "price": final_price,
                            "url": full_url,
                            "score": match_count
                        }

                        if is_exact:
                            exact_matches.append(candidate)
                            yield {"type": "log", "message": f"   🥇 {store['name']}: Candidato EXACTO ${final_price} - {title[:30]}..."}
                        else:
                            partial_matches.append(candidate)
                            yield {"type": "log", "message": f"   🥈 {store['name']}: Candidato PARCIAL ${final_price} - {title[:30]}..."}

                except Exception as e:
                    continue

            # --- SELECCIÓN DEL GANADOR ---
            winner = None
            if exact_matches:
                exact_matches.sort(key=lambda x: x["price"])
                winner = exact_matches[0]
                result["status"] = "success"
                result["match_type"] = "exact"
            elif partial_matches:
                partial_matches.sort(key=lambda x: x["price"])
                winner = partial_matches[0]
                result["status"] = "success" # O "warning"
                result["match_type"] = "partial"
            
            if winner:
                result["name"] = winner["name"]
                result["price"] = winner["price"]
                result["url"] = winner["url"]
            else:
                result["status"] = "not_found"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        await context.close()
        yield {"type": "result", "data": result}

async def collect_store_options(browser, store, query: str, limit: int = 5) -> List[dict]:
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
        locale="es-MX",
        timezone_id="America/Mexico_City",
    )
    page = await context.new_page()
    await apply_stealth_manual(page)
    await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

    search_url = store["search_url"].format(query=query.replace(" ", "+"))
    options: List[dict] = []

    try:
        await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

        # no-results early exit
        if "no_results" in store["selectors"]:
            try:
                if await page.locator(store["selectors"]["no_results"]).count() > 0 and await page.locator(store["selectors"]["no_results"]).first.is_visible():
                    await context.close()
                    return []
            except:
                pass

        # Determine item selector
        item_selector = store["selectors"]["item"]
        final_selector = None
        if isinstance(item_selector, list):
            for sel in item_selector:
                if await page.locator(sel).count() > 0:
                    final_selector = sel
                    break
            if not final_selector:
                final_selector = item_selector[0]
        else:
            final_selector = item_selector

        try:
            await page.wait_for_selector(final_selector, timeout=10000)
        except:
            await context.close()
            return []

        items = await page.locator(final_selector).all()

        normalized_query = normalize_text(query)
        query_tokens = set(normalized_query.split())

        for item in items[:20]:
            try:
                # title
                title = ""
                title_sel_conf = store["selectors"]["title"]
                title_sels = title_sel_conf if isinstance(title_sel_conf, list) else [title_sel_conf]
                for ts in title_sels:
                    if await item.locator(ts).count() > 0:
                        title = await item.locator(ts).first.inner_text()
                        break
                if not title:
                    continue

                normalized_title = normalize_text(title)
                title_tokens = set(normalized_title.split())
                common_tokens = query_tokens.intersection(title_tokens)
                match_count = len(common_tokens)
                total_required = len(query_tokens)

                is_exact = match_count == total_required
                is_partial = match_count >= (total_required - 1) and total_required > 1
                if not is_partial and not is_exact:
                    continue

                # price
                price_text = ""
                price_sel_conf = store["selectors"]["price"]
                price_sels = price_sel_conf if isinstance(price_sel_conf, list) else [price_sel_conf]
                for ps in price_sels:
                    if await item.locator(ps).count() > 0:
                        price_text = await item.locator(ps).first.inner_text()
                        if not price_text.strip():
                            price_text = await item.locator(ps).first.text_content()
                        if price_text.strip():
                            break
                final_price = clean_price(price_text)
                if final_price > 500000:
                    final_price /= 100
                if final_price <= 50:
                    continue

                # link
                link_href = ""
                link_sel_conf = store["selectors"]["link"]
                link_sels = link_sel_conf if isinstance(link_sel_conf, list) else [link_sel_conf]
                for ls in link_sels:
                    if await item.locator(ls).count() > 0:
                        link_href = await item.locator(ls).first.get_attribute("href")
                        break
                full_url = link_href
                if link_href and not link_href.startswith("http"):
                    base = "https://www.amazon.com.mx" if "amazon" in store["search_url"] else (
                        "https://www.cyberpuerta.mx" if "cyberpuerta" in store["search_url"] else (
                            "https://www.mercadolibre.com.mx" if "mercadolibre" in store["search_url"] else "https://ddtech.mx"
                        )
                    )
                    full_url = urljoin(base, link_href)

                options.append({
                    "name": title.strip(),
                    "price": final_price,
                    "url": full_url,
                    "store": store["name"],
                    "match_score": match_count,
                })
            except Exception:
                continue

        # sort by price asc, then by match score desc
        options.sort(key=lambda x: (x["price"], -x["match_score"]))
        # de-duplicate by name+url
        seen = set()
        deduped = []
        for opt in options:
            key = (opt["name"], opt["url"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(opt)
        await context.close()
        return deduped[:limit]
    except Exception:
        await context.close()
        return []

# --- ENDPOINTS ---

@app.get("/", tags=["meta"])
async def root():
    return {"status": "ok", "service": "price-hunter-backend", "cache_system": "DISABLED_FOR_DEBUG"}

# --- NUEVO ENDPOINT CON STREAMING ---
@app.get("/products", response_model=List[ScrapeResult])
async def get_products():
    """
    Retorna todos los productos almacenados en la base de datos.
    Útil para restaurar el estado de la aplicación al recargar.
    """
    products = get_all_cached_products()
    return [ScrapeResult(**p) for p in products]

@app.get("/scrape-stream")
async def scrape_stream(product_name: str = Query(...), force_refresh: bool = False):
    async def event_generator():
        playwright = None
        browser = None
        try:
            yield f"data: {json.dumps({'type': 'log', 'message': f'🚀 Iniciando búsqueda: {product_name}'})}\n\n"

            if not force_refresh:
                cached = get_cached_results(product_name)
                if cached:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✅ Caché: {len(cached)} items.'})}\n\n"
                    for prod in cached:
                        prod['query_term'] = product_name
                        yield f"data: {json.dumps({'type': 'result', 'data': prod})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'message': 'Fin por caché'})}\n\n"
                    return

            yield f"data: {json.dumps({'type': 'log', 'message': '🕷️ Iniciando navegador...'})}\n\n"
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            results_for_cache = []
            for store in STORES:
                store_name = store['name']
                msg = f"🔎 Consultando {store_name}..."
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                try:
                    async for event in search_store(browser, store, product_name):
                        if event["type"] == "log":
                            yield f"data: {json.dumps(event)}\n\n"
                        elif event["type"] == "result":
                            result = event["data"]
                            if result['status'] == 'success':
                                mt = "EXACTO" if result.get('match_type') == 'exact' else "PARCIAL"
                                msg = f"🎉 {store_name}: {mt} ${result['price']:,.2f}"
                                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                                yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
                                results_for_cache.append(result)
                            elif result['status'] == 'not_found':
                                msg = f"⚠️ {store_name}: Sin resultados."
                                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                except Exception as e:
                     msg = f"💥 Error {store_name}: {e}"
                     yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"

            if results_for_cache:
                save_results_to_cache(product_name, results_for_cache)
            
            yield f"data: {json.dumps({'type': 'done', 'message': 'Proceso terminado'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'message': f'Error crítico: {e}'})}\n\n"
        finally:
            if browser: await browser.close()
            if playwright: await playwright.stop()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/scrape", response_model=List[ScrapeResult])
async def scrape(product_name: str = Query(...), force_refresh: bool = False):
    if not product_name: return []
    if not force_refresh:
        cached = get_cached_results(product_name)
        if cached: 
            for r in cached: r['query_term'] = product_name
            return [ScrapeResult(**r) for r in cached]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        tasks = [consume_search_store(p, browser, s, product_name) for s in STORES] # Fix: dummy consume
        # Nota: Este endpoint legacy no soporta el generador async directo fácilmente sin refactor, 
        # se recomienda usar scrape-stream.
        return [] 

# Helper para scrape legacy (simplificado)
async def consume_search_store(p, b, s, q): pass

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalysisRequest):
    return AnalysisResponse(analysis="Análisis pendiente de implementación lógica.")

# --- OPCIONES POR TIENDA (Comparación) ---
@app.get("/store-options")
async def store_options(product_name: str = Query(...), store_name: str = Query(...), limit: int = 5):
    try:
        store = next((s for s in STORES if s["name"].lower() == store_name.lower()), None)
        if not store:
            return []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            options = await collect_store_options(browser, store, product_name, limit)
            await browser.close()
            return options
    except Exception as e:
        print(f"Error in /store-options: {e}")
        return []

# --- ENDPOINTS DE TRACKING ---

@app.get("/tracked")
async def get_tracked():
    return get_tracked_queries_db()

@app.post("/track")
async def track_query(query: str = Query(...)):
    add_tracked_query_db(query)
    # Opcional: Iniciar scrape inmediato en background
    asyncio.create_task(scrape_and_cache(query))
    return {"status": "ok", "message": f"Rastreando: {query}"}

@app.delete("/track")
async def untrack_query(query: str = Query(...)):
    remove_tracked_query_db(query)
    return {"status": "ok", "message": f"Dejado de rastrear: {query}"}

if __name__ == "__main__":
    import uvicorn
    # Usar instancia directa evita re-importar el módulo y duplicar inicialización Firebase
    # Leer puerto de variable de entorno para Render/Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)