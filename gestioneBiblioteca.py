#!/usr/bin/env python3
import sys
import psycopg2
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QInputDialog, QMessageBox, QListWidget, QTextEdit, QLineEdit, QFormLayout, QDialog, QDialogButtonBox, QStackedWidget, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class Libro:
    def __init__(self, titolo, autore, genere, anno_pubblicazione, numero_pagine, prezzo):
        self.titolo = titolo
        self.autore = autore
        self.genere = genere
        self.anno_pubblicazione = anno_pubblicazione
        self.numero_pagine = numero_pagine
        self.prezzo = prezzo
        self.disponibile = True  # Di default è disponibile

    def __str__(self):
        return f"{self.titolo} - {self.autore} - {self.genere} - {self.anno_pubblicazione} - {self.numero_pagine} pagine - €{self.prezzo:.2f} - {'Disponibile' if self.disponibile else 'Non disponibile'}"

class Biblioteca:
    autori = ["Pierfrancesco Amendola", "George Orwell", "Disney"]

    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='a',  # Cambia con la tua password
            database='biblioteca'
        )
        self.create_table()
        self.libri = self.load_libri()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS autori (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) UNIQUE
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS generi (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) UNIQUE
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS libri (
            id SERIAL PRIMARY KEY,
            titolo VARCHAR(255),
            autore_id INTEGER REFERENCES autori(id),
            genere_id INTEGER REFERENCES generi(id),
            anno_pubblicazione INTEGER,
            numero_pagine INTEGER,
            prezzo DECIMAL(10,2)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS libri_disponibili (
            libro_id INTEGER PRIMARY KEY REFERENCES libri(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS libri_prestati (
            libro_id INTEGER PRIMARY KEY REFERENCES libri(id),
            data_prestito TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()
        cursor.close()

    def load_libri(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT l.titolo, a.nome, g.nome, l.anno_pubblicazione, l.numero_pagine, l.prezzo,
                                 CASE WHEN ld.libro_id IS NOT NULL THEN TRUE ELSE FALSE END as disponibile
                          FROM libri l
                          JOIN autori a ON l.autore_id = a.id
                          JOIN generi g ON l.genere_id = g.id
                          LEFT JOIN libri_disponibili ld ON l.id = ld.libro_id''')
        rows = cursor.fetchall()
        libri = []
        for row in rows:
            libro = Libro(row[0], row[1], row[2], row[3], row[4], row[5])
            libro.disponibile = bool(row[6])
            libri.append(libro)
        cursor.close()
        print(f"Caricati {len(libri)} libri dal database PostgreSQL.")  # Debug
        # Se il DB è vuoto, aggiungi libri di default
        if not libri:
            default_libri = [
                Libro("Lion King", "Disney", "Animazione", 1994, 88, 19.99),
                Libro("Il piccolo principe", "Antoine de Saint-Exupéry", "Narrativa", 1943, 96, 12.99),
                Libro("1984", "George Orwell", "Distopia", 1949, 328, 15.99)
            ]
            for libro in default_libri:
                self.save_libro(libro)
            libri = default_libri
        return libri

    def save_libro(self, libro):
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
        cursor.execute('INSERT INTO libri (titolo, autore_id, genere_id, anno_pubblicazione, numero_pagine, prezzo) VALUES (%s, %s, %s, %s, %s, %s)',
                       (libro.titolo, autore_id, genere_id, libro.anno_pubblicazione, libro.numero_pagine, libro.prezzo))
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

    def aggiungi_libro(self, libro):
        self.libri.append(libro)
        self.libri.sort(key=lambda x: x.titolo)
        self.save_libro(libro)

    def rimuovi_libro(self, titolo):
        libro = self.cerca_titolo(titolo)
        if libro:
            self.libri.remove(libro)
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
        for libro in self.libri:
            if libro.titolo == titolo:
                return libro
        return None

    def cerca_autore(self, autore):
        for libro in self.libri:
            if libro.autore == autore:
                return libro
        return None

    def presta_libro(self, titolo):
        libro = self.cerca_titolo(titolo)
        if libro and libro.disponibile:
            libro.disponibile = False
            self.update_disponibile(libro)
            return libro
        return None

    def riprendi_libro(self, titolo):
        libro = self.cerca_titolo(titolo)
        if libro and not libro.disponibile:
            libro.disponibile = True
            self.update_disponibile(libro)
            return libro
        return None

    def mostra_catalogo(self):
        return [str(libro) for libro in self.libri]

    def mostra_libri_prestati(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT l.titolo, a.nome, g.nome, l.anno_pubblicazione, l.numero_pagine, l.prezzo
                          FROM libri l
                          JOIN autori a ON l.autore_id = a.id
                          JOIN generi g ON l.genere_id = g.id
                          JOIN libri_prestati lp ON l.id = lp.libro_id''')
        rows = cursor.fetchall()
        libri = []
        for row in rows:
            libro = Libro(row[0], row[1], row[2], row[3], row[4], row[5])
            libro.disponibile = False
            libri.append(libro)
        cursor.close()
        return [str(libro) for libro in libri]

    def mostra_libri_disponibili(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT l.titolo, a.nome, g.nome, l.anno_pubblicazione, l.numero_pagine, l.prezzo
                          FROM libri l
                          JOIN autori a ON l.autore_id = a.id
                          JOIN generi g ON l.genere_id = g.id
                          JOIN libri_disponibili ld ON l.id = ld.libro_id''')
        rows = cursor.fetchall()
        libri = []
        for row in rows:
            libro = Libro(row[0], row[1], row[2], row[3], row[4], row[5])
            libro.disponibile = True
            libri.append(libro)
        cursor.close()
        return [str(libro) for libro in libri]

    def __del__(self):
        if self.conn:
            self.conn.close()

    def modifica_libro(self, titolo_vecchio, nuovo_libro):
        libro = self.cerca_titolo(titolo_vecchio)
        if libro:
            # Rimuovi il vecchio libro dalla lista
            self.libri.remove(libro)
            # Rimuovi dal DB
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM libri WHERE titolo = %s', (titolo_vecchio,))
            libro_id = cursor.fetchone()[0]
            cursor.execute('DELETE FROM libri_disponibili WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri_prestati WHERE libro_id = %s', (libro_id,))
            cursor.execute('DELETE FROM libri WHERE id = %s', (libro_id,))
            self.conn.commit()
            cursor.close()
            # Aggiungi il nuovo libro
            self.aggiungi_libro(nuovo_libro)
            return True
        return False

    def mostra_autori(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT nome FROM autori ORDER BY nome')
        rows = cursor.fetchall()
        autori = [row[0] for row in rows]
        cursor.close()
        return autori

    def mostra_generi(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT nome FROM generi ORDER BY nome')
        rows = cursor.fetchall()
        generi = [row[0] for row in rows]
        cursor.close()
        return generi

class BibliotecaGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.biblioteca = Biblioteca()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Gestione Biblioteca')
        self.setGeometry(300, 300, 800, 600)

        # Imposta il tema chiaro simile ad Apple
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        self.setPalette(palette)

        self.stacked_widget = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Pagina di benvenuto
        self.create_welcome_page()

        # Pagina principale
        self.create_main_page()

        # Applica stili simili ad Apple
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f5f7, stop:1 #e5e5e7);
                color: #1d1d1f;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007aff, stop:1 #0056cc);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px 20px;
                font-size: 16px;
                font-weight: 500;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056cc, stop:1 #004499);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004499, stop:1 #003366);
            }
            QLabel {
                color: #1d1d1f;
                font-size: 18px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #d1d1d6;
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f5f7, stop:1 #e5e5e7);
                border-radius: 15px;
            }
        """)

    def create_welcome_page(self):
        welcome_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(40)  # Spaziatura maggiore per sofisticatezza

        # Sfondo bianco puro come Apple
        welcome_widget.setStyleSheet("background-color: #ffffff;")

        # Spazio iniziale
        layout.addStretch()

        # Icona libro grande
        icon_label = QLabel('📚')
        icon_label.setFont(QFont('Helvetica Neue', 80))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Titolo grande
        title = QLabel('Biblioteca Digitale')
        title.setFont(QFont('Helvetica Neue', 42, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1d1d1f;")
        layout.addWidget(title)

        # Sottotitolo
        subtitle = QLabel('Gestisci i tuoi libri con facilità e stile')
        subtitle.setFont(QFont('Helvetica Neue', 22))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #86868b;")
        layout.addWidget(subtitle)

        # Spazio
        layout.addStretch()

        # Pulsante per entrare, stile Apple
        enter_btn = QPushButton('Inizia')
        enter_btn.setFont(QFont('Helvetica Neue', 20, QFont.Bold))
        enter_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 15px 40px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        enter_btn.clicked.connect(self.show_main_page)
        layout.addWidget(enter_btn, alignment=Qt.AlignCenter)

        # Spazio finale
        layout.addStretch()

        welcome_widget.setLayout(layout)
        self.stacked_widget.addWidget(welcome_widget)

    def create_main_page(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Griglia per pulsanti
        button_grid = QGridLayout()
        button_grid.setSpacing(20)

        self.btn_aggiungi = QPushButton('Aggiungi un Libro')
        self.btn_aggiungi.clicked.connect(self.aggiungi_libro)
        button_grid.addWidget(self.btn_aggiungi, 0, 0)

        self.btn_rimuovi = QPushButton('Rimuovi un Libro')
        self.btn_rimuovi.clicked.connect(self.rimuovi_libro)
        button_grid.addWidget(self.btn_rimuovi, 0, 1)

        self.btn_cerca_titolo = QPushButton('Cerca per Titolo')
        self.btn_cerca_titolo.clicked.connect(self.cerca_titolo)
        button_grid.addWidget(self.btn_cerca_titolo, 1, 0)

        self.btn_cerca_autore = QPushButton('Cerca per Autore')
        self.btn_cerca_autore.clicked.connect(self.cerca_autore)
        button_grid.addWidget(self.btn_cerca_autore, 1, 1)

        self.btn_presta = QPushButton('Presta un Libro')
        self.btn_presta.clicked.connect(self.presta_libro)
        button_grid.addWidget(self.btn_presta, 2, 0)

        self.btn_riprendi = QPushButton('Riprendi un Libro')
        self.btn_riprendi.clicked.connect(self.riprendi_libro)
        button_grid.addWidget(self.btn_riprendi, 2, 1)

        self.btn_mostra_prestati = QPushButton('Visualizza Libri Prestati')
        self.btn_mostra_prestati.clicked.connect(self.mostra_libri_prestati)
        button_grid.addWidget(self.btn_mostra_prestati, 3, 0)

        self.btn_mostra_catalogo = QPushButton('Visualizza Catalogo Completo')
        self.btn_mostra_catalogo.clicked.connect(self.mostra_catalogo)
        button_grid.addWidget(self.btn_mostra_catalogo, 3, 1)

        self.btn_mostra_autori = QPushButton('Visualizza Lista Autori')
        self.btn_mostra_autori.clicked.connect(self.mostra_autori)
        button_grid.addWidget(self.btn_mostra_autori, 4, 0)

        self.btn_modifica = QPushButton('Modifica un Libro')
        self.btn_modifica.clicked.connect(self.modifica_libro)
        button_grid.addWidget(self.btn_modifica, 4, 1)

        # Pulsante indietro
        back_btn = QPushButton('Torna alla Home')
        back_btn.clicked.connect(self.show_welcome_page)
        button_grid.addWidget(back_btn, 5, 0)

        # Pulsante esci
        exit_btn = QPushButton('Esci')
        exit_btn.clicked.connect(self.close)
        button_grid.addWidget(exit_btn, 5, 1)

        layout.addLayout(button_grid)

        main_widget.setLayout(layout)
        self.stacked_widget.addWidget(main_widget)

    def show_welcome_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def aggiungi_libro(self):
        dialog = AddBookDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                titolo, autore, genere, anno, pagine, prezzo = dialog.get_data()
                if titolo and autore and genere and anno and pagine and prezzo:
                    libro = Libro(titolo, autore, genere, int(anno), int(pagine), float(prezzo))
                    self.biblioteca.aggiungi_libro(libro)
                    QMessageBox.information(self, 'Successo', f"Libro '{titolo}' aggiunto alla biblioteca.")
                else:
                    QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori.')
            except ValueError as e:
                QMessageBox.warning(self, 'Errore', f"Dati non validi: {str(e)}. Assicurati che anno, pagine e prezzo siano numeri.")
            except Exception as e:
                QMessageBox.critical(self, 'Errore Database', f"Si è verificato un errore durante l'aggiunta: {str(e)}")

    def rimuovi_libro(self):
        titolo, ok = QInputDialog.getText(self, 'Rimuovi Libro', 'Inserisci il titolo del libro da rimuovere:')
        if ok and titolo:
            if self.biblioteca.rimuovi_libro(titolo):
                QMessageBox.information(self, 'Successo', f"Libro '{titolo}' rimosso dalla biblioteca.")
            else:
                QMessageBox.warning(self, 'Errore', f"Nessun libro trovato con il titolo '{titolo}'.")

    def cerca_titolo(self):
        titolo, ok = QInputDialog.getText(self, 'Cerca per Titolo', 'Inserisci il titolo:')
        if ok and titolo:
            libro = self.biblioteca.cerca_titolo(titolo)
            if libro:
                self.show_result_dialog("Libro trovato", str(libro))
            else:
                self.show_result_dialog("Risultato", f"Nessun libro trovato con il titolo '{titolo}'.")

    def cerca_autore(self):
        autore, ok = QInputDialog.getText(self, 'Cerca per Autore', 'Inserisci l\'autore:')
        if ok and autore:
            libro = self.biblioteca.cerca_autore(autore)
            if libro:
                self.show_result_dialog("Libro trovato", str(libro))
            else:
                self.show_result_dialog("Risultato", f"Nessun libro trovato dell'autore '{autore}'.")

    def presta_libro(self):
        titolo, ok = QInputDialog.getText(self, 'Presta Libro', 'Inserisci il titolo del libro da prestare:')
        if ok and titolo:
            libro = self.biblioteca.presta_libro(titolo)
            if libro:
                self.show_result_dialog("Successo", f"Libro '{libro.titolo}' prestato con successo.")
            else:
                self.show_result_dialog("Errore", f"Il libro '{titolo}' non è disponibile per il prestito.")

    def riprendi_libro(self):
        titolo, ok = QInputDialog.getText(self, 'Riprendi Libro', 'Inserisci il titolo del libro da restituire:')
        if ok and titolo:
            libro = self.biblioteca.riprendi_libro(titolo)
            if libro:
                self.show_result_dialog("Successo", f"Libro '{libro.titolo}' restituito con successo.")
            else:
                self.show_result_dialog("Errore", f"Il libro '{titolo}' non è stato restituito con successo.")

    def mostra_libri_prestati(self):
        try:
            libri = self.biblioteca.mostra_libri_prestati()
            if libri:
                self.show_result_dialog("Libri Prestati", "\n".join(libri))
            else:
                self.show_result_dialog("Libri Prestati", "Nessun libro prestato.")
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def mostra_catalogo(self):
        try:
            libri = self.biblioteca.mostra_catalogo()
            self.show_result_dialog("Catalogo della Biblioteca", "\n".join(libri))
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def mostra_autori(self):
        try:
            autori = self.biblioteca.mostra_autori()
            self.show_result_dialog("Lista degli Autori", "\n".join(autori))
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def show_result_dialog(self, title, content):
        dialog = ResultDialog(title, content, self)
        dialog.exec_()

    def modifica_libro(self):
        titolo, ok = QInputDialog.getText(self, 'Modifica Libro', 'Inserisci il titolo del libro da modificare:')
        if ok and titolo:
            libro = self.biblioteca.cerca_titolo(titolo)
            if libro:
                dialog = EditBookDialog(libro, self)
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        nuovo_titolo, autore, genere, anno, pagine, prezzo = dialog.get_data()
                        if nuovo_titolo and autore and genere and anno and pagine and prezzo:
                            nuovo_libro = Libro(nuovo_titolo, autore, genere, int(anno), int(pagine), float(prezzo))
                            nuovo_libro.disponibile = libro.disponibile  # Mantieni lo stato di disponibilità
                            if self.biblioteca.modifica_libro(titolo, nuovo_libro):
                                QMessageBox.information(self, 'Successo', f"Libro '{titolo}' modificato con successo.")
                            else:
                                QMessageBox.warning(self, 'Errore', 'Errore nella modifica del libro.')
                        else:
                            QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori.')
                    except ValueError as e:
                        QMessageBox.warning(self, 'Errore', f"Dati non validi: {str(e)}. Assicurati che anno, pagine e prezzo siano numeri.")
                    except Exception as e:
                        QMessageBox.critical(self, 'Errore Database', f"Si è verificato un errore durante la modifica: {str(e)}")
            else:
                QMessageBox.warning(self, 'Errore', f"Nessun libro trovato con il titolo '{titolo}'.")

class AddBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Aggiungi Libro')
        self.layout = QFormLayout(self)

        self.titolo_edit = QLineEdit()
        self.layout.addRow('Titolo:', self.titolo_edit)

        self.autore_edit = QLineEdit()
        self.layout.addRow('Autore:', self.autore_edit)

        self.genere_edit = QLineEdit()
        self.layout.addRow('Genere:', self.genere_edit)

        self.anno_edit = QLineEdit()
        self.layout.addRow('Anno Pubblicazione:', self.anno_edit)

        self.pagine_edit = QLineEdit()
        self.layout.addRow('Numero Pagine:', self.pagine_edit)

        self.prezzo_edit = QLineEdit()
        self.layout.addRow('Prezzo:', self.prezzo_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Ok).setAutoDefault(False)
        buttons.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addRow(buttons)

    def get_data(self):
        return (
            self.titolo_edit.text(),
            self.autore_edit.text(),
            self.genere_edit.text(),
            self.anno_edit.text(),
            self.pagine_edit.text(),
            self.prezzo_edit.text()
        )

class EditBookDialog(QDialog):
    def __init__(self, libro, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Modifica Libro')
        self.layout = QFormLayout(self)

        self.titolo_edit = QLineEdit(libro.titolo)
        self.layout.addRow('Titolo:', self.titolo_edit)

        self.autore_edit = QLineEdit(libro.autore)
        self.layout.addRow('Autore:', self.autore_edit)

        self.genere_edit = QLineEdit(libro.genere)
        self.layout.addRow('Genere:', self.genere_edit)

        self.anno_edit = QLineEdit(str(libro.anno_pubblicazione))
        self.layout.addRow('Anno Pubblicazione:', self.anno_edit)

        self.pagine_edit = QLineEdit(str(libro.numero_pagine))
        self.layout.addRow('Numero Pagine:', self.pagine_edit)

        self.prezzo_edit = QLineEdit(str(libro.prezzo))
        self.layout.addRow('Prezzo:', self.prezzo_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Ok).setAutoDefault(False)
        buttons.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addRow(buttons)

    def get_data(self):
        return (
            self.titolo_edit.text(),
            self.autore_edit.text(),
            self.genere_edit.text(),
            self.anno_edit.text(),
            self.pagine_edit.text(),
            self.prezzo_edit.text()
        )

class ResultDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout()

        # Titolo
        title_label = QLabel(title)
        title_label.setFont(QFont('Helvetica Neue', 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Contenuto
        if isinstance(content, list) and content and isinstance(content[0], Libro):
            # Mostra in tabella
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels(['Titolo', 'Autore', 'Genere', 'Anno Pubblicazione', 'Numero Pagine', 'Prezzo', 'Disponibile'])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setRowCount(len(content))
            for row, libro in enumerate(content):
                table.setItem(row, 0, QTableWidgetItem(libro.titolo))
                table.setItem(row, 1, QTableWidgetItem(libro.autore))
                table.setItem(row, 2, QTableWidgetItem(libro.genere))
                table.setItem(row, 3, QTableWidgetItem(str(libro.anno_pubblicazione)))
                table.setItem(row, 4, QTableWidgetItem(str(libro.numero_pagine)))
                table.setItem(row, 5, QTableWidgetItem(f"€{libro.prezzo:.2f}"))
                table.setItem(row, 6, QTableWidgetItem('Sì' if libro.disponibile else 'No'))
            layout.addWidget(table)
        else:
            # Mostra come testo
            content_area = QTextEdit()
            content_area.setPlainText(str(content))
            content_area.setReadOnly(True)
            content_area.setFont(QFont('Helvetica Neue', 14))
            layout.addWidget(content_area)

        # Pulsante Chiudi
        close_btn = QPushButton('Chiudi')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = BibliotecaGUI()
    gui.show()
    sys.exit(app.exec_())
