export interface PriceEntry {
  date: Date;
  price: number;
}

export interface Product {
  id: string;
  query: string; // The search term used to find this product
  name: string;
  store: 'Amazon México' | 'Cyberpuerta' | 'Mercado Libre' | 'DDtech';
  storeLogo: string; // SVG path or URL
  url: string;
  priceHistory: PriceEntry[];
}
