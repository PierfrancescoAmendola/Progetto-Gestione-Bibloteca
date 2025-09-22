"""
Script per popolare il database con dati di esempio
"""

import random
from datetime import datetime, timedelta
from database import DatabaseManager


class DatabasePopulator:
    """Classe per popolare il database con dati di esempio"""

    def __init__(self):
        """Inizializza il popolatore del database"""
        self.db = DatabaseManager()

        # Liste di dati per la generazione
        self.autori_italiani = [
            "Umberto Eco", "Italo Calvino", "Alessandro Manzoni", "Dante Alighieri",
            "Giovanni Boccaccio", "Petrarca", "Niccolò Machiavelli", "Carlo Collodi",
            "Luigi Pirandello", "Elsa Morante", "Primo Levi", "Natalia Ginzburg",
            "Cesare Pavese", "Alberto Moravia", "Leonardo Sciascia", "Andrea Camilleri",
            "Gianrico Carofiglio", "Roberto Saviano", "Elena Ferrante", "Paolo Giordano",
            "Alessandro Baricco", "Margaret Mazzantini", "Susanna Tamaro", "Melania Mazzucco",
            "Antonio Tabucchi", "Claudio Magris", "Erri De Luca", "Fabio Volo",
            "Giorgio Faletti", "Massimo Carlotto", "Sandrone Dazieri", "Giuseppe Pederiali"
        ]

        self.autori_internazionali = [
            "George Orwell", "Jane Austen", "Charles Dickens", "Mark Twain",
            "Ernest Hemingway", "F. Scott Fitzgerald", "William Faulkner", "John Steinbeck",
            "Harper Lee", "J.D. Salinger", "Jack Kerouac", "Sylvia Plath",
            "Toni Morrison", "Alice Walker", "Maya Angelou", "Zora Neale Hurston",
            "Gabriel García Márquez", "Mario Vargas Llosa", "Isabel Allende", "Jorge Luis Borges",
            "Franz Kafka", "Thomas Mann", "Hermann Hesse", "Bertolt Brecht",
            "Albert Camus", "Jean-Paul Sartre", "Simone de Beauvoir", "André Breton",
            "Federico García Lorca", "Pablo Neruda", "Octavio Paz", "Carlos Fuentes",
            "Chinua Achebe", "Wole Soyinka", "Ngũgĩ wa Thiong'o", "Achebe Chinua",
            "Haruki Murakami", "Yukio Mishima", "Banana Yoshimoto", "Kenzaburō Ōe",
            "Orhan Pamuk", "Halide Edib Adıvar", "Yaşar Kemal", "Aziz Nesin"
        ]

        self.generi = [
            "Narrativa", "Saggistica", "Poesia", "Teatro", "Fantascienza", "Fantasy",
            "Giallo", "Thriller", "Horror", "Storico", "Biografia", "Autobiografia",
            "Filosofia", "Psicologia", "Scienza", "Storia", "Arte", "Musica",
            "Cinema", "Fotografia", "Viaggi", "Sport", "Cucina", "Giardinaggio",
            "Manuali", "Scuola", "Università", "Bambini", "Ragazzi", "Giovani Adulti"
        ]

        self.citta_italiane = [
            ("Milano", "Lombardia"), ("Roma", "Lazio"), ("Torino", "Piemonte"),
            ("Firenze", "Toscana"), ("Napoli", "Campania"), ("Bologna", "Emilia-Romagna"),
            ("Venezia", "Veneto"), ("Genova", "Liguria"), ("Palermo", "Sicilia"),
            ("Bari", "Puglia"), ("Catania", "Sicilia"), ("Verona", "Veneto"),
            ("Messina", "Sicilia"), ("Padova", "Veneto"), ("Trieste", "Friuli-Venezia Giulia"),
            ("Brescia", "Lombardia"), ("Parma", "Emilia-Romagna"), ("Modena", "Emilia-Romagna"),
            ("Reggio Emilia", "Emilia-Romagna"), ("Reggio Calabria", "Calabria"),
            ("Perugia", "Umbria"), ("Livorno", "Toscana"), ("Ravenna", "Emilia-Romagna"),
            ("Cagliari", "Sardegna"), ("Foggia", "Puglia"), ("Rimini", "Emilia-Romagna"),
            ("Salerno", "Campania"), ("Ferrara", "Emilia-Romagna"), ("Sassari", "Sardegna"),
            ("Latina", "Lazio"), ("Giugliano in Campania", "Campania"), ("Monza", "Lombardia")
        ]

    def create_diverse_libraries(self):
        """Crea città, biblioteche e librerie diverse"""
        print("Creazione di città, biblioteche e librerie...")

        # Inserisci città aggiuntive
        for nome, regione in self.citta_italiane:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("INSERT INTO citta (nome, regione) VALUES (%s, %s) ON CONFLICT (nome) DO NOTHING",
                             (nome, regione))
                self.db.conn.commit()
                cursor.close()
            except Exception as e:
                print(f"Errore nell'inserimento della città {nome}: {e}")
                self.db.conn.rollback()

        # Crea biblioteche per ogni città
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, nome FROM citta")
        citta_list = cursor.fetchall()
        cursor.close()

        for citta_id, citta_nome in citta_list:
            # Crea 1-3 biblioteche per città
            num_biblioteche = random.randint(1, 3)
            for i in range(num_biblioteche):
                nome_biblioteca = f"Biblioteca {'Centrale' if i == 0 else f'Comunale {i}'} di {citta_nome}"
                indirizzo = f"Via Biblioteca {random.randint(1, 100)}, {citta_nome}"

                try:
                    cursor = self.db.conn.cursor()
                    cursor.execute("INSERT INTO biblioteche (nome, indirizzo, citta_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                 (nome_biblioteca, indirizzo, citta_id))
                    self.db.conn.commit()
                    cursor.close()
                except Exception as e:
                    print(f"Errore nell'inserimento della biblioteca {nome_biblioteca}: {e}")
                    self.db.conn.rollback()

        # Crea librerie per ogni città
        for citta_id, citta_nome in citta_list:
            # Crea 2-5 librerie per città
            num_librerie = random.randint(2, 5)
            nomi_librerie = ["Mondadori", "Feltrinelli", "IBS", "Libreria Universitaria", "Libreria del Centro",
                           "Libreria Moderna", "Libreria dei Ragazzi", "Libreria Tecnica", "Libreria Storica"]

            for i in range(num_librerie):
                nome_libreria = f"{random.choice(nomi_librerie)} {citta_nome}"
                indirizzo = f"Via dei Libri {random.randint(1, 200)}, {citta_nome}"

                try:
                    cursor = self.db.conn.cursor()
                    cursor.execute("INSERT INTO librerie (nome, indirizzo, citta_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                 (nome_libreria, indirizzo, citta_id))
                    self.db.conn.commit()
                    cursor.close()
                except Exception as e:
                    print(f"Errore nell'inserimento della libreria {nome_libreria}: {e}")
                    self.db.conn.rollback()

        print("Città, biblioteche e librerie create con successo!")

    def create_books_collection(self):
        """Crea una collezione di oltre 1000 libri"""
        print("Creazione della collezione di libri...")

        libri_creati = 0
        target_libri = 1200  # Oltre 1000 libri

        # Combinazioni autore-genere per creare libri realistici
        combinazioni = []
        for autore in self.autori_italiani + self.autori_internazionali:
            for genere in self.generi:
                combinazioni.append((autore, genere))

        # Mescola le combinazioni per varietà
        random.shuffle(combinazioni)

        # Crea libri basati sulle combinazioni
        for autore, genere in combinazioni[:target_libri]:
            # Genera titolo basato su autore e genere
            titoli_base = {
                "Narrativa": ["Storia di", "Vita di", "Cronaca di", "Memorie di", "Il viaggio di", "L'amore di"],
                "Fantascienza": ["Il pianeta", "Stelle", "Galassia", "Il futuro", "Cyber", "Robot"],
                "Fantasy": ["Il regno di", "La spada di", "Il mago", "L'elfo", "Il drago", "La profezia"],
                "Giallo": ["Il mistero di", "L'enigma", "Il caso", "L'indagine", "Il delitto", "L'ombra"],
                "Thriller": ["La minaccia", "Il pericolo", "La caccia", "L'intrigo", "Il complotto", "La fuga"],
                "Storico": ["L'era di", "Il tempo di", "La storia di", "L'impero di", "La battaglia di", "Il re"],
                "Poesia": ["Versi per", "Poesie di", "Canti di", "Rime per", "Liriche di", "Sonetti per"],
                "Saggistica": ["Saggio su", "Studio di", "Analisi di", "Riflessioni su", "Pensieri su", "Teoria di"]
            }

            base_titolo = titoli_base.get(genere, ["Il libro di"])[0]
            # Aggiungi un numero casuale per rendere i titoli unici
            numero_unico = random.randint(1, 9999)
            titolo = f"{base_titolo} {autore.split()[0]} {numero_unico}"

            # Genera anno pubblicazione (dagli anni '40 ad oggi)
            anno_pubblicazione = random.randint(1940, 2023)

            # Genera numero pagine (50-800)
            numero_pagine = random.randint(50, 800)

            # Genera prezzi
            prezzo_base = random.uniform(5.0, 50.0)
            prezzo_nuovo = round(prezzo_base, 2)
            prezzo_usato = round(prezzo_base * random.uniform(0.3, 0.8), 2)  # 30-80% del prezzo nuovo

            # Genera descrizione
            descrizioni = [
                f"Un'opera {genere.lower()} scritta da {autore}.",
                f"Libro di {genere.lower()} dell'autore {autore}, pubblicato nel {anno_pubblicazione}.",
                f"Una storia coinvolgente nel genere {genere.lower()} firmata da {autore}.",
                f"Opera letteraria di {autore} appartenente al genere {genere.lower()}.",
                f"Pubblicazione del {anno_pubblicazione} nel campo della {genere.lower()}."
            ]
            descrizione = random.choice(descrizioni)

            # Genera ISBN fittizio
            isbn = f"978-{random.randint(10,99)}-{random.randint(100000,999999)}-{random.randint(0,9)}"

            try:
                # Salva il libro
                from models import Libro
                libro = Libro(titolo, autore, genere, anno_pubblicazione, numero_pagine,
                            prezzo_nuovo, prezzo_nuovo, prezzo_usato, descrizione, isbn)
                self.db.save_libro(libro)
                libri_creati += 1

                if libri_creati % 50 == 0:
                    print(f"Creati {libri_creati} libri...")

            except Exception as e:
                print(f"Errore nella creazione del libro '{titolo}': {e}")
                # Continua con il prossimo libro invece di fermarsi
                continue

        print(f"Collezione di {libri_creati} libri creata con successo!")

    def populate_inventory(self):
        """Popola l'inventario delle librerie con copie dei libri"""
        print("Popolamento dell'inventario delle librerie...")

        try:
            cursor = self.db.conn.cursor()

            # Ottieni tutte le librerie
            cursor.execute("SELECT id, nome FROM librerie")
            librerie = cursor.fetchall()

            # Ottieni tutti i libri
            cursor.execute("SELECT id, titolo FROM libri")
            libri = cursor.fetchall()

            cursor.close()

            inventario_creato = 0

            for libreria_id, libreria_nome in librerie:
                # Per ogni libreria, aggiungi inventario per alcuni libri casuali
                libri_per_libreria = random.sample(libri, min(len(libri), random.randint(50, 200)))

                for libro_id, libro_titolo in libri_per_libreria:
                    # Genera copie nuove e usate
                    copie_nuove = random.randint(0, 10)
                    copie_usate = random.randint(0, 5)

                    if copie_nuove > 0 or copie_usate > 0:
                        try:
                            success, message = self.db.aggiorna_inventario_libreria(
                                libreria_id, libro_id, copie_nuove, copie_usate)
                            if success:
                                inventario_creato += 1
                            else:
                                print(f"Errore inventario {libreria_nome} - {libro_titolo}: {message}")
                        except Exception as e:
                            print(f"Errore nell'aggiornamento inventario per {libreria_nome}: {e}")
                            continue

                # Commit ogni 10 librerie per evitare problemi di transazione
                if librerie.index((libreria_id, libreria_nome)) % 10 == 0:
                    try:
                        self.db.conn.commit()
                    except Exception as e:
                        print(f"Errore commit parziale: {e}")

            # Commit finale
            try:
                self.db.conn.commit()
            except Exception as e:
                print(f"Errore commit finale: {e}")

            print(f"Inventario popolato per {inventario_creato} voci!")

        except Exception as e:
            print(f"Errore nel popolamento dell'inventario: {e}")
            try:
                self.db.conn.rollback()
            except Exception:
                pass

    def run(self):
        """Esegue tutto il popolamento del database"""
        print("=== AVVIO POPOLAMENTO DATABASE ===")

        try:
            self.create_diverse_libraries()
            self.create_books_collection()
            self.populate_inventory()

            print("=== POPOLAMENTO COMPLETATO CON SUCCESSO ===")
            print("Il database ora contiene:")
            print("- Città italiane con biblioteche e librerie")
            print("- Oltre 1000 libri di autori italiani e internazionali")
            print("- Inventario distribuito nelle librerie")

        except Exception as e:
            print(f"Errore durante il popolamento: {e}")
        finally:
            # Chiudi la connessione
            if hasattr(self.db, 'conn'):
                self.db.conn.close()


if __name__ == "__main__":
    populator = DatabasePopulator()
    populator.run()