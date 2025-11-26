import { ChangeDetectionStrategy, Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product, PriceEntry } from '../../models/product.model';
import { GeminiService } from '../../services/gemini.service';
import { ProductService } from '../../services/product.service';
import { SafeHtmlPipe } from '../../pipes/safe-html.pipe';

@Component({
  selector: 'app-product-card',
  templateUrl: './product-card.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, SafeHtmlPipe],
})
export class ProductCardComponent {
  @Input() product!: Product;
  @Output() deleteRequest = new EventEmitter<string>();

  constructor(private geminiService: GeminiService, private productService: ProductService) {}

  analysis: string | null = null;
  isLoadingAnalysis = false;
  error: string | null = null;
  showHistory = false;

  // Comparison options state
  optionsOpen = false;
  optionsLoading = false;
  options: Array<{ name: string; price: number; url: string; store: string }> = [];

  get currentPrice(): PriceEntry | undefined {
    const history = this.product?.priceHistory ?? [];
    return history.length > 0 ? history[history.length - 1] : undefined;
  }

  get previousPrice(): PriceEntry | undefined {
    const history = this.product?.priceHistory ?? [];
    return history.length > 1 ? history[history.length - 2] : undefined;
  }

  get priceChange(): { amount: number; isUp: boolean } | null {
    const current = this.currentPrice;
    const previous = this.previousPrice;
    if (current && previous) {
      const diff = current.price - previous.price;
      return {
        amount: Math.abs(diff),
        isUp: diff > 0,
      };
    }
    return null;
  }

  get isSignificantDrop(): boolean {
    const current = this.currentPrice;
    const previous = this.previousPrice;
    if (current && previous && current.price < previous.price) {
      const percentageDrop = (previous.price - current.price) / previous.price;
      return percentageDrop > 0.1; // 10% drop
    }
    return false;
  }

  isUrlVerified(): boolean {
    if (!this.product) return false;
    const p = this.product;
    const storeDomains: { [key in Product['store']]: string } = {
      'Amazon México': 'amazon.com.mx',
      'Cyberpuerta': 'cyberpuerta.mx',
      'Mercado Libre': 'mercadolibre.com.mx',
      'DDtech': 'ddtech.mx',
    };
    const expectedDomain = storeDomains[p.store];
    return p.url.includes(expectedDomain);
  }

  get displayHistory() {
    return [...(this.product?.priceHistory ?? [])].reverse();
  }

  async getAnalysis() {
    this.isLoadingAnalysis = true;
    this.analysis = null;
    this.error = null;
    try {
      const result = await this.geminiService.analyzePriceTrend(
        this.product.name,
        this.product.priceHistory
      );
      this.analysis = result;
    } catch (e) {
      this.error = 'Error al obtener el análisis.';
      console.error(e);
    } finally {
      this.isLoadingAnalysis = false;
    }
  }

  formatCurrency(value: number): string {
    return value.toLocaleString('es-MX', {
      style: 'currency',
      currency: 'MXN',
    });
  }

  toggleOptions() {
    this.optionsOpen = !this.optionsOpen;
    if (this.optionsOpen && this.options.length === 0) {
      this.loadOptions();
    }
  }

  private loadOptions() {
    const q = this.product.query || this.product.name;
    // Pasamos empty string para obtener opciones de TODAS las tiendas
    const store = ''; // Empty = todas las tiendas
    this.optionsLoading = true;
    this.productService.getStoreOptions(q, store, 10).subscribe({
      next: (opts: any) => {
        this.options = opts || [];
        this.optionsLoading = false;
      },
      error: () => {
        this.options = [];
        this.optionsLoading = false;
      },
    });
  }
}
