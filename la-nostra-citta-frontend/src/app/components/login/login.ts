import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Api, LoginCredentials, LoginResponse } from '../../services/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div style="max-width: 400px; margin: 20px auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px;">
      <h2>Accesso Cittadino</h2>
      <div style="margin-bottom: 15px;">
        <label style="display: block; margin-bottom: 5px;">Email:</label>
        <input type="email" [(ngModel)]="credentials.email" style="width: 100%; padding: 8px; box-sizing: border-box;">
      </div>
      <div style="margin-bottom: 15px;">
        <label style="display: block; margin-bottom: 5px;">Password:</label>
        <input type="password" [(ngModel)]="credentials.password" style="width: 100%; padding: 8px; box-sizing: border-box;">
      </div>
      <button (click)="onLogin()" style="width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Accedi
      </button>

      <div *ngIf="messaggioErrore" style="color: red; margin-top: 15px; padding: 10px; background: #fee;">
        {{ messaggioErrore }}
      </div>
      <div *ngIf="messaggioSuccesso" style="color: green; margin-top: 15px; padding: 10px; background: #efe;">
        {{ messaggioSuccesso }}
      </div>
    </div>
  `,
})
export class LoginComponent {
  credentials: LoginCredentials = { email: '', password: '' };
  messaggioErrore = '';
  messaggioSuccesso = '';

  constructor(private readonly api: Api) {}

  onLogin(): void {
    this.messaggioErrore = '';
    this.messaggioSuccesso = '';

    this.api.login(this.credentials).subscribe({
      next: (response: LoginResponse) => {
        localStorage.setItem('jwt_token', response.token);
        localStorage.setItem('user_role', response.ruolo);
        this.messaggioSuccesso = 'Accesso effettuato! Reindirizzamento...';

        setTimeout(() => {
          window.location.reload();
        }, 1000);
      },
      error: (err: { error?: { errore?: string } }) => {
        this.messaggioErrore = err.error?.errore ?? 'Errore di connessione al server';
      },
    });
  }
}