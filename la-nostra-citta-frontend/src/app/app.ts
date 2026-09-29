import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardComponent } from './components/dashboard/dashboard';
import { LoginComponent } from './components/login/login';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, DashboardComponent, LoginComponent],
  template: `
    <div style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0; color: #333;">La Nostra Città, Il Nostro Futuro</h1>
        <button *ngIf="isLoggedIn" (click)="logout()" style="padding: 8px 15px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Esci
        </button>
      </div>

      <app-login *ngIf="!isLoggedIn"></app-login>
      <app-dashboard *ngIf="isLoggedIn"></app-dashboard>
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