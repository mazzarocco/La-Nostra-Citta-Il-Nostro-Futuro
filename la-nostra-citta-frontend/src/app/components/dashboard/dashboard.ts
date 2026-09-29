import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Api, Segnalazione } from '../../services/api';
import { InserisciSegnalazioneComponent } from '../inserisci-segnalazione/inserisci-segnalazione';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, InserisciSegnalazioneComponent],
  template: `
    <app-inserisci-segnalazione (segnalazioneCreata)="caricaSegnalazioni()"></app-inserisci-segnalazione>

    <h2>Segnalazioni Pubbliche Recenti</h2>
    <div *ngIf="segnalazioni.length === 0" style="color: #666; font-style: italic;">
      Nessuna segnalazione presente.
    </div>

    <div *ngFor="let seg of segnalazioni" style="border: 1px solid #ccc; border-radius: 8px; margin-bottom: 15px; padding: 15px; background: white;">
      <h3 style="margin-top: 0; color: #0056b3;">{{ seg.titolo }}</h3>
      <div style="font-size: 0.9em; color: #666; margin-bottom: 10px;">
        <strong>Quartiere:</strong> {{ seg.quartiere }} |
        <strong>Stato:</strong> <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px;">{{ seg.stato }}</span>
      </div>
      <p style="line-height: 1.5;">{{ seg.descrizione }}</p>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
        <span style="font-weight: bold;">Sostegni: {{ seg.numero_sostegni }}</span>
        <button (click)="sostieni(seg.id_segnalazione)" style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Sostieni questa causa
        </button>
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  segnalazioni: Segnalazione[] = [];

  constructor(private readonly api: Api) {}

  ngOnInit(): void {
    this.caricaSegnalazioni();
  }

  caricaSegnalazioni(): void {
    this.api.getSegnalazioniPubbliche().subscribe((data: Segnalazione[]) => {
      this.segnalazioni = data;
    });
  }

  sostieni(id: number): void {
    this.api.sostieniSegnalazione(id).subscribe({
      next: () => {
        alert('Sostegno aggiunto!');
        this.caricaSegnalazioni();
      },
      error: (err: { error?: { errore?: string } }) => {
        alert(err.error?.errore ?? 'Si è verificato un errore durante il sostegno.');
      },
    });
  }
}