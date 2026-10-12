import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Api, LoginCredentials, LoginResponse, RegistrazioneDati } from '../../services/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section class="auth-panel" aria-labelledby="auth-title">
      <p class="eyebrow">Partecipazione locale</p><h1 id="auth-title">La tua voce, il futuro della città.</h1><p class="auth-intro">Accedi per sostenere le idee degli altri cittadini o crea un account verificato per proporre un cambiamento.</p>
      <div class="auth-form">
      <ng-container *ngIf="registrazioneAttiva">
        <div class="form-grid"><label>Nome<input type="text" [(ngModel)]="registrazione.nome" autocomplete="given-name" required></label><label>Cognome<input type="text" [(ngModel)]="registrazione.cognome" autocomplete="family-name" required></label></div>
        <label>Codice fiscale<input type="text" [(ngModel)]="registrazione.codice_fiscale" maxlength="16" required></label>
        <label>Indirizzo di residenza<input type="text" [(ngModel)]="registrazione.indirizzo_residenza" autocomplete="street-address" required></label>
        <label>Data di nascita<input type="date" [(ngModel)]="registrazione.data_nascita" [max]="dataMassima" required></label>
        <div class="form-grid"><label>Documento, fronte<input type="file" accept="image/jpeg,image/png,image/webp" (change)="selezionaDocumento($event, 'fronte')" required></label><label>Documento, retro<input type="file" accept="image/jpeg,image/png,image/webp" (change)="selezionaDocumento($event, 'retro')" required></label></div>
      </ng-container>
      <label>Email<input type="email" [(ngModel)]="credentials.email" autocomplete="email" required></label>
      <label>Password<input type="password" [(ngModel)]="credentials.password" [autocomplete]="registrazioneAttiva ? 'new-password' : 'current-password'" required></label>
      <button (click)="registrazioneAttiva ? registrati() : onLogin()">
        {{ registrazioneAttiva ? 'Registrati' : 'Accedi' }}
      </button>
      <button class="secondary" type="button" (click)="toggleRegistrazione()">
        {{ registrazioneAttiva ? 'Ho già un account' : 'Crea un account' }}
      </button>
      </div>
      <p *ngIf="messaggioErrore" class="form-message error" role="alert">{{ messaggioErrore }}</p><p *ngIf="messaggioSuccesso" class="form-message success" role="status">{{ messaggioSuccesso }}</p>
    </section>
  `,
})
export class LoginComponent {
  credentials: LoginCredentials = { email: '', password: '' };
  registrazioneAttiva = false;
  registrazione: Partial<RegistrazioneDati> = {
    nome: '', cognome: '', codice_fiscale: '', indirizzo_residenza: '', data_nascita: '',
  };
  documentoFronte: File | null = null;
  documentoRetro: File | null = null;
  messaggioErrore = '';
  messaggioSuccesso = '';
  dataMassima = new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().slice(0, 10);

  constructor(private readonly api: Api) {}

  toggleRegistrazione(): void {
    this.registrazioneAttiva = !this.registrazioneAttiva;
    this.messaggioErrore = '';
    this.messaggioSuccesso = '';
  }

  selezionaDocumento(event: Event, lato: 'fronte' | 'retro'): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    if (lato === 'fronte') this.documentoFronte = file;
    else this.documentoRetro = file;
  }

  registrati(): void {
    const dati = this.registrazione;
    if (!dati.nome || !dati.cognome || !dati.codice_fiscale || !dati.indirizzo_residenza ||
        !dati.data_nascita || !this.credentials.email || !this.credentials.password ||
        !this.documentoFronte || !this.documentoRetro) {
      this.messaggioErrore = 'Compila tutti i campi e carica fronte e retro del documento.';
      return;
    }
    const formData = new FormData();
    Object.entries({ ...dati, email: this.credentials.email, password: this.credentials.password })
      .forEach(([chiave, valore]) => formData.append(chiave, String(valore)));
    formData.append('documento_fronte', this.documentoFronte);
    formData.append('documento_retro', this.documentoRetro);
    this.api.registrati(formData).subscribe({
      next: (response) => {
        this.messaggioSuccesso = response.messaggio;
        this.registrazioneAttiva = false;
      },
      error: (err: { error?: { errore?: string } }) => {
        this.messaggioErrore = err.error?.errore ?? 'Errore durante la registrazione';
      },
    });
  }

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

export { LoginComponent as Login };