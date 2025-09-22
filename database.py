"""
Modulo per la gestione del database PostgreSQL
"""

import psycopg2
import hashlib
from datetime import datetime, timedelta
from models import Libro


class DatabaseManager:
    """Classe per gestire le operazioni del database"""

    def __init__(self):
        """Inizializza la connessione al database"""
        try:
            self.conn = psycopg2.connect(
                dbname='biblioteca',
                user='postgres',
                password='a',  # Password corretta fornita dall'utente
                host='localhost',
                port='5432'
            )
            self.conn.autocommit = False
            self.create_tables()
        except Exception as e:
            print(f"Errore di connessione al database: {e}")
            print("Assicurati che il database 'biblioteca' esista su PostgreSQL.")
            raise

    def create_tables(self):
        """Crea le tabelle del database se non esistono"""
        cursor = self.conn.cursor()

        try:
            # Tabelle esistenti per l'autenticazione
            cursor.execute('''CREATE TABLE IF NOT EXISTS ruoli (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(50) UNIQUE NOT NULL
            )''')

            # Nuova tabella per le città
            cursor.execute('''CREATE TABLE IF NOT EXISTS citta (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                regione VARCHAR(255)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS biblioteche (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                indirizzo VARCHAR(255),
                citta_id INTEGER REFERENCES citta(id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS librerie (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                indirizzo VARCHAR(255),
                citta_id INTEGER REFERENCES citta(id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                nome_utente VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(100) NOT NULL,
                cognome VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                ruolo_id INTEGER REFERENCES ruoli(id),
                biblioteca_id INTEGER REFERENCES biblioteche(id),
                libreria_id INTEGER REFERENCES librerie(id),
                data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Tabelle per i libri
            cursor.execute('''CREATE TABLE IF NOT EXISTS autori (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS generi (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS libri (
                id SERIAL PRIMARY KEY,
                titolo VARCHAR(255) NOT NULL,
                autore_id INTEGER REFERENCES autori(id),
                genere_id INTEGER REFERENCES generi(id),
                anno_pubblicazione INTEGER,
                numero_pagine INTEGER,
                prezzo_nuovo DECIMAL(10,2),
                prezzo_usato DECIMAL(10,2),
                descrizione TEXT,
                isbn VARCHAR(20) UNIQUE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS libri_disponibili (
                id SERIAL PRIMARY KEY,
                libro_id INTEGER REFERENCES libri(id) UNIQUE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS libri_prestati (
                id SERIAL PRIMARY KEY,
                libro_id INTEGER REFERENCES libri(id) UNIQUE
            )''')

            # Nuove tabelle per il sistema di acquisti
            cursor.execute('''CREATE TABLE IF NOT EXISTS inventario_librerie (
                id SERIAL PRIMARY KEY,
                libreria_id INTEGER REFERENCES librerie(id),
                libro_id INTEGER REFERENCES libri(id),
                copie_nuove INTEGER DEFAULT 0,
                copie_usate INTEGER DEFAULT 0,
                copie_vendute INTEGER DEFAULT 0,
                UNIQUE(libreria_id, libro_id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS indirizzi_utente (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                nome VARCHAR(100) NOT NULL,
                cognome VARCHAR(100) NOT NULL,
                indirizzo VARCHAR(255) NOT NULL,
                citta VARCHAR(100) NOT NULL,
                cap VARCHAR(10) NOT NULL,
                provincia VARCHAR(50) NOT NULL,
                telefono VARCHAR(20),
                is_default BOOLEAN DEFAULT FALSE,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS metodi_pagamento (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('carta_credito', 'carta_debito', 'paypal')),
                numero_carta VARCHAR(255), -- criptato
                scadenza DATE,
                titolare VARCHAR(100),
                is_default BOOLEAN DEFAULT FALSE,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS acquisti (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                libreria_id INTEGER REFERENCES librerie(id),
                indirizzo_consegna_id INTEGER REFERENCES indirizzi_utente(id),
                metodo_pagamento_id INTEGER REFERENCES metodi_pagamento(id),
                totale DECIMAL(10,2) NOT NULL,
                tasse DECIMAL(10,2) DEFAULT 0,
                sconto DECIMAL(10,2) DEFAULT 0,
                stato VARCHAR(30) DEFAULT 'in_attesa' CHECK (stato IN ('in_attesa', 'confermato', 'in_preparazione', 'spedito', 'consegnato', 'cancellato')),
                tipo_consegna VARCHAR(20) DEFAULT 'negozio' CHECK (tipo_consegna IN ('negozio', 'casa')),
                note TEXT,
                data_acquisto TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_consegna_prevista TIMESTAMP,
                data_consegna_effettiva TIMESTAMP
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS dettagli_acquisto (
                id SERIAL PRIMARY KEY,
                acquisto_id INTEGER REFERENCES acquisti(id),
                libro_id INTEGER REFERENCES libri(id),
                libreria_id INTEGER REFERENCES librerie(id),
                quantita INTEGER NOT NULL,
                condizione VARCHAR(10) NOT NULL CHECK (condizione IN ('nuovo', 'usato')),
                prezzo_unitario DECIMAL(10,2) NOT NULL,
                sconto DECIMAL(10,2) DEFAULT 0,
                totale DECIMAL(10,2) NOT NULL
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS feedback_libri (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                libro_id INTEGER REFERENCES libri(id),
                acquisto_id INTEGER REFERENCES acquisti(id),
                valutazione INTEGER CHECK (valutazione >= 1 AND valutazione <= 5),
                commento TEXT,
                utile INTEGER DEFAULT 0,
                non_utile INTEGER DEFAULT 0,
                data_recensione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                moderato BOOLEAN DEFAULT FALSE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS consegne (
                id SERIAL PRIMARY KEY,
                acquisto_id INTEGER REFERENCES acquisti(id),
                corriere VARCHAR(100),
                numero_tracking VARCHAR(100) UNIQUE,
                stato VARCHAR(30) DEFAULT 'in_preparazione' CHECK (stato IN ('in_preparazione', 'spedito', 'in_transito', 'consegnato', 'ritornato')),
                indirizzo_consegna TEXT,
                data_spedizione TIMESTAMP,
                data_consegna_prevista TIMESTAMP,
                data_consegna_effettiva TIMESTAMP,
                note TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS richieste_bibliotecari (
                id SERIAL PRIMARY KEY,
                bibliotecario_id INTEGER REFERENCES utenti(id),
                tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('prenotazione', 'lista_attesa', 'restituzione', 'altro')),
                descrizione TEXT NOT NULL,
                priorita VARCHAR(10) DEFAULT 'normale' CHECK (priorita IN ('bassa', 'normale', 'alta', 'urgente')),
                stato VARCHAR(20) DEFAULT 'aperta' CHECK (stato IN ('aperta', 'in_lavorazione', 'risolta', 'chiusa')),
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_risoluzione TIMESTAMP
            )''')

            # Migrazioni per aggiornare lo schema esistente
            cursor.execute('''ALTER TABLE libri ADD COLUMN IF NOT EXISTS prezzo_nuovo DECIMAL(10,2)''')
            cursor.execute('''ALTER TABLE libri ADD COLUMN IF NOT EXISTS prezzo_usato DECIMAL(10,2)''')
            cursor.execute('''ALTER TABLE libri ADD COLUMN IF NOT EXISTS descrizione TEXT''')
            cursor.execute('''ALTER TABLE libri ADD COLUMN IF NOT EXISTS isbn VARCHAR(20)''')

            # Aggiorna prezzi esistenti se NULL
            cursor.execute('''UPDATE libri SET prezzo_nuovo = prezzo WHERE prezzo_nuovo IS NULL''')
            cursor.execute('''UPDATE libri SET prezzo_usato = prezzo * 0.7 WHERE prezzo_usato IS NULL''')  # usato = 70% del prezzo nuovo

            cursor.execute('''ALTER TABLE biblioteche ADD COLUMN IF NOT EXISTS citta_id INTEGER REFERENCES citta(id)''')
            cursor.execute('''ALTER TABLE librerie ADD COLUMN IF NOT EXISTS citta_id INTEGER REFERENCES citta(id)''')

            # Aggiorna dati esistenti se citta_id è NULL (per database esistenti)
            cursor.execute('''UPDATE biblioteche SET citta_id = (SELECT id FROM citta WHERE nome = 'Roma' LIMIT 1) WHERE citta_id IS NULL''')
            cursor.execute('''UPDATE librerie SET citta_id = (SELECT id FROM citta WHERE nome = 'Roma' LIMIT 1) WHERE citta_id IS NULL''')

            # Inserisci ruoli di default se non esistono
            cursor.execute("INSERT INTO ruoli (nome) VALUES ('bibliotecario') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO ruoli (nome) VALUES ('libraio') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO ruoli (nome) VALUES ('utente') ON CONFLICT (nome) DO NOTHING")

            # Inserisci città di default se non esistono
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Milano', 'Lombardia') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Roma', 'Lazio') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Torino', 'Piemonte') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Firenze', 'Toscana') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Napoli', 'Campania') ON CONFLICT (nome) DO NOTHING")
            cursor.execute("INSERT INTO citta (nome, regione) VALUES ('Bologna', 'Emilia-Romagna') ON CONFLICT (nome) DO NOTHING")

            # Migrazioni per aggiornare lo schema esistente
            cursor.execute('''ALTER TABLE biblioteche ADD COLUMN IF NOT EXISTS citta_id INTEGER REFERENCES citta(id)''')
            cursor.execute('''ALTER TABLE librerie ADD COLUMN IF NOT EXISTS citta_id INTEGER REFERENCES citta(id)''')

            # Aggiorna dati esistenti se citta_id è NULL (per database esistenti)
            cursor.execute('''UPDATE biblioteche SET citta_id = (SELECT id FROM citta WHERE nome = 'Roma' LIMIT 1) WHERE citta_id IS NULL''')
            cursor.execute('''UPDATE librerie SET citta_id = (SELECT id FROM citta WHERE nome = 'Roma' LIMIT 1) WHERE citta_id IS NULL''')

            # Inserisci biblioteche di default se non esistono
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Centrale', 'Via Roma 1, Milano', c.id FROM citta c WHERE c.nome = 'Milano' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Comunale', 'Piazza Garibaldi 2, Roma', c.id FROM citta c WHERE c.nome = 'Roma' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Nazionale', 'Via Nazionale 1, Roma', c.id FROM citta c WHERE c.nome = 'Roma' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Universitaria', 'Via Università 2, Milano', c.id FROM citta c WHERE c.nome = 'Milano' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Civica', 'Piazza Dante 3, Firenze', c.id FROM citta c WHERE c.nome = 'Firenze' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) SELECT 'Biblioteca Provinciale', 'Via Garibaldi 4, Napoli', c.id FROM citta c WHERE c.nome = 'Napoli' ON CONFLICT DO NOTHING")

            # Inserisci librerie di default se non esistono
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'Mondadori', 'Via dei Libri 1, Roma', c.id FROM citta c WHERE c.nome = 'Roma' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'Feltrinelli', 'Corso Italia 2, Milano', c.id FROM citta c WHERE c.nome = 'Milano' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'IBS', 'Via Shopping 3, Firenze', c.id FROM citta c WHERE c.nome = 'Firenze' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'Libreria Universitaria', 'Via Studenti 4, Napoli', c.id FROM citta c WHERE c.nome = 'Napoli' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'Libreria del Centro', 'Piazza Duomo 5, Bologna', c.id FROM citta c WHERE c.nome = 'Bologna' ON CONFLICT DO NOTHING")
            cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) SELECT 'Libreria Moderna', 'Via Moderna 6, Torino', c.id FROM citta c WHERE c.nome = 'Torino' ON CONFLICT DO NOTHING")

            # Nuove tabelle per le funzionalità utente
            cursor.execute('''CREATE TABLE IF NOT EXISTS prenotazioni (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                libro_id INTEGER REFERENCES libri(id),
                data_prenotazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_scadenza TIMESTAMP,
                stato VARCHAR(20) DEFAULT 'attiva' CHECK (stato IN ('attiva', 'completata', 'scaduta'))
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS liste_attesa (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                libro_id INTEGER REFERENCES libri(id),
                data_richiesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                posizione INTEGER,
                stato VARCHAR(20) DEFAULT 'attiva' CHECK (stato IN ('attiva', 'notificato', 'completata'))
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS libri_salvati (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                libro_id INTEGER REFERENCES libri(id),
                data_salvataggio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(utente_id, libro_id)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS notifiche (
                id SERIAL PRIMARY KEY,
                utente_id INTEGER REFERENCES utenti(id),
                messaggio TEXT NOT NULL,
                tipo VARCHAR(50) DEFAULT 'generale',
                letta BOOLEAN DEFAULT FALSE,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            self.conn.commit()
            cursor.close()

            # Popola il database con dati di esempio
            self.populate_sample_data_if_empty()

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            raise e

    def populate_sample_data_if_empty(self):
        """Popola il database con dati di esempio solo se è vuoto"""
        try:
            cursor = self.conn.cursor()

            # Verifica se ci sono già utenti nel database
            cursor.execute("SELECT COUNT(*) FROM utenti")
            user_count = cursor.fetchone()[0]

            if user_count > 0:
                print("Database già popolato con dati esistenti.")
                cursor.close()
                return

            # Se il database è vuoto, popola con dati di esempio
            print("Database vuoto. Popolamento con dati di esempio...")

            # Aggiungi biblioteche di esempio con riferimento alla città
            biblioteche = [
                ('Biblioteca Nazionale', 'Via Nazionale 1, Roma', 'Roma'),
                ('Biblioteca Universitaria', 'Via Università 2, Milano', 'Milano'),
                ('Biblioteca Civica', 'Piazza Dante 3, Firenze', 'Firenze'),
                ('Biblioteca Provinciale', 'Via Garibaldi 4, Napoli', 'Napoli')
            ]

            for nome, indirizzo, citta_nome in biblioteche:
                cursor.execute("""
                    INSERT INTO biblioteche (nome, indirizzo, citta_id)
                    SELECT %s, %s, c.id FROM citta c WHERE c.nome = %s
                    ON CONFLICT DO NOTHING
                """, (nome, indirizzo, citta_nome))

            # Aggiungi librerie di esempio con riferimento alla città
            librerie = [
                ('Mondadori', 'Via dei Libri 1, Roma', 'Roma'),
                ('Feltrinelli', 'Corso Italia 2, Milano', 'Milano'),
                ('IBS', 'Via Shopping 3, Firenze', 'Firenze'),
                ('Libreria Universitaria', 'Via Studenti 4, Napoli', 'Napoli'),
                ('Libreria del Centro', 'Piazza Duomo 5, Bologna', 'Bologna'),
                ('Libreria Moderna', 'Via Moderna 6, Torino', 'Torino')
            ]

            for nome, indirizzo, citta_nome in librerie:
                cursor.execute("""
                    INSERT INTO librerie (nome, indirizzo, citta_id)
                    SELECT %s, %s, c.id FROM citta c WHERE c.nome = %s
                    ON CONFLICT DO NOTHING
                """, (nome, indirizzo, citta_nome))

            # Aggiungi utenti di esempio
            utenti = [
                # Bibliotecari
                ('mario.rossi@email.com', 'mario_bib', 'Mario', 'Rossi', 'password123', 'bibliotecario', 1, None),
                ('giulia.verdi@email.com', 'giulia_bib', 'Giulia', 'Verdi', 'password123', 'bibliotecario', 2, None),
                ('luca.bianchi@email.com', 'luca_bib', 'Luca', 'Bianchi', 'password123', 'bibliotecario', 3, None),

                # Librai
                ('anna.neri@email.com', 'anna_lib', 'Anna', 'Neri', 'password123', 'libraio', None, 1),
                ('franco.gallo@email.com', 'franco_lib', 'Franco', 'Gallo', 'password123', 'libraio', None, 2),
                ('sara.moro@email.com', 'sara_lib', 'Sara', 'Moro', 'password123', 'libraio', None, 3),

                # Utenti normali (studenti)
                ('piero.amendola@email.com', 'piero_user', 'Piero', 'Amendola', 'password123', 'utente', None, None),
                ('marco.tosi@email.com', 'marco_user', 'Marco', 'Tosi', 'password123', 'utente', None, None),
                ('elena.fini@email.com', 'elena_user', 'Elena', 'Fini', 'password123', 'utente', None, None),
                ('giovanni.roma@email.com', 'giovanni_user', 'Giovanni', 'Roma', 'password123', 'utente', None, None),
                ('sofia.luna@email.com', 'sofia_user', 'Sofia', 'Luna', 'password123', 'utente', None, None)
            ]

            for email, username, nome, cognome, password, ruolo, bib_id, lib_id in utenti:
                password_hash = self.hash_password(password)
                cursor.execute("""
                    INSERT INTO utenti (email, nome_utente, nome, cognome, password_hash, ruolo_id, biblioteca_id, libreria_id)
                    SELECT %s, %s, %s, %s, %s, r.id, %s, %s
                    FROM ruoli r WHERE r.nome = %s
                    ON CONFLICT (email) DO NOTHING
                """, (email, username, nome, cognome, password_hash, bib_id, lib_id, ruolo))

            self.conn.commit()
            cursor.close()
            print("Database popolato con dati di esempio per i test.")

        except Exception as e:
            print(f"Errore durante la popolazione del database: {str(e)}")
            self.conn.rollback()
            cursor.close()

    def hash_password(self, password):
        """Hash della password usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    # Metodi per la gestione delle città
    def get_citta(self):
        """Restituisce la lista delle città"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome, regione FROM citta ORDER BY nome")
            citta = cursor.fetchall()
            cursor.close()
            return citta
        except Exception as e:
            cursor.close()
            return []

    def get_biblioteche_by_citta(self, citta_id):
        """Restituisce la lista delle biblioteche per una città specifica"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome FROM biblioteche WHERE citta_id = %s ORDER BY nome", (citta_id,))
            biblioteche = cursor.fetchall()
            cursor.close()
            return biblioteche
        except Exception as e:
            cursor.close()
            return []

    def get_librerie_by_citta(self, citta_id):
        """Restituisce la lista delle librerie per una città specifica"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome FROM librerie WHERE citta_id = %s ORDER BY nome", (citta_id,))
            librerie = cursor.fetchall()
            cursor.close()
            return librerie
        except Exception as e:
            cursor.close()
            return []

    # Metodi per la gestione delle strutture
    def get_biblioteche(self):
        """Restituisce la lista delle biblioteche"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome FROM biblioteche ORDER BY nome")
            biblioteche = cursor.fetchall()
            cursor.close()
            return biblioteche
        except Exception as e:
            cursor.close()
            return []

    def get_librerie(self):
        """Restituisce la lista delle librerie"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome FROM librerie ORDER BY nome")
            librerie = cursor.fetchall()
            cursor.close()
            return librerie
        except Exception as e:
            cursor.close()
            return []

    # Metodi per la gestione degli utenti
    def registra_utente(self, email, nome_utente, nome, cognome, password, ruolo, struttura_id=None):
        """Registra un nuovo utente nel database"""
        try:
            cursor = self.conn.cursor()
            password_hash = self.hash_password(password)

            # Ottieni l'ID del ruolo
            cursor.execute("SELECT id FROM ruoli WHERE nome = %s", (ruolo,))
            ruolo_id = cursor.fetchone()
            if not ruolo_id:
                return False, "Ruolo non valido"

            ruolo_id = ruolo_id[0]

            # Prepara i dati per l'inserimento
            if ruolo == 'bibliotecario':
                query = """INSERT INTO utenti (email, nome_utente, nome, cognome, password_hash, ruolo_id, biblioteca_id)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                params = (email, nome_utente, nome, cognome, password_hash, ruolo_id, struttura_id)
            elif ruolo == 'libraio':
                query = """INSERT INTO utenti (email, nome_utente, nome, cognome, password_hash, ruolo_id, libreria_id)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                params = (email, nome_utente, nome, cognome, password_hash, ruolo_id, struttura_id)
            else:  # utente normale
                query = """INSERT INTO utenti (email, nome_utente, nome, cognome, password_hash, ruolo_id)
                          VALUES (%s, %s, %s, %s, %s, %s)"""
                params = (email, nome_utente, nome, cognome, password_hash, ruolo_id)

            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
            return True, "Registrazione completata con successo"
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            cursor.close()
            if 'email' in str(e):
                return False, "Email già registrata"
            elif 'nome_utente' in str(e):
                return False, "Nome utente già esistente"
            else:
                return False, "Errore di integrità dei dati"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore durante la registrazione: {str(e)}"

    def login(self, email_utente, password):
        """Effettua il login dell'utente"""
        try:
            cursor = self.conn.cursor()
            password_hash = self.hash_password(password)

            # Cerca l'utente per email o nome utente
            cursor.execute("""
                SELECT u.id, u.email, u.nome_utente, u.nome, u.cognome, r.nome as ruolo,
                       b.nome as biblioteca, l.nome as libreria
                FROM utenti u
                JOIN ruoli r ON u.ruolo_id = r.id
                LEFT JOIN biblioteche b ON u.biblioteca_id = b.id
                LEFT JOIN librerie l ON u.libreria_id = l.id
                WHERE (u.email = %s OR u.nome_utente = %s) AND u.password_hash = %s
            """, (email_utente, email_utente, password_hash))

            user = cursor.fetchone()
            cursor.close()

            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'nome_utente': user[2],
                    'nome': user[3],
                    'cognome': user[4],
                    'ruolo': user[5],
                    'biblioteca': user[6],
                    'libreria': user[7]
                }
            else:
                return None
        except Exception as e:
            cursor.close()
            return None

    # Metodi per la gestione dei libri
    def load_libri(self):
        """Carica tutti i libri dal database"""
        cursor = self.conn.cursor()
        cursor.execute('''SELECT l.titolo, a.nome, g.nome, l.anno_pubblicazione, l.numero_pagine, l.prezzo,
                                 l.prezzo_nuovo, l.prezzo_usato, l.descrizione, l.isbn,
                                 CASE WHEN ld.libro_id IS NOT NULL THEN TRUE ELSE FALSE END as disponibile
                          FROM libri l
                          JOIN autori a ON l.autore_id = a.id
                          JOIN generi g ON l.genere_id = g.id
                          LEFT JOIN libri_disponibili ld ON l.id = ld.libro_id''')
        rows = cursor.fetchall()
        libri = []
        for row in rows:
            libro = Libro(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
            libro.disponibile = bool(row[10])
            libri.append(libro)
        cursor.close()
        print(f"Caricati {len(libri)} libri dal database PostgreSQL.")
        # Se il DB è vuoto, aggiungi libri di default
        if not libri:
            default_libri = [
                Libro("Lion King", "Disney", "Animazione", 1994, 88, 19.99, 19.99, 13.99, "Un classico Disney sulla savana africana", "978-88-04-58031-4"),
                Libro("Il piccolo principe", "Antoine de Saint-Exupéry", "Narrativa", 1943, 96, 12.99, 12.99, 9.09, "Una storia poetica sulla vita e l'amicizia", "978-88-04-58032-1"),
                Libro("1984", "George Orwell", "Distopia", 1949, 328, 15.99, 15.99, 11.19, "Un romanzo distopico sulla sorveglianza totale", "978-88-04-58033-8")
            ]
            for libro in default_libri:
                self.save_libro(libro)
            libri = default_libri
        return libri

    def save_libro(self, libro):
        """Salva un libro nel database"""
        cursor = self.conn.cursor()
        # Inserisci autore se non esiste
        cursor.execute('INSERT INTO autori (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING', (libro.autore,))
        cursor.execute('SELECT id FROM autori WHERE nome = %s', (libro.autore,))
        autore_id = cursor.fetchone()[0]
        # Inserisci genere se non esiste
        cursor.execute('INSERT INTO generi (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING', (libro.genere,))
        cursor.execute('SELECT id FROM generi WHERE nome = %s', (libro.genere,))
        genere_id = cursor.fetchone()[0]
        # Inserisci libro
        cursor.execute('INSERT INTO libri (titolo, autore_id, genere_id, anno_pubblicazione, numero_pagine, prezzo, prezzo_nuovo, prezzo_usato, descrizione, isbn) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (libro.titolo, autore_id, genere_id, libro.anno_pubblicazione, libro.numero_pagine, libro.prezzo, libro.prezzo_nuovo, libro.prezzo_usato, libro.descrizione, libro.isbn))
        cursor.execute('SELECT id FROM libri WHERE titolo = %s', (libro.titolo,))
        libro_id = cursor.fetchone()[0]
        # Inserisci in disponibili se disponibile
        if libro.disponibile:
            cursor.execute('INSERT INTO libri_disponibili (libro_id) VALUES (%s)', (libro_id,))
        else:
            cursor.execute('INSERT INTO libri_prestati (libro_id) VALUES (%s)', (libro_id,))
        self.conn.commit()
        cursor.close()

    def update_disponibile(self, libro):
        """Aggiorna la disponibilità di un libro"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM libri WHERE titolo = %s', (libro.titolo,))
        libro_id = cursor.fetchone()[0]
        if libro.disponibile:
            cursor.execute('DELETE FROM libri_prestati WHERE libro_id = %s', (libro_id,))
            cursor.execute('INSERT INTO libri_disponibili (libro_id) VALUES (%s) ON CONFLICT DO NOTHING', (libro_id,))
        else:
            cursor.execute('DELETE FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            cursor.execute('INSERT INTO libri_prestati (libro_id) VALUES (%s)', (libro_id,))
        self.conn.commit()
        cursor.close()

    def rimuovi_libro(self, titolo):
        """Rimuove un libro dal database"""
        libro = self.cerca_titolo(titolo)
        if libro:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM libri WHERE titolo = %s', (titolo,))
            libro_id = cursor.fetchone()[0]
            cursor.execute('DELETE FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri_prestati WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri WHERE id = %s', (libro_id,))
            self.conn.commit()
            cursor.close()
            return True
        return False

    def cerca_titolo(self, titolo):
        """Cerca un libro per titolo"""
        for libro in self.load_libri():
            if libro.titolo == titolo:
                return libro
        return None

    def cerca_autore(self, autore):
        """Cerca un libro per autore"""
        for libro in self.load_libri():
            if libro.autore == autore:
                return libro
        return None

    def presta_libro(self, titolo):
        """Presta un libro"""
        libro = self.cerca_titolo(titolo)
        if libro and libro.disponibile:
            libro.disponibile = False
            self.update_disponibile(libro)
            return libro
        return None

    def riprendi_libro(self, titolo):
        """Restituisce un libro prestato"""
        libro = self.cerca_titolo(titolo)
        if libro and not libro.disponibile:
            libro.disponibile = True
            self.update_disponibile(libro)
            return libro
        return None

    def modifica_libro(self, titolo_vecchio, nuovo_libro):
        """Modifica un libro esistente"""
        libro = self.cerca_titolo(titolo_vecchio)
        if libro:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM libri WHERE titolo = %s', (titolo_vecchio,))
            libro_id = cursor.fetchone()[0]
            cursor.execute('DELETE FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri_prestati WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri WHERE id = %s', (libro_id,))
            self.conn.commit()
            cursor.close()
            self.save_libro(nuovo_libro)
            return True
        return False

    def mostra_autori(self):
        """Restituisce la lista degli autori"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT nome FROM autori ORDER BY nome')
        rows = cursor.fetchall()
        autori = [row[0] for row in rows]
        cursor.close()
        return autori

    def mostra_generi(self):
        """Restituisce la lista dei generi"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT nome FROM generi ORDER BY nome')
        rows = cursor.fetchall()
        generi = [row[0] for row in rows]
        cursor.close()
        return generi

    def get_libro_id_by_titolo(self, titolo):
        """Restituisce l'ID del libro dato il titolo"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM libri WHERE titolo = %s', (titolo,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    # Metodi per prenotazioni e liste d'attesa
    def prenota_libro(self, utente_id, libro_titolo):
        """Permette a un utente di prenotare un libro disponibile"""
        try:
            cursor = self.conn.cursor()

            # Ottieni l'ID del libro
            libro_id = self.get_libro_id_by_titolo(libro_titolo)
            if not libro_id:
                cursor.close()
                return False, "Libro non trovato"

            # Verifica se il libro è disponibile
            cursor.execute('SELECT libro_id FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            if not cursor.fetchone():
                cursor.close()
                return False, "Il libro non è disponibile per la prenotazione"

            # Verifica se l'utente ha già prenotazioni attive per questo libro
            cursor.execute('SELECT id FROM prenotazioni WHERE utente_id = %s AND libro_id = %s AND stato = %s',
                         (utente_id, libro_id, 'attiva'))
            if cursor.fetchone():
                cursor.close()
                return False, "Hai già una prenotazione attiva per questo libro"

            # Calcola la data di scadenza (7 giorni dalla prenotazione)
            data_scadenza = datetime.now() + timedelta(days=7)

            # Crea la prenotazione
            cursor.execute('''INSERT INTO prenotazioni (utente_id, libro_id, data_scadenza)
                            VALUES (%s, %s, %s)''', (utente_id, libro_id, data_scadenza))

            # Rimuovi il libro dalla disponibilità
            cursor.execute('DELETE FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            cursor.execute('INSERT INTO libri_prestati (libro_id) VALUES (%s)', (libro_id,))

            self.conn.commit()
            cursor.close()
            return True, f"Prenotazione effettuata con successo. Scadenza: {data_scadenza.strftime('%d/%m/%Y')}"

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore durante la prenotazione: {str(e)}"

    def aggiungi_lista_attesa(self, utente_id, libro_titolo):
        """Aggiunge un utente alla lista d'attesa per un libro non disponibile"""
        try:
            cursor = self.conn.cursor()

            # Ottieni l'ID del libro
            libro_id = self.get_libro_id_by_titolo(libro_titolo)
            if not libro_id:
                cursor.close()
                return False, "Libro non trovato"

            # Verifica se il libro è effettivamente non disponibile
            cursor.execute('SELECT libro_id FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            if cursor.fetchone():
                cursor.close()
                return False, "Il libro è disponibile, puoi prenotarlo direttamente"

            # Verifica se l'utente è già in lista d'attesa per questo libro
            cursor.execute('SELECT id FROM liste_attesa WHERE utente_id = %s AND libro_id = %s AND stato = %s',
                         (utente_id, libro_id, 'attiva'))
            if cursor.fetchone():
                cursor.close()
                return False, "Sei già in lista d'attesa per questo libro"

            # Calcola la posizione nella coda
            cursor.execute('SELECT COUNT(*) FROM liste_attesa WHERE libro_id = %s AND stato = %s',
                         (libro_id, 'attiva'))
            posizione = cursor.fetchone()[0] + 1

            # Aggiungi alla lista d'attesa
            cursor.execute('''INSERT INTO liste_attesa (utente_id, libro_id, posizione)
                            VALUES (%s, %s, %s)''', (utente_id, libro_id, posizione))

            self.conn.commit()
            cursor.close()
            return True, f"Aggiunto alla lista d'attesa. La tua posizione è: {posizione}"

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore durante l'aggiunta alla lista d'attesa: {str(e)}"

    def aggiungi_favorito(self, utente_id, libro_titolo):
        """Permette a un utente di salvare un libro nei preferiti"""
        try:
            cursor = self.conn.cursor()

            # Ottieni l'ID del libro
            libro_id = self.get_libro_id_by_titolo(libro_titolo)
            if not libro_id:
                cursor.close()
                return False, "Libro non trovato"

            # Verifica se è già nei preferiti
            cursor.execute('SELECT id FROM libri_salvati WHERE utente_id = %s AND libro_id = %s',
                         (utente_id, libro_id))
            if cursor.fetchone():
                cursor.close()
                return False, "Il libro è già nei tuoi preferiti"

            # Aggiungi ai preferiti
            cursor.execute('INSERT INTO libri_salvati (utente_id, libro_id) VALUES (%s, %s)',
                         (utente_id, libro_id))

            self.conn.commit()
            cursor.close()
            return True, "Libro aggiunto ai preferiti"

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore durante l'aggiunta ai preferiti: {str(e)}"

    def mostra_favoriti(self, utente_id):
        """Restituisce la lista dei libri salvati dall'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT l.titolo, a.nome, g.nome, l.anno_pubblicazione, l.numero_pagine, l.prezzo
                            FROM libri l
                            JOIN autori a ON l.autore_id = a.id
                            JOIN generi g ON l.genere_id = g.id
                            JOIN libri_salvati ls ON l.id = ls.libro_id
                            WHERE ls.utente_id = %s
                            ORDER BY ls.data_salvataggio DESC''', (utente_id,))

            rows = cursor.fetchall()
            libri = []
            for row in rows:
                libro = Libro(row[0], row[1], row[2], row[3], row[4], row[5])
                libri.append(libro)

            cursor.close()
            return libri

        except Exception as e:
            cursor.close()
            return []

    def mostra_prenotazioni_utente(self, utente_id):
        """Restituisce la lista delle prenotazioni attive dell'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT l.titolo, a.nome, p.data_prenotazione, p.data_scadenza
                            FROM prenotazioni p
                            JOIN libri l ON p.libro_id = l.id
                            JOIN autori a ON l.autore_id = a.id
                            WHERE p.utente_id = %s AND p.stato = 'attiva'
                            ORDER BY p.data_prenotazione DESC''', (utente_id,))

            rows = cursor.fetchall()
            prenotazioni = []
            for row in rows:
                prenotazioni.append({
                    'titolo': row[0],
                    'autore': row[1],
                    'data_prenotazione': row[2].strftime('%d/%m/%Y') if row[2] else 'N/A',
                    'data_scadenza': row[3].strftime('%d/%m/%Y') if row[3] else 'N/A'
                })

            cursor.close()
            return prenotazioni

        except Exception as e:
            cursor.close()
            return []

    def mostra_notifiche(self, utente_id):
        """Restituisce le notifiche non lette dell'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT messaggio, tipo, data_creazione
                            FROM notifiche
                            WHERE utente_id = %s AND letta = FALSE
                            ORDER BY data_creazione DESC''', (utente_id,))

            rows = cursor.fetchall()
            notifiche = []
            for row in rows:
                notifiche.append({
                    'messaggio': row[0],
                    'tipo': row[1],
                    'data': row[2].strftime('%d/%m/%Y %H:%M') if row[2] else 'N/A'
                })

            cursor.close()
            return notifiche

        except Exception as e:
            cursor.close()
            return []

    def segna_notifiche_lette(self, utente_id):
        """Segna tutte le notifiche dell'utente come lette"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE notifiche SET letta = TRUE WHERE utente_id = %s AND letta = FALSE', (utente_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False

    def aggiungi_notifica(self, utente_id, messaggio, tipo='generale'):
        """Aggiunge una notifica per un utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO notifiche (utente_id, messaggio, tipo) VALUES (%s, %s, %s)',
                         (utente_id, messaggio, tipo))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False

    # Metodi per la gestione degli indirizzi utente
    def salva_indirizzo(self, utente_id, nome, cognome, indirizzo, citta, cap, provincia, telefono=None, is_default=False):
        """Salva un indirizzo per l'utente"""
        try:
            cursor = self.conn.cursor()

            # Se è l'indirizzo di default, rimuovi il flag dagli altri indirizzi
            if is_default:
                cursor.execute('UPDATE indirizzi_utente SET is_default = FALSE WHERE utente_id = %s', (utente_id,))

            cursor.execute('''INSERT INTO indirizzi_utente (utente_id, nome, cognome, indirizzo, citta, cap, provincia, telefono, is_default)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                         (utente_id, nome, cognome, indirizzo, citta, cap, provincia, telefono, is_default))

            self.conn.commit()
            cursor.close()
            return True, "Indirizzo salvato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nel salvataggio dell'indirizzo: {str(e)}"

    def get_indirizzi_utente(self, utente_id):
        """Restituisce tutti gli indirizzi dell'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT id, nome, cognome, indirizzo, citta, cap, provincia, telefono, is_default
                            FROM indirizzi_utente
                            WHERE utente_id = %s
                            ORDER BY is_default DESC, data_creazione DESC''', (utente_id,))

            indirizzi = []
            for row in cursor.fetchall():
                indirizzi.append({
                    'id': row[0],
                    'nome': row[1],
                    'cognome': row[2],
                    'indirizzo': row[3],
                    'citta': row[4],
                    'cap': row[5],
                    'provincia': row[6],
                    'telefono': row[7],
                    'is_default': row[8]
                })

            cursor.close()
            return indirizzi
        except Exception as e:
            cursor.close()
            return []

    # Metodi per la gestione dei metodi di pagamento
    def salva_metodo_pagamento(self, utente_id, tipo, numero_carta, scadenza, titolare, is_default=False):
        """Salva un metodo di pagamento per l'utente"""
        try:
            cursor = self.conn.cursor()

            # Criptazione semplice del numero carta (in produzione usare una vera crittografia)
            numero_criptato = self.hash_password(numero_carta)[:50]  # limita a 50 caratteri

            # Se è il metodo di default, rimuovi il flag dagli altri metodi
            if is_default:
                cursor.execute('UPDATE metodi_pagamento SET is_default = FALSE WHERE utente_id = %s', (utente_id,))

            cursor.execute('''INSERT INTO metodi_pagamento (utente_id, tipo, numero_carta, scadenza, titolare, is_default)
                            VALUES (%s, %s, %s, %s, %s, %s)''',
                         (utente_id, tipo, numero_criptato, scadenza, titolare, is_default))

            self.conn.commit()
            cursor.close()
            return True, "Metodo di pagamento salvato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nel salvataggio del metodo di pagamento: {str(e)}"

    def get_metodi_pagamento_utente(self, utente_id):
        """Restituisce tutti i metodi di pagamento dell'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT id, tipo, numero_carta, titolare, scadenza, is_default
                            FROM metodi_pagamento
                            WHERE utente_id = %s
                            ORDER BY is_default DESC, data_creazione DESC''', (utente_id,))

            metodi = []
            for row in cursor.fetchall():
                metodi.append({
                    'id': row[0],
                    'tipo': row[1],
                    'numero_carta': row[2],  # Per mostrare ultime 4 cifre
                    'titolare': row[3],
                    'scadenza': row[4],
                    'is_default': row[5]
                })

            cursor.close()
            return metodi
        except Exception as e:
            cursor.close()
            return []

    def imposta_metodo_predefinito(self, utente_id, metodo_id):
        """Imposta un metodo di pagamento come predefinito"""
        try:
            cursor = self.conn.cursor()

            # Rimuovi flag default da tutti i metodi dell'utente
            cursor.execute('UPDATE metodi_pagamento SET is_default = FALSE WHERE utente_id = %s', (utente_id,))

            # Imposta il metodo selezionato come default
            cursor.execute('UPDATE metodi_pagamento SET is_default = TRUE WHERE id = %s AND utente_id = %s',
                         (metodo_id, utente_id))

            self.conn.commit()
            cursor.close()
            return True, "Metodo di pagamento impostato come predefinito"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nell'impostazione del metodo predefinito: {str(e)}"

    def elimina_metodo_pagamento(self, metodo_id):
        """Elimina un metodo di pagamento"""
        try:
            cursor = self.conn.cursor()

            # Verifica che non sia l'unico metodo di pagamento dell'utente
            cursor.execute('''SELECT COUNT(*) FROM metodi_pagamento
                            WHERE utente_id = (SELECT utente_id FROM metodi_pagamento WHERE id = %s)''', (metodo_id,))
            count = cursor.fetchone()[0]

            if count <= 1:
                cursor.close()
                return False, "Non puoi eliminare l'unico metodo di pagamento. Aggiungine un altro prima di eliminarlo."

            cursor.execute('DELETE FROM metodi_pagamento WHERE id = %s', (metodo_id,))

            self.conn.commit()
            cursor.close()
            return True, "Metodo di pagamento eliminato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nell'eliminazione del metodo di pagamento: {str(e)}"

    # Metodi per la gestione dell'inventario librerie
    def aggiorna_inventario_libreria(self, libreria_id, libro_id, copie_nuove=None, copie_usate=None):
        """Aggiorna l'inventario di una libreria per un libro specifico"""
        try:
            cursor = self.conn.cursor()

            # Verifica se esiste già una voce di inventario
            cursor.execute('SELECT id, copie_nuove, copie_usate FROM inventario_librerie WHERE libreria_id = %s AND libro_id = %s',
                         (libreria_id, libro_id))
            existing = cursor.fetchone()

            if existing:
                # Aggiorna esistente
                current_nuove = existing[1] if existing[1] else 0
                current_usate = existing[2] if existing[2] else 0

                nuove_nuove = copie_nuove if copie_nuove is not None else current_nuove
                nuove_usate = copie_usate if copie_usate is not None else current_usate

                cursor.execute('''UPDATE inventario_librerie
                                SET copie_nuove = %s, copie_usate = %s
                                WHERE libreria_id = %s AND libro_id = %s''',
                             (nuove_nuove, nuove_usate, libreria_id, libro_id))
            else:
                # Crea nuova voce
                cursor.execute('''INSERT INTO inventario_librerie (libreria_id, libro_id, copie_nuove, copie_usate)
                                VALUES (%s, %s, %s, %s)''',
                             (libreria_id, libro_id, copie_nuove or 0, copie_usate or 0))

            self.conn.commit()
            cursor.close()
            return True, "Inventario aggiornato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nell'aggiornamento dell'inventario: {str(e)}"

    def get_inventario_libreria(self, libreria_id, libro_id=None):
        """Restituisce l'inventario di una libreria (per tutti i libri o per un libro specifico)"""
        try:
            cursor = self.conn.cursor()

            if libro_id:
                cursor.execute('''SELECT l.titolo, i.copie_nuove, i.copie_usate, i.copie_vendute
                                FROM inventario_librerie i
                                JOIN libri l ON i.libro_id = l.id
                                WHERE i.libreria_id = %s AND i.libro_id = %s''', (libreria_id, libro_id))
            else:
                cursor.execute('''SELECT l.titolo, i.copie_nuove, i.copie_usate, i.copie_vendute
                                FROM inventario_librerie i
                                JOIN libri l ON i.libro_id = l.id
                                WHERE i.libreria_id = %s
                                ORDER BY l.titolo''', (libreria_id,))

            inventario = []
            for row in cursor.fetchall():
                inventario.append({
                    'titolo': row[0],
                    'copie_nuove': row[1] or 0,
                    'copie_usate': row[2] or 0,
                    'copie_vendute': row[3] or 0,
                    'totale_disponibili': (row[1] or 0) + (row[2] or 0)
                })

            cursor.close()
            return inventario
        except Exception as e:
            cursor.close()
            return []

    # Metodi per gli acquisti
    def crea_acquisto(self, utente_id, libreria_id, indirizzo_id, metodo_pagamento_id, carrello, tipo_consegna='negozio', note=None):
        """Crea un nuovo acquisto"""
        try:
            cursor = self.conn.cursor()

            # Calcola il totale
            totale = 0
            for item in carrello:
                totale += item['prezzo_unitario'] * item['quantita']

            # Calcola la data di consegna prevista (3-7 giorni per spedizione, immediata per ritiro in negozio)
            if tipo_consegna == 'negozio':
                data_consegna_prevista = datetime.now()
            else:
                data_consegna_prevista = datetime.now() + timedelta(days=5)  # 5 giorni per spedizione

            # Crea l'acquisto
            cursor.execute('''INSERT INTO acquisti (utente_id, libreria_id, indirizzo_consegna_id, metodo_pagamento_id,
                                                   totale, tipo_consegna, note, data_consegna_prevista)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id''',
                         (utente_id, libreria_id, indirizzo_id, metodo_pagamento_id, totale, tipo_consegna, note, data_consegna_prevista))

            acquisto_id = cursor.fetchone()[0]

            # Aggiungi i dettagli dell'acquisto e aggiorna l'inventario
            for item in carrello:
                libro_id = item['libro_id']
                quantita = item['quantita']
                condizione = item['condizione']
                prezzo_unitario = item['prezzo_unitario']

                # Aggiungi dettaglio acquisto
                cursor.execute('''INSERT INTO dettagli_acquisto (acquisto_id, libro_id, libreria_id, quantita, condizione, prezzo_unitario, totale)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                             (acquisto_id, libro_id, libreria_id, quantita, condizione, prezzo_unitario, prezzo_unitario * quantita))

                # Aggiorna inventario (diminuisci copie disponibili, aumenta copie vendute)
                if condizione == 'nuovo':
                    cursor.execute('''UPDATE inventario_librerie
                                    SET copie_nuove = copie_nuove - %s, copie_vendute = copie_vendute + %s
                                    WHERE libreria_id = %s AND libro_id = %s''',
                                 (quantita, quantita, libreria_id, libro_id))
                else:  # usato
                    cursor.execute('''UPDATE inventario_librerie
                                    SET copie_usate = copie_usate - %s, copie_vendute = copie_vendute + %s
                                    WHERE libreria_id = %s AND libro_id = %s''',
                                 (quantita, quantita, libreria_id, libro_id))

            # Se consegna a domicilio, crea una consegna
            if tipo_consegna == 'casa':
                cursor.execute('''INSERT INTO consegne (acquisto_id, stato, data_consegna_prevista)
                                VALUES (%s, 'in_preparazione', %s)''', (acquisto_id, data_consegna_prevista))

            # Aggiungi notifica all'utente
            self.aggiungi_notifica(utente_id, f"Il tuo acquisto #{acquisto_id} è stato confermato!", "acquisto")

            self.conn.commit()
            cursor.close()
            return True, f"Acquisto #{acquisto_id} creato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nella creazione dell'acquisto: {str(e)}"

    def get_acquisti_utente(self, utente_id):
        """Restituisce la lista degli acquisti dell'utente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT a.id, a.totale, a.stato, a.tipo_consegna, a.data_acquisto, a.data_consegna_prevista,
                                     l.nome as libreria, c.numero_tracking
                            FROM acquisti a
                            JOIN librerie l ON a.libreria_id = l.id
                            LEFT JOIN consegne c ON a.id = c.acquisto_id
                            WHERE a.utente_id = %s
                            ORDER BY a.data_acquisto DESC''', (utente_id,))

            acquisti = []
            for row in cursor.fetchall():
                acquisti.append({
                    'id': row[0],
                    'totale': float(row[1]),
                    'stato': row[2],
                    'tipo_consegna': row[3],
                    'data_acquisto': row[4].strftime('%d/%m/%Y %H:%M') if row[4] else None,
                    'data_consegna_prevista': row[5].strftime('%d/%m/%Y') if row[5] else None,
                    'libreria': row[6],
                    'tracking': row[7]
                })

            cursor.close()
            return acquisti
        except Exception as e:
            cursor.close()
            return []

    def get_dettagli_acquisto(self, acquisto_id):
        """Restituisce i dettagli di un acquisto specifico"""
        try:
            cursor = self.conn.cursor()

            # Dettagli acquisto
            cursor.execute('''SELECT a.id, a.totale, a.stato, a.tipo_consegna, a.data_acquisto, a.data_consegna_prevista,
                                     a.data_consegna_effettiva, l.nome as libreria, c.numero_tracking, c.stato as stato_consegna
                            FROM acquisti a
                            JOIN librerie l ON a.libreria_id = l.id
                            LEFT JOIN consegne c ON a.id = c.acquisto_id
                            WHERE a.id = %s''', (acquisto_id,))

            acquisto = cursor.fetchone()
            if not acquisto:
                cursor.close()
                return None

            # Dettagli libri
            cursor.execute('''SELECT l.titolo, a.nome as autore, da.quantita, da.condizione, da.prezzo_unitario, da.totale
                            FROM dettagli_acquisto da
                            JOIN libri l ON da.libro_id = l.id
                            JOIN autori a ON l.autore_id = a.id
                            WHERE da.acquisto_id = %s''', (acquisto_id,))

            libri = []
            for row in cursor.fetchall():
                libri.append({
                    'titolo': row[0],
                    'autore': row[1],
                    'quantita': row[2],
                    'condizione': row[3],
                    'prezzo_unitario': float(row[4]),
                    'totale': float(row[5])
                })

            cursor.close()

            return {
                'id': acquisto[0],
                'totale': float(acquisto[1]),
                'stato': acquisto[2],
                'tipo_consegna': acquisto[3],
                'data_acquisto': acquisto[4].strftime('%d/%m/%Y %H:%M') if acquisto[4] else None,
                'data_consegna_prevista': acquisto[5].strftime('%d/%m/%Y') if acquisto[5] else None,
                'data_consegna_effettiva': acquisto[6].strftime('%d/%m/%Y') if acquisto[6] else None,
                'libreria': acquisto[7],
                'tracking': acquisto[8],
                'stato_consegna': acquisto[9],
                'libri': libri
            }
        except Exception as e:
            cursor.close()
            return None

    # Metodi per il feedback e recensioni
    def aggiungi_feedback(self, utente_id, libro_id, acquisto_id, valutazione, commento=None):
        """Aggiunge una recensione per un libro acquistato"""
        try:
            cursor = self.conn.cursor()

            # Verifica che l'utente abbia acquistato il libro
            cursor.execute('''SELECT id FROM dettagli_acquisto
                            WHERE acquisto_id = %s AND libro_id = %s''', (acquisto_id, libro_id))
            if not cursor.fetchone():
                cursor.close()
                return False, "Non puoi recensire un libro che non hai acquistato"

            cursor.execute('''INSERT INTO feedback_libri (utente_id, libro_id, acquisto_id, valutazione, commento)
                            VALUES (%s, %s, %s, %s, %s)''',
                         (utente_id, libro_id, acquisto_id, valutazione, commento))

            self.conn.commit()
            cursor.close()
            return True, "Recensione aggiunta con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nell'aggiunta della recensione: {str(e)}"

    def get_feedback_libro(self, libro_id, limit=10):
        """Restituisce le recensioni di un libro"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT f.valutazione, f.commento, f.data_recensione, u.nome_utente,
                                     f.utile, f.non_utile
                            FROM feedback_libri f
                            JOIN utenti u ON f.utente_id = u.id
                            WHERE f.libro_id = %s AND f.moderato = FALSE
                            ORDER BY f.data_recensione DESC
                            LIMIT %s''', (libro_id, limit))

            feedback = []
            for row in cursor.fetchall():
                feedback.append({
                    'valutazione': row[0],
                    'commento': row[1],
                    'data': row[2].strftime('%d/%m/%Y') if row[2] else None,
                    'utente': row[3],
                    'utile': row[4] or 0,
                    'non_utile': row[5] or 0
                })

            cursor.close()
            return feedback
        except Exception as e:
            cursor.close()
            return []

    def vota_feedback(self, feedback_id, utile=True):
        """Vota utile/non utile una recensione"""
        try:
            cursor = self.conn.cursor()

            if utile:
                cursor.execute('UPDATE feedback_libri SET utile = utile + 1 WHERE id = %s', (feedback_id,))
            else:
                cursor.execute('UPDATE feedback_libri SET non_utile = non_utile + 1 WHERE id = %s', (feedback_id,))

            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False

    # Metodi per le richieste dei bibliotecari
    def crea_richiesta_bibliotecario(self, bibliotecario_id, tipo, descrizione, priorita='normale'):
        """Crea una nuova richiesta per un bibliotecario"""
        try:
            cursor = self.conn.cursor()

            cursor.execute('''INSERT INTO richieste_bibliotecari (bibliotecario_id, tipo, descrizione, priorita)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id''', (bibliotecario_id, tipo, descrizione, priorita))

            richiesta_id = cursor.fetchone()[0]

            # Notifica gli amministratori (per ora tutti i bibliotecari)
            cursor.execute('''SELECT id FROM utenti WHERE ruolo_id = (SELECT id FROM ruoli WHERE nome = 'bibliotecario')''')
            bibliotecari = cursor.fetchall()

            for bib in bibliotecari:
                if bib[0] != bibliotecario_id:  # Non notificare se stesso
                    self.aggiungi_notifica(bib[0], f"Nuova richiesta #{richiesta_id}: {tipo}", "richiesta")

            self.conn.commit()
            cursor.close()
            return True, f"Richiesta #{richiesta_id} creata con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nella creazione della richiesta: {str(e)}"

    def get_richieste_bibliotecario(self, bibliotecario_id=None):
        """Restituisce le richieste dei bibliotecari (tutte se admin, solo proprie se bibliotecario)"""
        try:
            cursor = self.conn.cursor()

            if bibliotecario_id:
                cursor.execute('''SELECT r.id, r.tipo, r.descrizione, r.priorita, r.stato, r.data_creazione,
                                         u.nome_utente as bibliotecario
                                FROM richieste_bibliotecari r
                                JOIN utenti u ON r.bibliotecario_id = u.id
                                WHERE r.bibliotecario_id = %s
                                ORDER BY r.data_creazione DESC''', (bibliotecario_id,))
            else:
                cursor.execute('''SELECT r.id, r.tipo, r.descrizione, r.priorita, r.stato, r.data_creazione,
                                         u.nome_utente as bibliotecario
                                FROM richieste_bibliotecari r
                                JOIN utenti u ON r.bibliotecario_id = u.id
                                ORDER BY r.priorita DESC, r.data_creazione DESC''')

            richieste = []
            for row in cursor.fetchall():
                richieste.append({
                    'id': row[0],
                    'tipo': row[1],
                    'descrizione': row[2],
                    'priorita': row[3],
                    'stato': row[4],
                    'data_creazione': row[5].strftime('%d/%m/%Y %H:%M') if row[5] else None,
                    'bibliotecario': row[6]
                })

            cursor.close()
            return richieste
        except Exception as e:
            cursor.close()
            return []

    def aggiorna_stato_richiesta(self, richiesta_id, nuovo_stato, bibliotecario_id=None):
        """Aggiorna lo stato di una richiesta"""
        try:
            cursor = self.conn.cursor()

            if nuovo_stato == 'risolta':
                cursor.execute('UPDATE richieste_bibliotecari SET stato = %s, data_risoluzione = CURRENT_TIMESTAMP WHERE id = %s',
                             (nuovo_stato, richiesta_id))
            else:
                cursor.execute('UPDATE richieste_bibliotecari SET stato = %s WHERE id = %s', (nuovo_stato, richiesta_id))

            # Notifica il bibliotecario che ha fatto la richiesta
            if bibliotecario_id:
                cursor.execute('SELECT bibliotecario_id FROM richieste_bibliotecari WHERE id = %s', (richiesta_id,))
                bib_id = cursor.fetchone()
                if bib_id:
                    self.aggiungi_notifica(bib_id[0], f"La tua richiesta #{richiesta_id} è stata aggiornata a '{nuovo_stato}'", "richiesta")

            self.conn.commit()
            cursor.close()
            return True, "Stato richiesta aggiornato con successo"
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return False, f"Errore nell'aggiornamento dello stato: {str(e)}"

    def __del__(self):
        """Chiude la connessione al database"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()