import { ComponentFixture, TestBed } from '@angular/core/testing';
import { InserisciSegnalazione } from './inserisci-segnalazione';

describe('InserisciSegnalazione', () => {
  let component: InserisciSegnalazione;
  let fixture: ComponentFixture<InserisciSegnalazione>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InserisciSegnalazione],
    }).compileComponents();

    fixture = TestBed.createComponent(InserisciSegnalazione);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
