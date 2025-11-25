
import { Injectable } from '@angular/core';
import { PriceEntry } from '../models/product.model';

@Injectable({
  providedIn: 'root',
})
export class GeminiService {
  // Calls backend /analyze endpoint which runs the same logic server-side.
  async analyzePriceTrend(productName: string, priceHistory: PriceEntry[]): Promise<string> {
    try {
      const resp = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ productName, priceHistory })
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Backend error: ${resp.status} ${text}`);
      }

      const data = await resp.json();
      return data.analysis || 'No analysis returned.';
    } catch (err) {
      console.error('Error calling backend analyze:', err);
      // Fallback to local analysis in case backend is unreachable
      if (priceHistory.length < 2) {
        return 'No hay suficientes datos para un análisis de tendencia.';
      }

      const latestPrice = priceHistory[priceHistory.length - 1].price;
      const previousPrice = priceHistory[priceHistory.length - 2].price;
      const trend = latestPrice - previousPrice;

      let analysis = `Análisis para ${productName}:\n`;
      if (trend < -50) {
        analysis += `Se observa una baja de precio significativa reciente, lo que podría indicar una buena oportunidad de compra. El precio actual es de $${latestPrice.toFixed(2)} MXN.`;
      } else if (trend > 50) {
        analysis += `El precio ha subido recientemente. Sería prudente monitorear por unos días antes de comprar. El precio actual es de $${latestPrice.toFixed(2)} MXN.`;
      } else {
        analysis += `El precio se ha mantenido relativamente estable. Es un buen momento para comprar si necesitas el producto pronto. El precio actual es de $${latestPrice.toFixed(2)} MXN.`;
      }

      return analysis;
    }
  }
}
