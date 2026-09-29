import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

export interface Segnalazione {
  id_segnalazione: number;
  titolo: string;
  quartiere: string;
  descrizione: string;
  stato: string;
  numero_sostegni: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  ruolo: string;
}

@Injectable({ providedIn: 'root' })
export class Api {
  getSegnalazioniPubbliche(): Observable<Segnalazione[]> {
    return of([
      {
        id_segnalazione: 1,
        titolo: 'Buche in via Roma',
        quartiere: 'Centro',
        descrizione: 'Numerose buche e dissesto nella carreggiata del tratto principale.',
        stato: 'Aperta',
        numero_sostegni: 12,
      },
      {
        id_segnalazione: 2,
        titolo: 'Illuminazione insufficiente',
        quartiere: 'San Paolo',
        descrizione: 'Lampioni non funzionanti nel parcheggio pubblico del quartiere.',
        stato: 'In lavorazione',
        numero_sostegni: 7,
      },
    ]);
  }

  login(credentials: LoginCredentials): Observable<LoginResponse> {
    if (credentials.email === 'admin@demo.it' && credentials.password === 'admin123') {
      return of({ token: 'mock-jwt-token', ruolo: 'admin' });
    }

    return of({ token: 'mock-jwt-token', ruolo: 'cittadino' });
  }

  inviaSegnalazione(formData: FormData): Observable<{ success: boolean; message: string }> {
    return of({ success: true, message: 'Segnalazione inserita con successo' });
  }

  sostieniSegnalazione(id: number): Observable<{ success: boolean; id: number }> {
    return of({ success: true, id });
  }
}
