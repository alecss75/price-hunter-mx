import { Injectable, signal, NgZone } from "@angular/core";
import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Product } from "../models/product.model";
// Firebase JS SDK (no AngularFire to avoid version mismatch)
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { collection, doc, setDoc, deleteDoc, onSnapshot, getDoc } from 'firebase/firestore';
import { firebaseAuth, firebaseDb } from '../firebase.config';
import { switchMap, of, Observable } from 'rxjs';
import { environment } from '../environments/environment';

interface ScrapeResult {
  name: string;
  store: string;
  price: number;
  status: string;
  url: string;
  query_term?: string;
}

@Injectable({
  providedIn: "root",
})
export class ProductService {
  searchLogs = signal<string[]>([]);
  isLoading = signal<boolean>(false);

  constructor(private http: HttpClient, private ngZone: NgZone) {}

  // Usuario actual (Observable)
  user$ = new Observable<any>((subscriber) => {
    const unsub = onAuthStateChanged(firebaseAuth, (u) => subscriber.next(u));
    return () => unsub();
  });

  // Lista de tracking privada del usuario
  userTracking$ = this.user$.pipe(
    switchMap(u => {
      if (u) {
        return new Observable<any[]>((subscriber) => {
          const trackingCol = collection(firebaseDb, `users/${u.uid}/tracking`);
          const unsub = onSnapshot(trackingCol, (snap) => {
            const items = snap.docs.map(d => ({ id: d.id, ...d.data() }));
            subscriber.next(items as any[]);
          });
          return () => unsub();
        });
      } else {
        return of([]);
      }
    })
  );

  private availableStoresData: {
    name: Product["store"];
    logo: string;
    url: string;
  }[] = [
    {
      name: "Amazon México",
      logo: `
        <svg class="w-8 h-8" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.531 11.453l-6.328 6.328c-.313.313-.828.313-1.141 0l-6.328-6.328c-.625-.625-.188-1.719.688-1.719h12.5c.859 0 1.313 1.094.688 1.719z"></path>
        </svg>`,
      url: "https://www.amazon.com.mx",
    },
    {
      name: "Cyberpuerta",
      logo: `
        <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
        </svg>`,
      url: "https://www.cyberpuerta.mx",
    },
    {
      name: "Mercado Libre",
      logo: `
        <svg class="w-8 h-8" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M18.903 6.031l-5.656 5.657c-.125.125-.281.188-.453.188s-.328-.063-.453-.188L6.03 5.422c-.25-.25-.656-.25-.906 0s-.25.656 0 .906l6.219 6.844c.641.641 1.703.641 2.344 0l6.219-6.844c.25-.25.25-.656 0-.906s-.656-.25-.906 0z"></path>
        </svg>`,
      url: "https://www.mercadolibre.com.mx",
    },
    {
      name: "DDtech",
      logo: `
        <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
          <line x1="7" y1="17" x2="7" y2="7"></line>
          <line x1="17" y1="17" x2="17" y2="7"></line>
          <line x1="7" y1="7" x2="17" y2="7"></line>
          <line x1="7" y1="12" x2="12" y2="12"></line>
          <line x1="12" y1="17" x2="12" y2="7"></line>
        </svg>`,
      url: "https://www.ddtech.mx",
    },
  ];

  products = signal<Product[]>([]);

  // Expose products as a plain array accessor for templates/components
  getProducts(): Product[] {
    return this.products();
  }

  getAvailableStores() {
    return this.availableStoresData;
  }

  // Auth
  login() {
    return signInWithPopup(firebaseAuth, new GoogleAuthProvider());
  }

  logout() {
    return signOut(firebaseAuth);
  }

  loadBackendProducts(): void {
    this.http.get<ScrapeResult[]>(`${environment.apiUrl}/products`).subscribe({
      next: (results) => {
        this.products.update((currentProducts) => {
          const updatedProducts = [...currentProducts];

          results.forEach((res) => {
            const storeInfo = this.availableStoresData.find(
              (s) => s.name === res.store
            );
            const logo = storeInfo ? storeInfo.logo : "";
            const queryTerm = res.query_term || res.name;

            const existingIndex = updatedProducts.findIndex(
              (p) => p.query === queryTerm && p.store === res.store
            );

            if (existingIndex !== -1) {
              // Update existing
              const existingProduct = updatedProducts[existingIndex];
              updatedProducts[existingIndex] = {
                ...existingProduct,
                name: res.name,
                url: res.url,
                priceHistory: [
                  ...existingProduct.priceHistory,
                  { date: new Date(), price: res.price },
                ],
              };
            } else {
              // Add new
              updatedProducts.push({
                id: `${res.store
                  .toLowerCase()
                  .replace(/\s/g, "-")}-${Date.now()}-${Math.floor(
                  Math.random() * 1000
                )}`,
                query: queryTerm,
                name: res.name,
                store: res.store as Product["store"],
                storeLogo: logo,
                url: res.url,
                priceHistory: [
                  {
                    date: new Date(),
                    price: res.price,
                  },
                ],
              });
            }
          });

          return updatedProducts;
        });
      },
      error: (err) => console.error("Error fetching backend products", err),
    });
  }

