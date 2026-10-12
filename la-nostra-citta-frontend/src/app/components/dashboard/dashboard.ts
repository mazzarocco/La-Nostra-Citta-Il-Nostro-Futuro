import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Api, Commento, Profilo, Segnalazione } from '../../services/api';
import { InserisciSegnalazioneComponent } from '../inserisci-segnalazione/inserisci-segnalazione';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, InserisciSegnalazioneComponent],
  template: `
    <section class="dashboard-head">
      <div><p class="eyebrow">Spazio civico</p><h2>Proposte per Milano</h2><p>Condividi problemi, idee e informazioni utili per il quartiere.</p></div>
      <nav aria-label="Sezioni personali"><button [attr.aria-current]="vista === 'home' ? 'page' : null" (click)="cambiaVista('home')">Esplora</button><button [attr.aria-current]="vista === 'mie' ? 'page' : null" (click)="cambiaVista('mie')">Le mie proposte</button><button [attr.aria-current]="vista === 'voti' ? 'page' : null" (click)="cambiaVista('voti')">I miei voti</button><button [attr.aria-current]="vista === 'profilo' ? 'page' : null" (click)="cambiaVista('profilo')">Profilo</button><button *ngIf="ruolo === 'COMITATO'" [attr.aria-current]="vista === 'comitato' ? 'page' : null" (click)="cambiaVista('comitato')">Comitato</button></nav>
    </section>
    <app-inserisci-segnalazione *ngIf="vista === 'home'" (segnalazioneCreata)="caricaSegnalazioni()"></app-inserisci-segnalazione>
    <p class="notice" *ngIf="messaggio" role="status">{{ messaggio }}</p>

    <section *ngIf="vista === 'home' || vista === 'comitato' || vista === 'mie' || vista === 'voti'" aria-live="polite">
      <h2>{{ titoloVista }}</h2><p *ngIf="listaAttiva.length === 0">Non ci sono ancora proposte in questa sezione.</p>
      <article *ngFor="let seg of listaAttiva" class="proposal">
        <div class="proposal-meta"><span>{{ seg.quartiere || 'Quartiere non indicato' }}</span><span>{{ seg.stato || 'Pubblicata' }}</span></div>
        <h3>{{ seg.titolo }}</h3><p>{{ seg.descrizione }}</p>
        <footer><strong>{{ seg.numero_sostegni || 0 }} sostegni</strong><button *ngIf="vista === 'home'" (click)="sostieni(seg.id_segnalazione)">Sostieni</button><button (click)="apriCommenti(seg.id_segnalazione)">Commenti</button><button *ngIf="vista === 'mie' || ruolo === 'COMITATO'" (click)="modificaSegnalazione(seg)">Modifica</button><button *ngIf="vista === 'mie' || ruolo === 'COMITATO'" class="danger" (click)="elimina(seg.id_segnalazione)">Elimina</button><button *ngIf="vista === 'comitato'" (click)="analizza(seg.id_segnalazione)">Analizza con IA</button></footer>
        <div *ngIf="editingId === seg.id_segnalazione" class="edit-form"><label>Titolo<input [(ngModel)]="editTitolo"></label><label>Descrizione<textarea [(ngModel)]="editDescrizione" rows="4"></textarea></label><button (click)="salvaModifica(seg.id_segnalazione)">Salva</button><button class="secondary" (click)="editingId = null">Annulla</button></div>
        <p *ngIf="analisi[seg.id_segnalazione]" class="analysis" role="status">IA: {{ analisi[seg.id_segnalazione].categoria }} · urgenza {{ analisi[seg.id_segnalazione].indice_urgenza }}/100</p>
        <div *ngIf="commentiAperti === seg.id_segnalazione" class="comments"><div *ngFor="let commento of commenti" class="comment"><strong>{{ commento.autore }}</strong><span>{{ commento.testo }}</span><button *ngIf="commento.id_utente === profilo?.id_utente || ruolo === 'COMITATO'" class="comment-action" (click)="eliminaCommento(commento.id_commento, seg.id_segnalazione)" aria-label="Elimina commento">Elimina</button></div><label>Nuovo commento<textarea [(ngModel)]="nuovoCommento" rows="2"></textarea></label><button (click)="commenta(seg.id_segnalazione)">Pubblica commento</button></div>
      </article>
    </section>
    <section *ngIf="vista === 'profilo'" class="profile"><h2>Il tuo profilo</h2><p *ngIf="profilo">Stato account: {{ profilo.stato_account }}</p><label>Nome<input [(ngModel)]="modifica.nome"></label><label>Cognome<input [(ngModel)]="modifica.cognome"></label><label>Indirizzo di residenza<input [(ngModel)]="modifica.indirizzo_residenza"></label><p class="privacy">Email e codice fiscale restano privati e non sono modificabili da questa pagina.</p><button (click)="salvaProfilo()">Salva modifiche</button><button class="danger" (click)="eliminaAccount()">Elimina account</button></section>
  `,
})
export class DashboardComponent implements OnInit {
  segnalazioni: Segnalazione[] = [];
  mie: Segnalazione[] = [];
  voti: Segnalazione[] = [];
  comitato: Segnalazione[] = [];
  profilo: Profilo | null = null;
  modifica = { nome: '', cognome: '', indirizzo_residenza: '' };
  commenti: Commento[] = [];
  commentiAperti: number | null = null;
  nuovoCommento = '';
  vista = 'home';
  ruolo = typeof localStorage === 'undefined' ? '' : localStorage.getItem('user_role') ?? '';
  messaggio = '';
  editingId: number | null = null;
  editTitolo = '';
  editDescrizione = '';
  analisi: Record<number, { categoria: string; indice_urgenza: number }> = {};

