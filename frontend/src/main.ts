import { bootstrapApplication } from '@angular/platform-browser';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';

import { AppComponent } from './app.component';

// Initialize Firebase app once via firebase.config.ts side-effect
import './firebase.config';

bootstrapApplication(AppComponent, {
  providers: [provideZonelessChangeDetection(), provideHttpClient()],
});

// Entrypoint convertido a `src/main.ts` para compatibilidad con Angular CLI