  addProduct(rawProductName: string, forceRefresh: boolean = false): void {
    // Normalize: Trim and Title Case (simple implementation)
    const productName = rawProductName.trim().replace(/\w\S*/g, (txt) => {
      return txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase();
    });

    console.log('addProduct called for:', productName, 'forceRefresh:', forceRefresh); // Debug log
    this.isLoading.set(true);
    this.searchLogs.set([]); // Limpiar logs viejos
    this.searchLogs.update((logs) => [
      ...logs,
      `> Iniciando protocolo de búsqueda para: ${productName}...`,
    ]);

    // Usamos EventSource para conectar al endpoint de Streaming
    const url = `${environment.apiUrl}/scrape-stream?product_name=${encodeURIComponent(productName)}&force_refresh=${forceRefresh}`;
    console.log('Connecting to EventSource:', url);
    
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
       console.log('EventSource connected');
    };

    eventSource.onmessage = (event) => {
      this.ngZone.run(() => {
        // console.log('Event received:', event.data); 
        const payload = JSON.parse(event.data);

        if (payload.type === "log") {
          // AGREGAMOS LOG A LA CONSOLA
          this.searchLogs.update((logs) => [...logs, `> ${payload.message}`]);
        } else if (payload.type === "result") {
          // PRODUCTO ENCONTRADO -> Lo procesamos
          const res = payload.data;
          this.processSingleResult(res);
        } else if (payload.type === "done") {
          // TERMINÓ
          this.searchLogs.update((logs) => [...logs, `> PROCESO COMPLETADO.`]);
          this.isLoading.set(false);
          eventSource.close(); // Cerramos conexión
        }
      });
    };

    eventSource.onerror = (error) => {
      this.ngZone.run(() => {
        console.error("EventSource error:", error);
        this.searchLogs.update((logs) => [
          ...logs,
          `> 💥 ERROR DE CONEXIÓN CON EL SERVIDOR. (Verifica que el backend esté corriendo)`,
        ]);
        this.isLoading.set(false);
        eventSource.close();
      });
    };
  }

  // Guardar tracking en tu lista privada
  async trackProduct(query: string) {
    const u = firebaseAuth.currentUser;
    if (!u) return alert("Inicia sesión para guardar");

    const docRef = doc(firebaseDb, `users/${u.uid}/tracking/${query.toLowerCase()}`);
    await setDoc(docRef, {
      query: query,
      created_at: new Date(),
      last_updated: null,
    });
  }

  async untrackProduct(queryId: string) {
    const u = firebaseAuth.currentUser;
    if (!u) return;
    const docRef = doc(firebaseDb, `users/${u.uid}/tracking/${queryId}`);
    await deleteDoc(docRef);
  }

  private addMockProduct(productName: string): void {
    const newProducts: Product[] = this.availableStoresData.map((storeInfo) => {
      const searchParam = encodeURIComponent(productName);
      const newProduct: Product = {
        query: productName,
        name: productName,
        id: `${storeInfo.name.toLowerCase().replace(/\s/g, "-")}-${Date.now()}`,
        store: storeInfo.name,
        storeLogo: storeInfo.logo,
        url: `${storeInfo.url}/s?k=${searchParam}`, // Generic search URL
        priceHistory: [
          {
            date: new Date(),
            price: Math.floor(Math.random() * 3000) + 5000, // Mock initial price
          },
        ],
      };
      return newProduct;
    });

    this.products.update((currentProducts) => [
      ...currentProducts,
      ...newProducts,
    ]);
  }

  private processSingleResult(res: any) {
    const storeInfo = this.availableStoresData.find(
      (s) => s.name === res.store
    );
    const logo = storeInfo ? storeInfo.logo : "";
    const queryTerm = res.query_term || res.name;

    this.products.update((currentProducts) => {
      const existingIndex = currentProducts.findIndex(
        (p) => p.query === queryTerm && p.store === res.store
      );

      if (existingIndex !== -1) {
        // Update existing product
        const updatedProducts = [...currentProducts];
        const existingProduct = updatedProducts[existingIndex];

        updatedProducts[existingIndex] = {
          ...existingProduct,
          name: res.name, // Update name just in case
          url: res.url, // Update URL just in case
          priceHistory: [
            ...existingProduct.priceHistory,
            { date: new Date(), price: res.price },
          ],
        };
        return updatedProducts;
      }

      // Add new product
      const newProduct: Product = {
        id: `${res.store
          .toLowerCase()
          .replace(/\s/g, "-")}-${Date.now()}-${Math.floor(
          Math.random() * 1000
        )}`,
        query: queryTerm,
        name: res.name,
        store: res.store,
        storeLogo: logo,
        url: res.url,
        priceHistory: [{ date: new Date(), price: res.price }],
      };

      return [...currentProducts, newProduct];
    });
  }

  deleteProduct(productId: string): void {
    this.products.update((currentProducts) =>
      currentProducts.filter((p) => p.id !== productId)
    );
  }

  // Fetch more options for comparison from Firestore (pre-scraped by GitHub Actions)
  getStoreOptions(query: string, store: string, limit: number = 10): Observable<Array<{ name: string; price: number; url: string; store: string }>> {
    return new Observable(observer => {
      const queryLower = query.toLowerCase();
      const docRef = doc(firebaseDb, 'store_options', queryLower);
      
      getDoc(docRef).then(docSnap => {
        if (docSnap.exists()) {
          const data = docSnap.data();
          const allOptions = data['options'] || [];
          
          // Filter by store if specified, otherwise return all
          let filteredOptions = store 
            ? allOptions.filter((opt: any) => opt.store === store)
            : allOptions;
          
          // Limit results
          filteredOptions = filteredOptions.slice(0, limit);
          
          observer.next(filteredOptions);
          observer.complete();
        } else {
          // No options found in Firestore
          observer.next([]);
          observer.complete();
        }
      }).catch(error => {
        console.error('Error fetching store options:', error);
        observer.error(error);
      });
    });
  }
}