  constructor(private readonly api: Api) {}

  ngOnInit(): void {
    this.caricaSegnalazioni();
    this.api.getProfilo().subscribe({ next: profilo => { this.profilo = profilo; this.modifica = { nome: profilo.nome, cognome: profilo.cognome, indirizzo_residenza: profilo.indirizzo_residenza }; } });
    this.api.getMieSegnalazioni().subscribe({ next: dati => this.mie = dati });
    this.api.getMieiVoti().subscribe({ next: dati => this.voti = dati });
    if (this.ruolo === 'COMITATO') this.api.getSegnalazioniComitato().subscribe({ next: dati => this.comitato = dati });
  }

  get titoloVista(): string { return this.vista === 'mie' ? 'Le mie proposte' : this.vista === 'voti' ? 'Proposte sostenute' : this.vista === 'comitato' ? 'Controllo del comitato' : 'Segnalazioni della comunità'; }
  get listaAttiva(): Segnalazione[] { return this.vista === 'mie' ? this.mie : this.vista === 'voti' ? this.voti : this.vista === 'comitato' ? this.comitato : this.segnalazioni; }
  cambiaVista(vista: string): void { this.vista = vista; this.messaggio = ''; }

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
        this.messaggio = err.error?.errore ?? 'Si è verificato un errore durante il sostegno.';
      },
    });
  }

  apriCommenti(id: number): void { this.commentiAperti = this.commentiAperti === id ? null : id; if (this.commentiAperti) this.api.getCommenti(id).subscribe({ next: dati => this.commenti = dati }); }
  commenta(id: number): void { if (!this.nuovoCommento.trim()) return; this.api.aggiungiCommento(id, this.nuovoCommento).subscribe({ next: () => { this.nuovoCommento = ''; this.apriCommenti(id); } }); }
  elimina(id: number): void { if (!confirm('Eliminare questa proposta?')) return; this.api.eliminaSegnalazione(id).subscribe({ next: () => { this.messaggio = 'Proposta eliminata.'; this.caricaSegnalazioni(); this.mie = this.mie.filter(item => item.id_segnalazione !== id); } }); }
  modificaSegnalazione(segnalazione: Segnalazione): void { this.editingId = segnalazione.id_segnalazione; this.editTitolo = segnalazione.titolo; this.editDescrizione = segnalazione.descrizione; }
  salvaModifica(id: number): void { this.api.aggiornaSegnalazione(id, { titolo: this.editTitolo, descrizione: this.editDescrizione }).subscribe({ next: () => { this.editingId = null; this.messaggio = 'Proposta aggiornata.'; this.caricaSegnalazioni(); this.api.getMieSegnalazioni().subscribe({ next: dati => this.mie = dati }); } }); }
  analizza(id: number): void { this.api.analizzaSegnalazione(id).subscribe({ next: risultato => this.analisi = { ...this.analisi, [id]: risultato }, error: () => this.messaggio = 'Analisi non disponibile.' }); }
  eliminaCommento(id: number, segnalazioneId: number): void { this.api.eliminaCommento(id).subscribe({ next: () => this.apriCommenti(segnalazioneId) }); }
  salvaProfilo(): void { this.api.aggiornaProfilo(this.modifica).subscribe({ next: response => this.messaggio = response.messaggio }); }
  eliminaAccount(): void { if (!confirm('Eliminare definitivamente il tuo account?')) return; this.api.eliminaAccount().subscribe({ next: () => { localStorage.clear(); window.location.reload(); } }); }
}