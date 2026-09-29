import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Api } from '../../services/api';

@Component({
  selector: 'app-inserisci-segnalazione',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 30px; background: #f8f9fa;">
      <h3 style="margin-top: 0;">Nuova Segnalazione</h3>

      <div style="margin-bottom: 15px;">
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Titolo (min 5 caratteri):</label>
        <input type="text" [(ngModel)]="titolo" style="width: 100%; padding: 8px; box-sizing: border-box;">
      </div>

      <div style="margin-bottom: 15px;">
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Descrizione:</label>
        <textarea [(ngModel)]="descrizione" rows="4" style="width: 100%; padding: 8px; box-sizing: border-box;"></textarea>
      </div>

      <div style="margin-bottom: 15px;">
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Quartiere:</label>
        <select [(ngModel)]="idQuartiere" style="width: 100%; padding: 8px; box-sizing: border-box;">
          <option value="" disabled selected>Seleziona un quartiere...</option>
          <option value="1">Centro Storico</option>
          <option value="2">Navigli</option>
          <option value="3">Isola</option>
          <option value="4">Bicocca</option>
          <option value="5">Lambrate</option>
          <option value="6">San Siro</option>
        </select>
      </div>

      <div style="margin-bottom: 20px;">
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Allegato (Foto/Video obbligatorio):</label>
        <input type="file" (change)="onFileSelected($event)" accept="image/*,video/*" style="width: 100%;">
      </div>

      <button (click)="invia()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Invia Segnalazione
      </button>

      <div *ngIf="messaggio" style="margin-top: 15px; padding: 10px; border-radius: 4px;"
           [ngStyle]="{'background-color': successo ? '#d4edda' : '#f8d7da', 'color': successo ? '#155724' : '#721c24'}">
        {{ messaggio }}
      </div>
    </div>
  `,
})
export class InserisciSegnalazioneComponent {
  @Output() segnalazioneCreata = new EventEmitter<void>();

  titolo = '';
  descrizione = '';
  idQuartiere = '';
  allegato: File | null = null;

  messaggio = '';
  successo = false;

  constructor(private readonly api: Api) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.allegato = file;
    }
  }

  invia(): void {
    this.messaggio = '';
    this.successo = false;

    if (!this.titolo || !this.descrizione || !this.idQuartiere || !this.allegato) {
      this.messaggio = 'Tutti i campi e l\'allegato sono obbligatori.';
      return;
    }

    const formData = new FormData();
    formData.append('titolo', this.titolo);
    formData.append('descrizione', this.descrizione);
    formData.append('id_quartiere', this.idQuartiere);
    formData.append('allegato', this.allegato);

    this.api.inviaSegnalazione(formData).subscribe({
      next: () => {
        this.successo = true;
        this.messaggio = 'Segnalazione inserita con successo!';
        this.resetForm();
        this.segnalazioneCreata.emit();
      },
      error: (err: { error?: { errore?: string } }) => {
        this.successo = false;
        this.messaggio = err.error?.errore ?? 'Errore durante l\'inserimento';
      },
    });
  }

  resetForm(): void {
    this.titolo = '';
    this.descrizione = '';
    this.idQuartiere = '';
    this.allegato = null;
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    if (fileInput) {
      fileInput.value = '';
    }
  }
}