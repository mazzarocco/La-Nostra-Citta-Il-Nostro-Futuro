import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Segnalazione {
  id_segnalazione: number;
  titolo: string;
  quartiere: string;
  descrizione: string;
  stato: string;
  numero_sostegni: number;
  id_autore?: number;
}

export interface Profilo {
  id_utente: number;
  nome: string;
  cognome: string;
  email: string;
  codice_fiscale: string;
  indirizzo_residenza: string;
  data_nascita: string;
  ruolo: string;
  stato_account: string;
}

export interface Commento {
  id_commento: number;
  id_utente: number;
  testo: string;
  autore: string;
  data_creazione: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  ruolo: string;
}

export interface RegistrazioneDati {
  nome: string;
  cognome: string;
  email: string;
  codice_fiscale: string;
  indirizzo_residenza: string;
  data_nascita: string;
  password: string;
  documento_fronte: File;
  documento_retro: File;
}

@Injectable({ providedIn: 'root' })
export class Api {
  private readonly baseUrl =
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? 'http://localhost:5000/api'
      : '/api';

  constructor(private readonly http: HttpClient) {}

  getSegnalazioniPubbliche(): Observable<Segnalazione[]> {
    return this.http.get<Segnalazione[]>(`${this.baseUrl}/segnalazioni`);
  }

  login(credentials: LoginCredentials): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login`, credentials);
  }

  registrati(dati: FormData): Observable<{ messaggio: string }> {
    return this.http.post<{ messaggio: string }>(`${this.baseUrl}/registrazione`, dati);
  }

  inviaSegnalazione(formData: FormData): Observable<{ id_segnalazione: number }> {
    return this.http.post<{ id_segnalazione: number }>(`${this.baseUrl}/segnalazioni`, formData);
  }

  sostieniSegnalazione(id: number): Observable<{ success: boolean; id: number }> {
    return this.http.post<{ success: boolean; id: number }>(
      `${this.baseUrl}/segnalazioni/${id}/sostieni`,
      {},
    );
  }

  getProfilo(): Observable<Profilo> {
    return this.http.get<Profilo>(`${this.baseUrl}/profilo`);
  }

  aggiornaProfilo(dati: Pick<Profilo, 'nome' | 'cognome' | 'indirizzo_residenza'>): Observable<{ messaggio: string }> {
    return this.http.put<{ messaggio: string }>(`${this.baseUrl}/profilo`, dati);
  }

  eliminaAccount(): Observable<{ messaggio: string }> {
    return this.http.delete<{ messaggio: string }>(`${this.baseUrl}/profilo`);
  }

  getMieSegnalazioni(): Observable<Segnalazione[]> {
    return this.http.get<Segnalazione[]>(`${this.baseUrl}/segnalazioni/mie`);
  }

  getMieiVoti(): Observable<Segnalazione[]> {
    return this.http.get<Segnalazione[]>(`${this.baseUrl}/miei-voti`);
  }

  aggiornaSegnalazione(id: number, dati: Pick<Segnalazione, 'titolo' | 'descrizione'>): Observable<{ messaggio: string }> {
    return this.http.put<{ messaggio: string }>(`${this.baseUrl}/segnalazioni/${id}`, dati);
  }

  eliminaSegnalazione(id: number): Observable<{ messaggio: string }> {
    return this.http.delete<{ messaggio: string }>(`${this.baseUrl}/segnalazioni/${id}`);
  }

  getCommenti(id: number): Observable<Commento[]> {
    return this.http.get<Commento[]>(`${this.baseUrl}/segnalazioni/${id}/commenti`);
  }

  aggiungiCommento(id: number, testo: string): Observable<{ messaggio: string }> {
    return this.http.post<{ messaggio: string }>(`${this.baseUrl}/segnalazioni/${id}/commenti`, { testo });
  }

  getSegnalazioniComitato(): Observable<Segnalazione[]> {
    return this.http.get<Segnalazione[]>(`${this.baseUrl}/comitato/segnalazioni`);
  }

  modificaCommento(id: number, testo: string): Observable<{ messaggio: string }> {
    return this.http.put<{ messaggio: string }>(`${this.baseUrl}/commenti/${id}`, { testo });
  }

  eliminaCommento(id: number): Observable<{ messaggio: string }> {
    return this.http.delete<{ messaggio: string }>(`${this.baseUrl}/commenti/${id}`);
  }

  getUtentiInVerifica(): Observable<Profilo[]> {
    return this.http.get<Profilo[]>(`${this.baseUrl}/comitato/utenti-in-verifica`);
  }

  verificaUtente(id: number, stato: 'ATTIVO' | 'RIFIUTATO'): Observable<{ messaggio: string }> {
    return this.http.post<{ messaggio: string }>(`${this.baseUrl}/comitato/utenti/${id}/verifica`, { stato });
  }

  analizzaSegnalazione(id: number): Observable<{ categoria: string; indice_urgenza: number; nota: string }> {
    return this.http.post<{ categoria: string; indice_urgenza: number; nota: string }>(`${this.baseUrl}/comitato/segnalazioni/${id}/analisi`, {});
  }
}
