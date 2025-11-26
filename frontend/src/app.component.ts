import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';
import { ProductCardComponent } from './components/product-card/product-card.component';
import { ProductService } from './services/product.service';
import { Product } from './models/product.model';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ProductCardComponent, ReactiveFormsModule],
})
export class AppComponent {
  constructor(public productService: ProductService) {
    // Auto-cargar productos guardados cuando el usuario se autentica
    this.productService.userTracking$.subscribe(trackingItems => {
      // Para cada producto rastreado, cargarlo automáticamente
      trackingItems.forEach(item => {
        const query = item.query || item.id;
        // Solo cargar si no está ya en la lista de productos actuales
        const alreadyLoaded = this.productService.getProducts().some(p => 
          (p.query || p.name) === query
        );
        if (!alreadyLoaded) {
          console.log(`🔄 Auto-cargando producto guardado: ${query}`);
          this.productService.addProduct(query, false);
        }
      });
    });
  }

  isAddingProduct = false;
  collapsedGroups = new Set<string>();

  availableStores = this.productService.getAvailableStores();

  productForm = new FormGroup({
    name: new FormControl('', [Validators.required, Validators.minLength(3)]),
  });

  get products() {
    return this.productService.getProducts();
  }

  get groupedProducts(): { name: string; products: Product[] }[] {
    const groups: { [key: string]: Product[] } = {};
    this.products.forEach((p) => {
      const key = p.query || p.name;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(p);
    });

    return Object.keys(groups).map((name) => ({
      name,
      products: groups[name],
    }));
  }

  isGroupOpen(groupName: string): boolean {
    return !this.collapsedGroups.has(groupName);
  }

  toggleGroup(groupName: string): void {
    if (this.collapsedGroups.has(groupName)) {
      this.collapsedGroups.delete(groupName);
    } else {
      this.collapsedGroups.add(groupName);
    }
  }

  refreshGroup(groupName: string): void {
    this.productService.addProduct(groupName, true);
  }

  deleteGroup(groupName: string): void {
    const productsToDelete = this.products.filter((p) => (p.query || p.name) === groupName);
    productsToDelete.forEach((p) => this.productService.deleteProduct(p.id));
  }

  onSubmit(): void {
    if (this.productForm.invalid || this.productLimitReached) {
      return;
    }
    const formValue = this.productForm.getRawValue();
    // Inicia streaming inmediato
    this.productService.addProduct(formValue.name!);
    // Guarda en la lista privada del usuario (si hay sesión)
    this.productService.trackProduct(formValue.name!);
    this.toggleAddProductForm();
  }

  onDeleteProduct(productId: string): void {
    this.productService.deleteProduct(productId);
  }

  get productLimitReached() {
    return this.products.length >= 10;
  }

  toggleAddProductForm(): void {
    this.isAddingProduct = !this.isAddingProduct;
    if (!this.isAddingProduct) {
      this.productForm.reset();
    }
  }
}
