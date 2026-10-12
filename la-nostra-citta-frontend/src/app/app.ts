import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardComponent } from './components/dashboard/dashboard';
import { LoginComponent } from './components/login/login';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, DashboardComponent, LoginComponent],
  template: `
    <div class="shell">
      <header class="site-header"><a class="brand" href="/" aria-label="La Nostra Città, home"><span class="brand-mark">LC</span><span>La Nostra Città<small>Il nostro futuro</small></span></a><button *ngIf="isLoggedIn" class="logout" (click)="logout()">Esci</button></header>
      <main><app-login *ngIf="!isLoggedIn"></app-login><app-dashboard *ngIf="isLoggedIn"></app-dashboard></main>
      <footer>Una piattaforma civica per Milano · Accessibile, trasparente, partecipata</footer>
    </div>
  `,
})
export class AppComponent implements OnInit {
  isLoggedIn = false;

  ngOnInit(): void {
    if (typeof localStorage !== 'undefined') {
      this.isLoggedIn = !!localStorage.getItem('jwt_token');
    }
  }

  logout(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('user_role');
    }
    this.isLoggedIn = false;
  }
}

export { AppComponent as App };