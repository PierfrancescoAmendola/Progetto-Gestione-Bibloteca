"""
Modulo per l'interfaccia grafica dell'applicazione biblioteca
"""

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDialog, QDialogButtonBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QScrollArea, QGridLayout, QFormLayout, QStackedWidget,
    QMenu, QMessageBox, QInputDialog, QHeaderView, QCheckBox, QSpinBox,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
import sys
import hashlib

from database import DatabaseManager
from models import Libro
from utils import (
    get_input_stylesheet, get_combobox_stylesheet,
    get_primary_button_stylesheet, get_secondary_button_stylesheet
)


class ResultDialog(QDialog):
    """Dialog per mostrare risultati di operazioni"""

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


class AddBookDialog(QDialog):
    """Dialog per aggiungere un nuovo libro"""

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
    """Dialog per modificare un libro esistente"""

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


class BibliotecaGUI(QWidget):
    """Classe principale per l'interfaccia grafica"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_user = None  # Utente attualmente loggato
        self.current_role = None  # Ruolo attualmente selezionato
        self.libri = []  # Cache dei libri
        self.carrello = []  # Carrello acquisti
        self.initUI()

    def initUI(self):
        """Inizializza l'interfaccia utente"""
        self.setWindowTitle('Gestione Biblioteca')
        self.setGeometry(200, 100, 1400, 900)  # Allargata per migliore visualizzazione

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

        # Pagina di login
        self.create_login_page()

        # Pagina di registrazione
        self.create_register_page()

        # Pagina di ricerca per utenti
        self.create_user_search_page()

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
        """Crea la pagina di benvenuto"""
        welcome_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(40)

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
        subtitle = QLabel('Seleziona il tuo ruolo per accedere al sistema')
        subtitle.setFont(QFont('Helvetica Neue', 22))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #86868b;")
        layout.addWidget(subtitle)

        # Spazio
        layout.addStretch()

        # Pulsanti per selezione ruolo
        button_layout = QVBoxLayout()
        button_layout.setSpacing(20)

        # Pulsante Bibliotecario
        bibliotecario_btn = QPushButton('Accedi come Bibliotecario')
        bibliotecario_btn.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        bibliotecario_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        bibliotecario_btn.clicked.connect(lambda: self.show_login_page('bibliotecario'))
        button_layout.addWidget(bibliotecario_btn, alignment=Qt.AlignCenter)

        # Pulsante Libraio
        libraio_btn = QPushButton('Accedi come Libraio')
        libraio_btn.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        libraio_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #28a745;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        libraio_btn.clicked.connect(lambda: self.show_login_page('libraio'))
        button_layout.addWidget(libraio_btn, alignment=Qt.AlignCenter)

        # Pulsante Utente
        utente_btn = QPushButton('Accedi come Utente')
        utente_btn.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        utente_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9500;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #e8890b;
            }
            QPushButton:pressed {
                background-color: #d97706;
            }
        """)
        utente_btn.clicked.connect(lambda: self.show_login_page('utente'))
        button_layout.addWidget(utente_btn, alignment=Qt.AlignCenter)

        layout.addLayout(button_layout)

        # Spazio finale
        layout.addStretch()

        welcome_widget.setLayout(layout)
        self.stacked_widget.addWidget(welcome_widget)

    def create_login_page(self):
        """Crea la pagina di login"""
        self.login_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)

        self.login_widget.setStyleSheet("background-color: #ffffff;")

        # Spazio iniziale
        layout.addStretch()

        # Titolo
        self.login_title = QLabel('Accedi al Sistema')
        self.login_title.setFont(QFont('Helvetica Neue', 36, QFont.Bold))
        self.login_title.setAlignment(Qt.AlignCenter)
        self.login_title.setStyleSheet("color: #1d1d1f;")
        layout.addWidget(self.login_title)

        # Ruolo selezionato
        self.login_role_label = QLabel('')
        self.login_role_label.setFont(QFont('Helvetica Neue', 18))
        self.login_role_label.setAlignment(Qt.AlignCenter)
        self.login_role_label.setStyleSheet("color: #86868b;")
        layout.addWidget(self.login_role_label)

        # Spazio
        layout.addStretch()

        # Form di login
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        # Campo Email/Nome Utente
        self.login_username_edit = QLineEdit()
        self.login_username_edit.setPlaceholderText('Email o Nome Utente')
        self.login_username_edit.setFont(QFont('Helvetica Neue', 16))
        self.login_username_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d1d6;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border-color: #007aff;
            }
        """)
        form_layout.addWidget(QLabel('Email o Nome Utente:', font=QFont('Helvetica Neue', 14, QFont.Bold)))
        form_layout.addWidget(self.login_username_edit)

        # Campo Password
        self.login_password_edit = QLineEdit()
        self.login_password_edit.setPlaceholderText('Password')
        self.login_password_edit.setEchoMode(QLineEdit.Password)
        self.login_password_edit.setFont(QFont('Helvetica Neue', 16))
        self.login_password_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d1d6;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border-color: #007aff;
            }
        """)
        form_layout.addWidget(QLabel('Password:', font=QFont('Helvetica Neue', 14, QFont.Bold)))
        form_layout.addWidget(self.login_password_edit)

        layout.addLayout(form_layout)

        # Spazio
        layout.addStretch()

        # Pulsanti
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)

        # Pulsante Accedi
        self.login_btn = QPushButton('Accedi')
        self.login_btn.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 15px 40px;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        self.login_btn.clicked.connect(self.perform_login)
        button_layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)

        # Link per registrazione
        register_label = QLabel('Non sei registrato? <a href="#" style="color: #007aff; text-decoration: none;">Clicca qui e registrati</a>')
        register_label.setFont(QFont('Helvetica Neue', 14))
        register_label.setAlignment(Qt.AlignCenter)
        register_label.setOpenExternalLinks(False)
        register_label.linkActivated.connect(self.show_register_page)
        button_layout.addWidget(register_label, alignment=Qt.AlignCenter)

        # Pulsante indietro
        back_btn = QPushButton('Torna alla Home')
        back_btn.setFont(QFont('Helvetica Neue', 14))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #86868b;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #007aff;
            }
        """)
        back_btn.clicked.connect(self.show_welcome_page)
        button_layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        layout.addLayout(button_layout)

        # Spazio finale
        layout.addStretch()

        self.login_widget.setLayout(layout)
        self.stacked_widget.addWidget(self.login_widget)

    def show_login_page(self, role):
        """Mostra la pagina di login per un ruolo specifico"""
        self.current_role = role
        role_names = {
            'bibliotecario': 'Bibliotecario',
            'libraio': 'Libraio',
            'utente': 'Utente'
        }
        self.login_title.setText(f'Accedi come {role_names[role]}')
        self.login_role_label.setText(f'Ruolo selezionato: {role_names[role]}')
        self.login_username_edit.clear()
        self.login_password_edit.clear()
        self.stacked_widget.setCurrentWidget(self.login_widget)

    def perform_login(self):
        """Esegue il login"""
        username = self.login_username_edit.text().strip()
        password = self.login_password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, 'Errore', 'Inserisci email/nome utente e password.')
            return

        user = self.db.login(username, password)

        if user:
            self.current_user = user
            QMessageBox.information(self, 'Successo', f"Benvenuto {user['nome']} {user['cognome']}!")
            self.show_main_page()
        else:
            QMessageBox.warning(self, 'Errore', 'Credenziali non valide')

    def create_register_page(self):
        """Crea la pagina di registrazione"""
        self.register_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Sfondo con gradiente sottile come Apple
        self.register_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f5f5f7);
            }
        """)

        # Scroll area principale
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(25)
        scroll_layout.setContentsMargins(0, 0, 0, 20)

        # Header elegante
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)

        # Titolo principale
        self.register_title = QLabel('Crea il tuo account')
        self.register_title.setFont(QFont('SF Pro Display', 28, QFont.Bold))
        self.register_title.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                background: transparent;
            }
        """)
        self.register_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.register_title)

        # Sottotitolo
        self.register_subtitle = QLabel('Compila i campi per registrarti al sistema')
        self.register_subtitle.setFont(QFont('SF Pro Text', 16))
        self.register_subtitle.setStyleSheet("""
            QLabel {
                color: #86868b;
                background: transparent;
            }
        """)
        self.register_subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.register_subtitle)

        scroll_layout.addLayout(header_layout)

        # Sezione Informazioni Personali
        personal_section, personal_container = self.create_form_section("👤 Informazioni Personali")
        personal_layout = QGridLayout()
        personal_layout.setSpacing(15)
        personal_layout.setContentsMargins(20, 20, 20, 20)

        # Email
        email_label = QLabel('Email')
        email_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        email_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_email_edit = QLineEdit()
        self.register_email_edit.setPlaceholderText('esempio@email.com')
        self.register_email_edit.setFont(QFont('SF Pro Text', 16))
        self.register_email_edit.setMinimumHeight(44)
        self.register_email_edit.setStyleSheet(get_input_stylesheet())
        personal_layout.addWidget(email_label, 0, 0)
        personal_layout.addWidget(self.register_email_edit, 1, 0)

        # Nome Utente
        username_label = QLabel('Nome Utente')
        username_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        username_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_username_edit = QLineEdit()
        self.register_username_edit.setPlaceholderText('nome_utente')
        self.register_username_edit.setFont(QFont('SF Pro Text', 16))
        self.register_username_edit.setMinimumHeight(44)
        self.register_username_edit.setStyleSheet(get_input_stylesheet())
        personal_layout.addWidget(username_label, 0, 1)
        personal_layout.addWidget(self.register_username_edit, 1, 1)

        # Nome
        nome_label = QLabel('Nome')
        nome_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        nome_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_nome_edit = QLineEdit()
        self.register_nome_edit.setPlaceholderText('Il tuo nome')
        self.register_nome_edit.setFont(QFont('SF Pro Text', 16))
        self.register_nome_edit.setMinimumHeight(44)
        self.register_nome_edit.setStyleSheet(get_input_stylesheet())
        personal_layout.addWidget(nome_label, 2, 0)
        personal_layout.addWidget(self.register_nome_edit, 3, 0)

        # Cognome
        cognome_label = QLabel('Cognome')
        cognome_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        cognome_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_cognome_edit = QLineEdit()
        self.register_cognome_edit.setPlaceholderText('Il tuo cognome')
        self.register_cognome_edit.setFont(QFont('SF Pro Text', 16))
        self.register_cognome_edit.setMinimumHeight(44)
        self.register_cognome_edit.setStyleSheet(get_input_stylesheet())
        personal_layout.addWidget(cognome_label, 2, 1)
        personal_layout.addWidget(self.register_cognome_edit, 3, 1)

        personal_container.setLayout(personal_layout)
        scroll_layout.addWidget(personal_section)

        # Sezione Sicurezza
        security_section, security_container = self.create_form_section("🔒 Sicurezza")
        security_layout = QVBoxLayout()
        security_layout.setSpacing(15)
        security_layout.setContentsMargins(20, 20, 20, 20)

        # Password
        password_label = QLabel('Password')
        password_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        password_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_password_edit = QLineEdit()
        self.register_password_edit.setPlaceholderText('Crea una password sicura')
        self.register_password_edit.setEchoMode(QLineEdit.Password)
        self.register_password_edit.setFont(QFont('SF Pro Text', 16))
        self.register_password_edit.setMinimumHeight(44)
        self.register_password_edit.setStyleSheet(get_input_stylesheet())
        security_layout.addWidget(password_label)
        security_layout.addWidget(self.register_password_edit)

        # Conferma Password
        confirm_label = QLabel('Conferma Password')
        confirm_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        confirm_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_confirm_password_edit = QLineEdit()
        self.register_confirm_password_edit.setPlaceholderText('Ripeti la password')
        self.register_confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.register_confirm_password_edit.setFont(QFont('SF Pro Text', 16))
        self.register_confirm_password_edit.setMinimumHeight(44)
        self.register_confirm_password_edit.setStyleSheet(get_input_stylesheet())
        security_layout.addWidget(confirm_label)
        security_layout.addWidget(self.register_confirm_password_edit)

        security_container.setLayout(security_layout)
        scroll_layout.addWidget(security_section)

        # Sezione Ruolo
        role_section, role_container = self.create_form_section("👔 Tipo di Account")
        role_layout = QVBoxLayout()
        role_layout.setSpacing(15)
        role_layout.setContentsMargins(20, 20, 20, 20)

        # ComboBox per il ruolo
        role_label = QLabel('Seleziona il tuo ruolo')
        role_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        role_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_role_combo = QComboBox()
        self.register_role_combo.addItems(['🎓 Studente', '🏛️ Bibliotecario', '📚 Libraio'])
        self.register_role_combo.setFont(QFont('SF Pro Text', 16))
        self.register_role_combo.setMinimumHeight(44)
        self.register_role_combo.setStyleSheet(get_combobox_stylesheet())
        self.register_role_combo.currentTextChanged.connect(self.on_role_changed)
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.register_role_combo)

        # ComboBox per la città (inizialmente nascosto)
        self.register_citta_label = QLabel('Città di riferimento')
        self.register_citta_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        self.register_citta_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_citta_combo = QComboBox()
        self.register_citta_combo.setFont(QFont('SF Pro Text', 16))
        self.register_citta_combo.setMinimumHeight(44)
        self.register_citta_combo.setStyleSheet(get_combobox_stylesheet())
        self.register_citta_combo.currentTextChanged.connect(self.on_citta_changed)
        self.register_citta_label.hide()
        self.register_citta_combo.hide()
        role_layout.addWidget(self.register_citta_label)
        role_layout.addWidget(self.register_citta_combo)

        # Campo struttura (inizialmente nascosto)
        self.register_struttura_label = QLabel('Biblioteca di riferimento')
        self.register_struttura_label.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        self.register_struttura_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        self.register_struttura_combo = QComboBox()
        self.register_struttura_combo.setFont(QFont('SF Pro Text', 16))
        self.register_struttura_combo.setMinimumHeight(44)
        self.register_struttura_combo.setStyleSheet(get_combobox_stylesheet())
        self.register_struttura_label.hide()
        self.register_struttura_combo.hide()
        role_layout.addWidget(self.register_struttura_label)
        role_layout.addWidget(self.register_struttura_combo)

        role_container.setLayout(role_layout)
        scroll_layout.addWidget(role_section)

        # Spazio
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Footer con pulsanti
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(20)

        # Pulsante Registrati
        self.register_btn = QPushButton('Crea Account')
        self.register_btn.setFont(QFont('SF Pro Text', 18, QFont.Bold))
        self.register_btn.setMinimumHeight(50)
        self.register_btn.setStyleSheet(get_primary_button_stylesheet())
        self.register_btn.clicked.connect(self.perform_registration)
        footer_layout.addWidget(self.register_btn)

        # Link per tornare al login
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        back_label = QLabel('Hai già un account?')
        back_label.setFont(QFont('SF Pro Text', 14))
        back_label.setStyleSheet("color: #86868b; background: transparent;")
        back_btn = QPushButton('Accedi')
        back_btn.setFont(QFont('SF Pro Text', 14, QFont.Medium))
        back_btn.setStyleSheet("""
            QPushButton {
                color: #007aff;
                background: transparent;
                border: none;
                text-decoration: underline;
                padding: 0;
            }
            QPushButton:hover {
                color: #0056cc;
            }
        """)
        back_btn.clicked.connect(lambda: self.show_login_page(self.current_role) if self.current_role else self.show_welcome_page())
        back_layout.addWidget(back_label)
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        footer_layout.addLayout(back_layout)

        layout.addLayout(footer_layout)

        self.register_widget.setLayout(layout)
        self.stacked_widget.addWidget(self.register_widget)

    def on_role_changed(self, role):
        """Gestisce il cambio di ruolo nella registrazione"""
        if role in ['🏛️ Bibliotecario', '📚 Libraio']:
            # Mostra il combo città
            self.register_citta_label.show()
            self.register_citta_combo.show()

            # Popola il combo città
            citta = self.db.get_citta()
            self.register_citta_combo.clear()
            if citta:
                for c in citta:
                    self.register_citta_combo.addItem(f"{c[1]} ({c[2]})", c[0])  # ID come data, "Nome (Regione)" come testo
            else:
                self.register_citta_combo.addItem('Nessuna città disponibile', None)

            # Nascondi il combo struttura fino a quando non viene selezionata una città
            self.register_struttura_label.hide()
            self.register_struttura_combo.hide()
        else:
            # Per studenti, nascondi tutto
            self.register_citta_label.hide()
            self.register_citta_combo.hide()
            self.register_struttura_label.hide()
            self.register_struttura_combo.hide()

    def on_citta_changed(self, citta_text):
        """Gestisce il cambio di città nella registrazione"""
        citta_id = self.register_citta_combo.currentData()
        role = self.register_role_combo.currentText()

        if citta_id is not None and role in ['🏛️ Bibliotecario', '📚 Libraio']:
            if role == '🏛️ Bibliotecario':
                self.register_struttura_label.setText('Biblioteca di riferimento')
                strutture = self.db.get_biblioteche_by_citta(citta_id)
            else:  # Libraio
                self.register_struttura_label.setText('Libreria di riferimento')
                strutture = self.db.get_librerie_by_citta(citta_id)

            self.register_struttura_combo.clear()
            if strutture:
                for struttura in strutture:
                    self.register_struttura_combo.addItem(struttura[1], struttura[0])
            else:
                self.register_struttura_combo.addItem('Nessuna struttura disponibile in questa città', None)

            self.register_struttura_label.show()
            self.register_struttura_combo.show()
        else:
            self.register_struttura_label.hide()
            self.register_struttura_combo.hide()

    def show_register_page(self):
        """Mostra la pagina di registrazione"""
        role_names = {
            'bibliotecario': 'Bibliotecario',
            'libraio': 'Libraio',
            'utente': 'Utente'
        }
        if self.current_role:
            self.register_title.setText(f'Registrazione Nuovo {role_names[self.current_role]}')
            self.register_subtitle.setText(f'Compila i campi per registrarti come {role_names[self.current_role].lower()}')
            # Imposta il ruolo di default nel combo box
            if self.current_role == 'bibliotecario':
                self.register_role_combo.setCurrentText('🏛️ Bibliotecario')
            elif self.current_role == 'libraio':
                self.register_role_combo.setCurrentText('📚 Libraio')
            else:
                self.register_role_combo.setCurrentText('🎓 Studente')
        else:
            self.register_title.setText('Crea il tuo account')
            self.register_subtitle.setText('Compila i campi per registrarti al sistema')

        # Pulisci tutti i campi
        self.register_email_edit.clear()
        self.register_username_edit.clear()
        self.register_nome_edit.clear()
        self.register_cognome_edit.clear()
        self.register_password_edit.clear()
        self.register_confirm_password_edit.clear()

        self.stacked_widget.setCurrentWidget(self.register_widget)

    def perform_registration(self):
        """Esegue la registrazione"""
        # Raccogli i dati dal form
        email = self.register_email_edit.text().strip()
        username = self.register_username_edit.text().strip()
        nome = self.register_nome_edit.text().strip()
        cognome = self.register_cognome_edit.text().strip()
        password = self.register_password_edit.text()
        confirm_password = self.register_confirm_password_edit.text()
        ruolo_selezionato = self.register_role_combo.currentText()

        # Validazione dei dati
        if not all([email, username, nome, cognome, password, confirm_password]):
            QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori.')
            return

        if password != confirm_password:
            QMessageBox.warning(self, 'Errore', 'Le password non coincidono.')
            return

        if len(password) < 6:
            QMessageBox.warning(self, 'Errore', 'La password deve essere di almeno 6 caratteri.')
            return

        # Mappa il ruolo selezionato al formato del database
        role_mapping = {
            '🎓 Studente': 'utente',
            '🏛️ Bibliotecario': 'bibliotecario',
            '📚 Libraio': 'libraio'
        }
        ruolo = role_mapping.get(ruolo_selezionato)

        if not ruolo:
            QMessageBox.warning(self, 'Errore', 'Ruolo non valido.')
            return

        # Gestisci la struttura se necessaria
        struttura_id = None
        if ruolo in ['bibliotecario', 'libraio']:
            struttura_selezionata = self.register_struttura_combo.currentData()
            if struttura_selezionata is None:
                struttura_name = "biblioteca" if ruolo == 'bibliotecario' else "libreria"
                QMessageBox.warning(self, 'Errore', f'Seleziona una {struttura_name} valida.')
                return
            struttura_id = struttura_selezionata

        # Effettua la registrazione
        success, message = self.db.registra_utente(
            email, username, nome, cognome, password, ruolo, struttura_id
        )

        if success:
            QMessageBox.information(self, 'Successo', message)
            # Torna alla pagina di login
            self.show_login_page(self.current_role)
        else:
            QMessageBox.warning(self, 'Errore', message)

    def perform_logout(self):
        """Esegue il logout"""
        reply = QMessageBox.question(self, 'Conferma Logout',
                                   'Sei sicuro di voler effettuare il logout?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.current_user = None
            self.current_role = None
            QMessageBox.information(self, 'Logout', 'Logout effettuato con successo.')
            self.show_welcome_page()

    def create_user_search_page(self):
        """Crea la pagina di ricerca per gli utenti normali"""
        self.user_search_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Sfondo con gradiente
        self.user_search_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f5f5f7);
            }
        """)

        # Header con menu utente
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # Informazioni utente a sinistra
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(5)

        welcome_label = QLabel(f'Benvenuto, {self.current_user["nome"] if self.current_user else "Utente"}!')
        welcome_label.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        welcome_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        user_info_layout.addWidget(welcome_label)

        subtitle_label = QLabel('Cerca e prenota i libri che ti interessano')
        subtitle_label.setFont(QFont('SF Pro Text', 16))
        subtitle_label.setStyleSheet("color: #86868b; background: transparent;")
        user_info_layout.addWidget(subtitle_label)

        header_layout.addLayout(user_info_layout)
        header_layout.addStretch()

        # Menu utente a destra
        self.create_user_menu()
        header_layout.addWidget(self.user_menu_widget)

        layout.addLayout(header_layout)

        # Sezione di ricerca
        search_section, search_container = self.create_form_section("🔍 Cerca Libri")
        search_layout = QVBoxLayout()
        search_layout.setSpacing(20)
        search_layout.setContentsMargins(25, 25, 25, 25)

        # Selezione città
        citta_layout = QHBoxLayout()
        citta_layout.setSpacing(15)

        citta_label = QLabel('Seleziona la città:')
        citta_label.setFont(QFont('SF Pro Text', 16, QFont.Medium))
        citta_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        citta_layout.addWidget(citta_label)

        self.search_citta_combo = QComboBox()
        self.search_citta_combo.setFont(QFont('SF Pro Text', 16))
        self.search_citta_combo.setMinimumHeight(44)
        self.search_citta_combo.setStyleSheet(get_combobox_stylesheet())
        self.search_citta_combo.currentTextChanged.connect(self.on_search_citta_changed)
        citta_layout.addWidget(self.search_citta_combo)

        citta_layout.addStretch()
        search_layout.addLayout(citta_layout)

        # Tipo di struttura
        type_layout = QHBoxLayout()
        type_layout.setSpacing(15)

        type_label = QLabel('Cerca in:')
        type_label.setFont(QFont('SF Pro Text', 16, QFont.Medium))
        type_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        type_layout.addWidget(type_label)

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(['🏛️ Biblioteca', '📚 Libreria'])
        self.search_type_combo.setFont(QFont('SF Pro Text', 16))
        self.search_type_combo.setMinimumHeight(44)
        self.search_type_combo.setStyleSheet(get_combobox_stylesheet())
        self.search_type_combo.currentTextChanged.connect(self.on_search_type_changed)
        type_layout.addWidget(self.search_type_combo)

        type_layout.addStretch()
        search_layout.addLayout(type_layout)

        # Selezione struttura specifica
        structure_layout = QHBoxLayout()
        structure_layout.setSpacing(15)

        self.structure_label = QLabel('Biblioteca:')
        self.structure_label.setFont(QFont('SF Pro Text', 16, QFont.Medium))
        self.structure_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        structure_layout.addWidget(self.structure_label)

        self.search_structure_combo = QComboBox()
        self.search_structure_combo.setFont(QFont('SF Pro Text', 16))
        self.search_structure_combo.setMinimumHeight(44)
        self.search_structure_combo.setStyleSheet(get_combobox_stylesheet())
        structure_layout.addWidget(self.search_structure_combo)

        structure_layout.addStretch()
        search_layout.addLayout(structure_layout)

        # Barra di ricerca
        search_bar_layout = QVBoxLayout()
        search_bar_layout.setSpacing(10)

        search_label = QLabel('Cosa stai cercando?')
        search_label.setFont(QFont('SF Pro Text', 16, QFont.Medium))
        search_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        search_bar_layout.addWidget(search_label)

        search_input_layout = QHBoxLayout()
        search_input_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Titolo, autore o genere del libro...')
        self.search_input.setFont(QFont('SF Pro Text', 18))
        self.search_input.setMinimumHeight(50)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d1d6;
                border-radius: 25px;
                padding: 12px 20px;
                background: white;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border-color: #007aff;
                background: #f8f9fa;
            }
            QLineEdit::placeholder {
                color: #8e8e93;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        search_input_layout.addWidget(self.search_input)

        search_btn = QPushButton('🔍 Cerca')
        search_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        search_btn.setMinimumHeight(50)
        search_btn.setMinimumWidth(120)
        search_btn.setStyleSheet(get_primary_button_stylesheet())
        search_btn.clicked.connect(self.perform_search)
        search_input_layout.addWidget(search_btn)

        search_bar_layout.addLayout(search_input_layout)
        search_layout.addLayout(search_bar_layout)

        search_container.setLayout(search_layout)
        layout.addWidget(search_section)

        # Area risultati (inizialmente nascosta)
        self.results_section, self.results_container = self.create_form_section("📚 Risultati della Ricerca")
        self.results_section.hide()

        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(15, 15, 15, 15)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(15)  # Maggiore spaziatura per migliore visualizzazione

        self.results_scroll.setWidget(self.results_widget)
        results_layout.addWidget(self.results_scroll)

        self.results_container.setLayout(results_layout)
        layout.addWidget(self.results_section)

        # Footer con logout
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        logout_btn = QPushButton('Logout')
        logout_btn.setFont(QFont('SF Pro Text', 14))
        logout_btn.setStyleSheet("""
            QPushButton {
                color: #86868b;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #007aff;
            }
        """)
        logout_btn.clicked.connect(self.perform_logout)
        footer_layout.addWidget(logout_btn)

        layout.addLayout(footer_layout)

        self.user_search_widget.setLayout(layout)
        self.stacked_widget.addWidget(self.user_search_widget)

        # Inizializza la selezione struttura
        self.populate_search_citta()
        self.on_search_citta_changed(self.search_citta_combo.currentText())

    def populate_search_citta(self):
        """Popola il combo delle città per la ricerca"""
        citta = self.db.get_citta()
        self.search_citta_combo.clear()
        if citta:
            for c in citta:
                self.search_citta_combo.addItem(f"{c[1]} ({c[2]})", c[0])
        else:
            self.search_citta_combo.addItem('Nessuna città disponibile', None)

    def on_search_citta_changed(self, citta_text):
        """Aggiorna la selezione struttura quando cambia la città"""
        citta_id = self.search_citta_combo.currentData()
        search_type = self.search_type_combo.currentText()

        if citta_id is not None:
            if search_type == '🏛️ Biblioteca':
                self.structure_label.setText('Biblioteca:')
                strutture = self.db.get_biblioteche_by_citta(citta_id)
            else:  # Libreria
                self.structure_label.setText('Libreria:')
                strutture = self.db.get_librerie_by_citta(citta_id)

            self.search_structure_combo.clear()
            if strutture:
                for struttura in strutture:
                    self.search_structure_combo.addItem(struttura[1], struttura[0])
            else:
                self.search_structure_combo.addItem('Nessuna struttura disponibile in questa città', None)
        else:
            self.search_structure_combo.clear()
            self.search_structure_combo.addItem('Seleziona prima una città', None)

    def on_search_type_changed(self, search_type):
        """Aggiorna la selezione struttura quando cambia il tipo"""
        # Questo metodo ora viene chiamato da on_search_citta_changed
        self.on_search_citta_changed(self.search_citta_combo.currentText())

    def perform_search(self):
        """Esegue la ricerca dei libri"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, 'Ricerca vuota', 'Inserisci un termine di ricerca.')
            return

        struttura_id = self.search_structure_combo.currentData()
        if struttura_id is None:
            QMessageBox.warning(self, 'Struttura non selezionata', 'Seleziona una struttura valida.')
            return

        # Qui dovrei implementare la ricerca nel database
        # Per ora mostro un messaggio di placeholder
        self.show_search_results(query, struttura_id)

    def show_search_results(self, query, struttura_id):
        """Mostra i risultati della ricerca"""
        # Pulisci risultati precedenti
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Carica libri dal database invece di usare mock data
        try:
            libri = self.db.load_libri()
            # Filtra libri per query se presente
            if query:
                libri_filtrati = []
                query_lower = query.lower()
                for libro in libri:
                    if (query_lower in libro.titolo.lower() or
                        query_lower in libro.autore.lower() or
                        query_lower in libro.genere.lower()):
                        libri_filtrati.append(libro)
                libri = libri_filtrati

            if not libri:
                no_results_label = QLabel("Nessun libro trovato per la ricerca effettuata.")
                no_results_label.setFont(QFont('SF Pro Text', 16))
                no_results_label.setStyleSheet("color: #86868b; text-align: center;")
                no_results_label.setAlignment(Qt.AlignCenter)
                self.results_layout.addWidget(no_results_label)
            else:
                for libro in libri:
                    book_card = self.create_purchase_book_card(libro)
                    self.results_layout.addWidget(book_card)

        except Exception as e:
            error_label = QLabel(f"Errore nel caricamento dei libri: {str(e)}")
            error_label.setFont(QFont('SF Pro Text', 16))
            error_label.setStyleSheet("color: #ff3b30; text-align: center;")
            error_label.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(error_label)

        self.results_section.show()

    def create_purchase_book_card(self, libro):
        """Crea una card elegante per un libro con funzionalità di acquisto"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e5e7;
                margin: 5px;
            }
            QWidget:hover {
                border-color: #007aff;
                background: #f8f9fa;
            }
        """)
        card.setMinimumHeight(200)  # Altezza aumentata per i nuovi controlli
        card.setMinimumWidth(650)   # Larghezza aumentata

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Icona libro
        icon_label = QLabel('📖')
        icon_label.setFont(QFont('SF Pro Text', 48))
        icon_label.setFixedSize(60, 60)
        layout.addWidget(icon_label)

        # Informazioni libro
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Titolo
        title_label = QLabel(libro.titolo)
        title_label.setFont(QFont('SF Pro Display', 18, QFont.Bold))
        title_label.setStyleSheet("color: #1d1d1f;")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        # Autore e genere
        author_genre = QLabel(f"di {libro.autore} • {libro.genere}")
        author_genre.setFont(QFont('SF Pro Text', 14))
        author_genre.setStyleSheet("color: #86868b;")
        author_genre.setWordWrap(True)
        info_layout.addWidget(author_genre)

        # Dettagli
        details = QLabel(f"{libro.anno_pubblicazione} • {libro.numero_pagine} pagine")
        details.setFont(QFont('SF Pro Text', 14))
        details.setStyleSheet("color: #1d1d1f;")
        info_layout.addWidget(details)

        # Descrizione se presente
        if libro.descrizione:
            desc = QLabel(libro.descrizione[:100] + "..." if len(libro.descrizione) > 100 else libro.descrizione)
            desc.setFont(QFont('SF Pro Text', 12))
            desc.setStyleSheet("color: #86868b;")
            desc.setWordWrap(True)
            info_layout.addWidget(desc)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Sezione prezzi e acquisto
        purchase_layout = QVBoxLayout()
        purchase_layout.setSpacing(12)

        # Prezzi
        price_layout = QVBoxLayout()
        price_layout.setSpacing(5)

        # Prezzo nuovo
        if libro.prezzo_nuovo:
            nuovo_price = QLabel(f"🆕 Nuovo: €{libro.prezzo_nuovo:.2f}")
            nuovo_price.setFont(QFont('SF Pro Text', 14, QFont.Bold))
            nuovo_price.setStyleSheet("color: #34c759;")
            price_layout.addWidget(nuovo_price)

        # Prezzo usato
        if libro.prezzo_usato:
            usato_price = QLabel(f"♻️ Usato: €{libro.prezzo_usato:.2f}")
            usato_price.setFont(QFont('SF Pro Text', 14, QFont.Bold))
            usato_price.setStyleSheet("color: #ff9500;")
            price_layout.addWidget(usato_price)

        # Prezzo base se non ci sono prezzi specifici
        if not libro.prezzo_nuovo and not libro.prezzo_usato:
            base_price = QLabel(f"Prezzo: €{libro.prezzo:.2f}")
            base_price.setFont(QFont('SF Pro Text', 14, QFont.Bold))
            base_price.setStyleSheet("color: #1d1d1f;")
            price_layout.addWidget(base_price)

        purchase_layout.addLayout(price_layout)

        # Controlli acquisto
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)

        # Selezione condizione
        condition_layout = QHBoxLayout()
        condition_layout.setSpacing(10)

        condition_label = QLabel('Condizione:')
        condition_label.setFont(QFont('SF Pro Text', 12))
        condition_layout.addWidget(condition_label)

        condition_combo = QComboBox()
        condition_combo.setFont(QFont('SF Pro Text', 12))
        condition_combo.setFixedWidth(100)

        # Aggiungi opzioni basate sui prezzi disponibili
        if libro.prezzo_nuovo:
            condition_combo.addItem('Nuovo', 'nuovo')
        if libro.prezzo_usato:
            condition_combo.addItem('Usato', 'usato')

        if condition_combo.count() == 0:
            condition_combo.addItem('Standard', 'standard')

        condition_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 4px 8px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #86868b;
                margin-right: 8px;
            }
        """)
        condition_layout.addWidget(condition_combo)

        condition_layout.addStretch()
        controls_layout.addLayout(condition_layout)

        # Quantità e pulsante acquisto
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        # Spinner quantità
        qty_label = QLabel('Q.tà:')
        qty_label.setFont(QFont('SF Pro Text', 12))
        action_layout.addWidget(qty_label)

        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setMaximum(10)
        qty_spin.setValue(1)
        qty_spin.setFixedWidth(60)
        qty_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 4px;
                background: white;
            }
        """)
        action_layout.addWidget(qty_spin)

        # Pulsante aggiungi al carrello
        add_cart_btn = QPushButton('� Aggiungi al Carrello')
        add_cart_btn.setFont(QFont('SF Pro Text', 12, QFont.Bold))
        add_cart_btn.setMinimumHeight(35)
        add_cart_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007aff, stop:1 #0056cc);
                color: white;
                border: none;
                border-radius: 17px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056cc, stop:1 #004499);
            }
        """)
        add_cart_btn.clicked.connect(lambda: self.aggiungi_al_carrello(libro, condition_combo.currentData(), qty_spin.value()))
        action_layout.addWidget(add_cart_btn)

        action_layout.addStretch()
        controls_layout.addLayout(action_layout)

        purchase_layout.addLayout(controls_layout)
        purchase_layout.addStretch()

        layout.addLayout(purchase_layout)

        return card

    def prenota_libro(self, titolo):
        """Gestisce la prenotazione di un libro"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per prenotare libri.')
            return

        reply = QMessageBox.question(
            self, 'Conferma Prenotazione',
            f'Vuoi prenotare il libro "{titolo}"?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.db.prenota_libro(self.current_user['id'], titolo)
            if success:
                QMessageBox.information(self, 'Prenotazione Confermata', message)
                # Aggiorna i risultati della ricerca
                self.perform_search()
            else:
                QMessageBox.warning(self, 'Errore', message)

    def aggiungi_a_lista_attesa(self, titolo):
        """Aggiunge un libro alla lista d'attesa"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per aggiungere libri alla lista d\'attesa.')
            return

        reply = QMessageBox.question(
            self, 'Conferma Lista d\'Attesa',
            f'Vuoi aggiungerti alla lista d\'attesa per il libro "{titolo}"?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = self.db.aggiungi_lista_attesa(self.current_user['id'], titolo)
            if success:
                QMessageBox.information(self, 'Lista d\'Attesa', message)
            else:
                QMessageBox.warning(self, 'Errore', message)

    def aggiungi_al_carrello(self, libro, condizione, quantita):
        """Aggiunge un libro al carrello acquisti"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per acquistare libri.')
            return

        # Determina il prezzo basato sulla condizione
        prezzo_unitario = libro.prezzo_nuovo if condizione == 'nuovo' and libro.prezzo_nuovo else \
                         libro.prezzo_usato if condizione == 'usato' and libro.prezzo_usato else libro.prezzo

        # Verifica se il libro è già nel carrello con la stessa condizione
        for item in self.carrello:
            if item['libro'].titolo == libro.titolo and item['condizione'] == condizione:
                item['quantita'] += quantita
                QMessageBox.information(self, 'Carrello Aggiornato',
                                      f"Quantità aggiornata per '{libro.titolo}' ({condizione}).\n"
                                      f"Nuova quantità: {item['quantita']}")
                return

        # Aggiungi nuovo elemento al carrello
        self.carrello.append({
            'libro': libro,
            'condizione': condizione,
            'quantita': quantita,
            'prezzo_unitario': prezzo_unitario
        })

        QMessageBox.information(self, 'Aggiunto al Carrello',
                              f"'{libro.titolo}' ({condizione}) x{quantita} aggiunto al carrello!\n"
                              f"Totale: €{prezzo_unitario * quantita:.2f}")

    def mostra_carrello(self):
        """Mostra il carrello acquisti"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per visualizzare il carrello.')
            return

        if not self.carrello:
            QMessageBox.information(self, 'Carrello Vuoto', 'Il tuo carrello è vuoto.')
            return

        # Crea dialog per il carrello
        cart_dialog = QDialog(self)
        cart_dialog.setWindowTitle('Carrello Acquisti')
        cart_dialog.setModal(True)
        cart_dialog.resize(800, 600)

        layout = QVBoxLayout(cart_dialog)

        # Titolo
        title = QLabel('Il tuo Carrello')
        title.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Lista elementi carrello
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        cart_layout = QVBoxLayout(scroll_widget)
        cart_layout.setSpacing(10)

        totale = 0
        for i, item in enumerate(self.carrello):
            # Card elemento carrello
            item_widget = QWidget()
            item_widget.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e5e5e7;
                    padding: 10px;
                }
            """)

            item_layout = QHBoxLayout(item_widget)

            # Info libro
            info_layout = QVBoxLayout()
            libro = item['libro']
            title_label = QLabel(f"{libro.titolo} ({item['condizione']})")
            title_label.setFont(QFont('SF Pro Text', 16, QFont.Bold))
            info_layout.addWidget(title_label)

            author_label = QLabel(f"di {libro.autore}")
            author_label.setFont(QFont('SF Pro Text', 14))
            author_label.setStyleSheet("color: #86868b;")
            info_layout.addWidget(author_label)

            item_layout.addLayout(info_layout)

            # Quantità e prezzo
            qty_price_layout = QVBoxLayout()
            qty_price_layout.setAlignment(Qt.AlignRight)

            qty_label = QLabel(f"Quantità: {item['quantita']}")
            qty_label.setFont(QFont('SF Pro Text', 14))
            qty_price_layout.addWidget(qty_label)

            price_label = QLabel(f"€{item['prezzo_unitario'] * item['quantita']:.2f}")
            price_label.setFont(QFont('SF Pro Text', 16, QFont.Bold))
            price_label.setStyleSheet("color: #007aff;")
            qty_price_layout.addWidget(price_label)

            item_layout.addLayout(qty_price_layout)

            # Pulsante rimuovi
            remove_btn = QPushButton('🗑️')
            remove_btn.setFixedSize(40, 40)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: #ff3b30;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: #d63027;
                }
            """)
            remove_btn.clicked.connect(lambda checked, idx=i: self.rimuovi_dal_carrello(idx))
            item_layout.addWidget(remove_btn)

            cart_layout.addWidget(item_widget)
            totale += item['prezzo_unitario'] * item['quantita']

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Totale e pulsanti azione
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(15)

        # Totale
        totale_layout = QHBoxLayout()
        totale_layout.addStretch()
        totale_label = QLabel(f'Totale: €{totale:.2f}')
        totale_label.setFont(QFont('SF Pro Display', 20, QFont.Bold))
        totale_label.setStyleSheet("color: #1d1d1f;")
        totale_layout.addWidget(totale_label)
        totale_layout.addStretch()
        footer_layout.addLayout(totale_layout)

        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Svuota carrello
        clear_btn = QPushButton('Svuota Carrello')
        clear_btn.setFont(QFont('SF Pro Text', 14))
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #ff3b30;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #d63027;
            }
        """)
        clear_btn.clicked.connect(self.svuota_carrello)
        buttons_layout.addWidget(clear_btn)

        buttons_layout.addStretch()

        # Continua acquisti
        continue_btn = QPushButton('Continua Acquisti')
        continue_btn.setFont(QFont('SF Pro Text', 14))
        continue_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        continue_btn.clicked.connect(cart_dialog.accept)
        buttons_layout.addWidget(continue_btn)

        # Checkout
        checkout_btn = QPushButton('Procedi al Checkout')
        checkout_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        checkout_btn.setStyleSheet("""
            QPushButton {
                background: #34c759;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: #28a745;
            }
        """)
        checkout_btn.clicked.connect(lambda: self.checkout(cart_dialog))
        buttons_layout.addWidget(checkout_btn)

        footer_layout.addLayout(buttons_layout)
        layout.addLayout(footer_layout)

        cart_dialog.setLayout(layout)
        cart_dialog.exec_()

    def rimuovi_dal_carrello(self, index):
        """Rimuove un elemento dal carrello"""
        if 0 <= index < len(self.carrello):
            item = self.carrello.pop(index)
            QMessageBox.information(self, 'Rimosso dal Carrello',
                                  f"'{item['libro'].titolo}' rimosso dal carrello.")

    def svuota_carrello(self):
        """Svuota completamente il carrello"""
        reply = QMessageBox.question(self, 'Conferma',
                                   'Sei sicuro di voler svuotare il carrello?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.carrello.clear()
            QMessageBox.information(self, 'Carrello Svuotato', 'Il carrello è stato svuotato.')

    def checkout(self, cart_dialog):
        """Avvia il processo di checkout"""
        cart_dialog.accept()  # Chiudi dialog carrello

        # Per ora mostra un messaggio - implementeremo il vero checkout dopo
        QMessageBox.information(self, 'Checkout',
                              'Il sistema di checkout sarà implementato nelle prossime versioni.\n'
                              'Potrai selezionare indirizzi di spedizione, metodi di pagamento e completare l\'acquisto.')

    def create_user_menu(self):
        """Crea il menu utente con avatar e dropdown"""
        self.user_menu_widget = QWidget()
        menu_layout = QHBoxLayout(self.user_menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(15)  # Spaziatura aumentata

        # Avatar migliorato con immagine profilo stilizzata e gradiente
        if self.current_user:
            nome = self.current_user.get('nome', '')
            cognome = self.current_user.get('cognome', '')
            iniziali = f"{nome[0] if nome else ''}{cognome[0] if cognome else ''}".upper()
        else:
            iniziali = "U"

        self.avatar_btn = QPushButton()
        self.avatar_btn.setFixedSize(60, 60)  # Dimensione aumentata ulteriormente

        # Crea un pixmap circolare con gradiente per l'avatar
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.transparent)

        from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QFont, QLinearGradient
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Crea un gradiente radiale per l'avatar
        gradient = QLinearGradient(0, 0, 60, 60)
        gradient.setColorAt(0, QColor('#007aff'))
        gradient.setColorAt(0.5, QColor('#5856d6'))
        gradient.setColorAt(1, QColor('#ff2d55'))

        # Disegna il cerchio di sfondo con gradiente
        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 60, 60)

        # Aggiungi un effetto ombra sottile
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, 58, 58)

        # Disegna le iniziali con font più elegante
        painter.setPen(QPen(QColor('white')))
        font = QFont('SF Pro Display', 18, QFont.Bold)  # Font più grande e bold
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, iniziali)
        painter.end()

        icon = QIcon(pixmap)
        self.avatar_btn.setIcon(icon)
        self.avatar_btn.setIconSize(pixmap.size())

        # Rimuovi il testo del pulsante e stili precedenti
        self.avatar_btn.setText("")
        self.avatar_btn.setStyleSheet("""
            QPushButton {
                border: 3px solid #007aff;
                border-radius: 30px;
                background: transparent;
                box-shadow: 0 4px 8px rgba(0, 122, 255, 0.3);
            }
            QPushButton:hover {
                border-color: #0056cc;
                background: rgba(0, 122, 255, 0.1);
                box-shadow: 0 6px 12px rgba(0, 122, 255, 0.4);
            }
            QPushButton:pressed {
                border-color: #004499;
                background: rgba(0, 122, 255, 0.2);
                box-shadow: 0 2px 4px rgba(0, 122, 255, 0.2);
            }
        """)

        # Menu dropdown migliorato
        self.user_menu = QMenu(self)
        self.user_menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #e5e5e7;
                border-radius: 16px;
                padding: 12px 0;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            }
            QMenu::item {
                padding: 16px 28px;  /* Padding aumentato ulteriormente */
                color: #1d1d1f;
                font-family: 'SF Pro Text';
                font-size: 16px;  /* Font leggermente più grande */
                border-radius: 8px;
                margin: 2px 8px;
            }
            QMenu::item:selected {
                background: #f8f9fa;
                color: #007aff;
            }
            QMenu::separator {
                height: 1px;
                background: #e5e5e7;
                margin: 8px 0;  /* Margine aumentato */
            }
        """)

        # Azioni del menu
        saved_books_action = self.user_menu.addAction('📚 Libri Salvati')
        saved_books_action.triggered.connect(self.mostra_libri_salvati)

        cart_action = self.user_menu.addAction('� Carrello')
        cart_action.triggered.connect(self.mostra_carrello)

        purchased_books_action = self.user_menu.addAction('� Ordini')
        purchased_books_action.triggered.connect(self.mostra_ordini)

        addresses_action = self.user_menu.addAction('🏠 I Miei Indirizzi')
        addresses_action.triggered.connect(self.gestisci_indirizzi)

        payment_methods_action = self.user_menu.addAction('💳 I Miei Metodi di Pagamento')
        payment_methods_action.triggered.connect(self.gestisci_metodi_pagamento)

        self.user_menu.addSeparator()

        notifications_action = self.user_menu.addAction('🔔 Notifiche')
        notifications_action.triggered.connect(self.mostra_notifiche)

        profile_action = self.user_menu.addAction('👤 Profilo')
        profile_action.triggered.connect(self.mostra_profilo)

        self.user_menu.addSeparator()

        logout_action = self.user_menu.addAction('🚪 Logout')
        logout_action.triggered.connect(self.perform_logout)

        self.avatar_btn.setMenu(self.user_menu)
        menu_layout.addWidget(self.avatar_btn)

    def mostra_libri_salvati(self):
        """Mostra i libri salvati nei preferiti"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per vedere i libri salvati.')
            return

        libri = self.db.mostra_favoriti(self.current_user['id'])
        if libri:
            content = "I tuoi libri salvati:\n\n" + "\n".join([f"• {libro.titolo} - {libro.autore}" for libro in libri])
        else:
            content = "Non hai ancora salvato libri nei preferiti."

        dialog = ResultDialog("Libri Salvati", content, self)
        dialog.exec_()

    def mostra_libri_prenotati(self):
        """Mostra i libri prenotati"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per vedere le prenotazioni.')
            return

        prenotazioni = self.db.mostra_prenotazioni_utente(self.current_user['id'])
        if prenotazioni:
            content = "Le tue prenotazioni attive:\n\n"
            for p in prenotazioni:
                content += f"• {p['titolo']} - {p['autore']}\n"
                content += f"  Prenotato il: {p['data_prenotazione']} - Scadenza: {p['data_scadenza']}\n\n"
        else:
            content = "Non hai prenotazioni attive."

        dialog = ResultDialog("Libri Prenotati", content, self)
        dialog.exec_()

    def mostra_carrello(self):
        """Mostra il carrello acquisti"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per visualizzare il carrello.')
            return

        if not self.carrello:
            QMessageBox.information(self, 'Carrello Vuoto', 'Il tuo carrello è vuoto.')
            return

        # Crea dialog per il carrello
        cart_dialog = QDialog(self)
        cart_dialog.setWindowTitle('Carrello Acquisti')
        cart_dialog.setModal(True)
        cart_dialog.resize(800, 600)

        layout = QVBoxLayout(cart_dialog)

        # Titolo
        title = QLabel('Il tuo Carrello')
        title.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Lista elementi carrello
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        cart_layout = QVBoxLayout(scroll_widget)
        cart_layout.setSpacing(10)

        totale = 0
        for i, item in enumerate(self.carrello):
            # Card elemento carrello
            item_widget = QWidget()
            item_widget.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e5e5e7;
                    padding: 10px;
                }
            """)

            item_layout = QHBoxLayout(item_widget)

            # Info libro
            info_layout = QVBoxLayout()
            libro = item['libro']
            title_label = QLabel(f"{libro.titolo} ({item['condizione']})")
            title_label.setFont(QFont('SF Pro Text', 16, QFont.Bold))
            info_layout.addWidget(title_label)

            author_label = QLabel(f"di {libro.autore}")
            author_label.setFont(QFont('SF Pro Text', 14))
            author_label.setStyleSheet("color: #86868b;")
            info_layout.addWidget(author_label)

            item_layout.addLayout(info_layout)

            # Quantità e prezzo
            qty_price_layout = QVBoxLayout()
            qty_price_layout.setAlignment(Qt.AlignRight)

            qty_label = QLabel(f"Quantità: {item['quantita']}")
            qty_label.setFont(QFont('SF Pro Text', 14))
            qty_price_layout.addWidget(qty_label)

            price_label = QLabel(f"€{item['prezzo_unitario'] * item['quantita']:.2f}")
            price_label.setFont(QFont('SF Pro Text', 16, QFont.Bold))
            price_label.setStyleSheet("color: #007aff;")
            qty_price_layout.addWidget(price_label)

            item_layout.addLayout(qty_price_layout)

            # Pulsante rimuovi
            remove_btn = QPushButton('🗑️')
            remove_btn.setFixedSize(40, 40)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: #ff3b30;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: #d63027;
                }
            """)
            remove_btn.clicked.connect(lambda checked, idx=i: self.rimuovi_dal_carrello(idx))
            item_layout.addWidget(remove_btn)

            cart_layout.addWidget(item_widget)
            totale += item['prezzo_unitario'] * item['quantita']

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Totale e pulsanti azione
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(15)

        # Totale
        totale_layout = QHBoxLayout()
        totale_layout.addStretch()
        totale_label = QLabel(f'Totale: €{totale:.2f}')
        totale_label.setFont(QFont('SF Pro Display', 20, QFont.Bold))
        totale_label.setStyleSheet("color: #1d1d1f;")
        totale_layout.addWidget(totale_label)
        totale_layout.addStretch()
        footer_layout.addLayout(totale_layout)

        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Svuota carrello
        clear_btn = QPushButton('Svuota Carrello')
        clear_btn.setFont(QFont('SF Pro Text', 14))
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #ff3b30;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #d63027;
            }
        """)
        clear_btn.clicked.connect(self.svuota_carrello)
        buttons_layout.addWidget(clear_btn)

        buttons_layout.addStretch()

        # Continua acquisti
        continue_btn = QPushButton('Continua Acquisti')
        continue_btn.setFont(QFont('SF Pro Text', 14))
        continue_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        continue_btn.clicked.connect(cart_dialog.accept)
        buttons_layout.addWidget(continue_btn)

        # Checkout
        checkout_btn = QPushButton('Procedi al Checkout')
        checkout_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        checkout_btn.setStyleSheet("""
            QPushButton {
                background: #34c759;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: #28a745;
            }
        """)
        checkout_btn.clicked.connect(lambda: self.checkout(cart_dialog))
        buttons_layout.addWidget(checkout_btn)

        footer_layout.addLayout(buttons_layout)
        layout.addLayout(footer_layout)

        cart_dialog.setLayout(layout)
        cart_dialog.exec_()

    def gestisci_indirizzi(self):
        """Gestisce gli indirizzi di spedizione dell'utente"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per gestire gli indirizzi.')
            return

        # Crea dialog per la gestione indirizzi
        address_dialog = QDialog(self)
        address_dialog.setWindowTitle('I Miei Indirizzi')
        address_dialog.setModal(True)
        address_dialog.resize(900, 700)

        layout = QVBoxLayout(address_dialog)

        # Titolo
        title = QLabel('Gestisci i tuoi Indirizzi')
        title.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Lista indirizzi
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        address_layout = QVBoxLayout(scroll_widget)
        address_layout.setSpacing(15)

        # Carica indirizzi esistenti
        indirizzi = self.db.get_indirizzi_utente(self.current_user['id'])

        if indirizzi:
            for indirizzo in indirizzi:
                # Card indirizzo
                addr_widget = QWidget()
                addr_widget.setStyleSheet("""
                    QWidget {
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e5e5e7;
                        padding: 15px;
                    }
                """)

                addr_main_layout = QVBoxLayout(addr_widget)

                # Header con nome e azioni
                header_layout = QHBoxLayout()

                name_label = QLabel(f"{indirizzo['nome']} {indirizzo['cognome']}")
                name_label.setFont(QFont('SF Pro Text', 16, QFont.Bold))
                header_layout.addWidget(name_label)

                if indirizzo['is_default']:
                    default_label = QLabel('🏠 Predefinito')
                    default_label.setFont(QFont('SF Pro Text', 12))
                    default_label.setStyleSheet("color: #34c759; background: #e8f5e8; padding: 4px 8px; border-radius: 4px;")
                    header_layout.addWidget(default_label)

                header_layout.addStretch()

                # Pulsanti azione
                actions_layout = QHBoxLayout()
                actions_layout.setSpacing(8)

                edit_btn = QPushButton('✏️')
                edit_btn.setFixedSize(35, 35)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background: #007aff;
                        color: white;
                        border: none;
                        border-radius: 17px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background: #0056cc;
                    }
                """)
                edit_btn.setToolTip('Modifica indirizzo')
                actions_layout.addWidget(edit_btn)

                if not indirizzo['is_default']:
                    default_btn = QPushButton('🏠')
                    default_btn.setFixedSize(35, 35)
                    default_btn.setStyleSheet("""
                        QPushButton {
                            background: #34c759;
                            color: white;
                            border: none;
                            border-radius: 17px;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background: #28a745;
                        }
                    """)
                    default_btn.setToolTip('Imposta come predefinito')
                    actions_layout.addWidget(default_btn)

                delete_btn = QPushButton('🗑️')
                delete_btn.setFixedSize(35, 35)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background: #ff3b30;
                        color: white;
                        border: none;
                        border-radius: 17px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background: #d63027;
                    }
                """)
                delete_btn.setToolTip('Elimina indirizzo')
                actions_layout.addWidget(delete_btn)

                header_layout.addLayout(actions_layout)
                addr_main_layout.addLayout(header_layout)

                # Dettagli indirizzo
                address_text = f"{indirizzo['indirizzo']}\n{indirizzo['citta']} {indirizzo['cap']}, {indirizzo['provincia']}"
                if indirizzo['telefono']:
                    address_text += f"\nTel: {indirizzo['telefono']}"

                addr_details = QLabel(address_text)
                addr_details.setFont(QFont('SF Pro Text', 14))
                addr_details.setStyleSheet("color: #1d1d1f; margin-top: 8px;")
                addr_main_layout.addWidget(addr_details)

                address_layout.addWidget(addr_widget)
        else:
            # Nessun indirizzo
            no_addr_label = QLabel("Non hai ancora salvato indirizzi di spedizione.")
            no_addr_label.setFont(QFont('SF Pro Text', 16))
            no_addr_label.setStyleSheet("color: #86868b; text-align: center;")
            no_addr_label.setAlignment(Qt.AlignCenter)
            address_layout.addWidget(no_addr_label)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Pulsanti footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(15)

        # Aggiungi nuovo indirizzo
        add_btn = QPushButton('➕ Aggiungi Nuovo Indirizzo')
        add_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        add_btn.setMinimumHeight(45)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007aff, stop:1 #0056cc);
                color: white;
                border: none;
                border-radius: 22px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056cc, stop:1 #004499);
            }
        """)
        add_btn.clicked.connect(lambda: self.aggiungi_indirizzo(address_dialog))
        footer_layout.addWidget(add_btn)

        footer_layout.addStretch()

        # Chiudi
        close_btn = QPushButton('Chiudi')
        close_btn.setFont(QFont('SF Pro Text', 14))
        close_btn.setMinimumHeight(45)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        close_btn.clicked.connect(address_dialog.accept)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

        address_dialog.setLayout(layout)
        address_dialog.exec_()

    def aggiungi_indirizzo(self, parent_dialog):
        """Aggiunge un nuovo indirizzo"""
        # Crea dialog per nuovo indirizzo
        add_dialog = QDialog(parent_dialog)
        add_dialog.setWindowTitle('Aggiungi Nuovo Indirizzo')
        add_dialog.setModal(True)
        add_dialog.resize(500, 600)

        layout = QVBoxLayout(add_dialog)

        # Titolo
        title = QLabel('Nuovo Indirizzo di Spedizione')
        title.setFont(QFont('SF Pro Display', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Nome
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText('Nome')
        nome_edit.setFont(QFont('SF Pro Text', 14))
        nome_edit.setMinimumHeight(40)
        nome_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Nome:', nome_edit)

        # Cognome
        cognome_edit = QLineEdit()
        cognome_edit.setPlaceholderText('Cognome')
        cognome_edit.setFont(QFont('SF Pro Text', 14))
        cognome_edit.setMinimumHeight(40)
        cognome_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Cognome:', cognome_edit)

        # Indirizzo
        indirizzo_edit = QLineEdit()
        indirizzo_edit.setPlaceholderText('Via/Piazza e numero civico')
        indirizzo_edit.setFont(QFont('SF Pro Text', 14))
        indirizzo_edit.setMinimumHeight(40)
        indirizzo_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Indirizzo:', indirizzo_edit)

        # Città
        citta_edit = QLineEdit()
        citta_edit.setPlaceholderText('Città')
        citta_edit.setFont(QFont('SF Pro Text', 14))
        citta_edit.setMinimumHeight(40)
        citta_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Città:', citta_edit)

        # CAP
        cap_edit = QLineEdit()
        cap_edit.setPlaceholderText('CAP')
        cap_edit.setFont(QFont('SF Pro Text', 14))
        cap_edit.setMinimumHeight(40)
        cap_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('CAP:', cap_edit)

        # Provincia
        provincia_edit = QLineEdit()
        provincia_edit.setPlaceholderText('Provincia')
        provincia_edit.setFont(QFont('SF Pro Text', 14))
        provincia_edit.setMinimumHeight(40)
        provincia_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Provincia:', provincia_edit)

        # Telefono
        telefono_edit = QLineEdit()
        telefono_edit.setPlaceholderText('Telefono (opzionale)')
        telefono_edit.setFont(QFont('SF Pro Text', 14))
        telefono_edit.setMinimumHeight(40)
        telefono_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Telefono:', telefono_edit)

        # Checkbox indirizzo predefinito
        default_check = QCheckBox('Imposta come indirizzo predefinito')
        default_check.setFont(QFont('SF Pro Text', 14))
        default_check.setStyleSheet("color: #1d1d1f;")
        form_layout.addRow('', default_check)

        layout.addLayout(form_layout)

        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        cancel_btn = QPushButton('Annulla')
        cancel_btn.setFont(QFont('SF Pro Text', 14))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        cancel_btn.clicked.connect(add_dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton('Salva Indirizzo')
        save_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet(get_primary_button_stylesheet())
        save_btn.clicked.connect(lambda: self.salva_nuovo_indirizzo(
            nome_edit.text(), cognome_edit.text(), indirizzo_edit.text(),
            citta_edit.text(), cap_edit.text(), provincia_edit.text(),
            telefono_edit.text(), default_check.isChecked(), add_dialog, parent_dialog
        ))
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        add_dialog.setLayout(layout)
        add_dialog.exec_()

    def salva_nuovo_indirizzo(self, nome, cognome, indirizzo, citta, cap, provincia, telefono, is_default, add_dialog, parent_dialog):
        """Salva un nuovo indirizzo"""
        if not all([nome, cognome, indirizzo, citta, cap, provincia]):
            QMessageBox.warning(add_dialog, 'Campi obbligatori', 'Tutti i campi sono obbligatori tranne il telefono.')
            return

        success, message = self.db.salva_indirizzo(
            self.current_user['id'], nome, cognome, indirizzo, citta, cap, provincia, telefono, is_default
        )

        if success:
            QMessageBox.information(add_dialog, 'Successo', 'Indirizzo salvato con successo!')
            add_dialog.accept()
            # Ricarica la lista indirizzi
            parent_dialog.close()
            self.gestisci_indirizzi()
        else:
            QMessageBox.warning(add_dialog, 'Errore', message)

    def gestisci_metodi_pagamento(self):
        """Gestisce i metodi di pagamento dell'utente"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per gestire i metodi di pagamento.')
            return

        # Crea dialog principale
        payment_dialog = QDialog(self)
        payment_dialog.setWindowTitle('I Miei Metodi di Pagamento')
        payment_dialog.setModal(True)
        payment_dialog.resize(800, 600)

        layout = QVBoxLayout(payment_dialog)

        # Titolo
        title = QLabel('💳 I Miei Metodi di Pagamento')
        title.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Scroll area per metodi pagamento
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        payment_layout = QVBoxLayout(scroll_widget)
        payment_layout.setSpacing(15)

        # Carica metodi pagamento
        metodi = self.db.get_metodi_pagamento_utente(self.current_user['id'])

        if metodi:
            for metodo in metodi:
                # Card widget
                card_widget = QWidget()
                card_widget.setStyleSheet("""
                    QWidget {
                        background: white;
                        border: 1px solid #e5e5e7;
                        border-radius: 12px;
                        padding: 15px;
                    }
                """)

                card_layout = QVBoxLayout(card_widget)

                # Header con tipo e azioni
                header_layout = QHBoxLayout()

                # Tipo carta e numero
                tipo_info = QLabel(f"{metodo['tipo']} ****{metodo['numero_carta'][-4:]}")
                tipo_info.setFont(QFont('SF Pro Text', 16, QFont.Bold))
                header_layout.addWidget(tipo_info)

                # Badge predefinito
                if metodo['is_default']:
                    default_badge = QLabel('Predefinito')
                    default_badge.setFont(QFont('SF Pro Text', 12, QFont.Bold))
                    default_badge.setStyleSheet("""
                        QLabel {
                            background: #34c759;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 8px;
                        }
                    """)
                    header_layout.addWidget(default_badge)

                header_layout.addStretch()

                # Azioni
                actions_layout = QHBoxLayout()
                actions_layout.setSpacing(10)

                # Imposta come predefinito
                if not metodo['is_default']:
                    default_btn = QPushButton('⭐')
                    default_btn.setToolTip('Imposta come predefinito')
                    default_btn.setFixedSize(30, 30)
                    default_btn.setStyleSheet("""
                        QPushButton {
                            background: #007aff;
                            color: white;
                            border: none;
                            border-radius: 15px;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background: #0056cc;
                        }
                    """)
                    default_btn.clicked.connect(lambda checked, mid=metodo['id']: self.imposta_metodo_predefinito(mid, payment_dialog))
                    actions_layout.addWidget(default_btn)

                # Elimina
                delete_btn = QPushButton('🗑️')
                delete_btn.setToolTip('Elimina metodo')
                delete_btn.setFixedSize(30, 30)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background: #ff3b30;
                        color: white;
                        border: none;
                        border-radius: 15px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background: #d63027;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, mid=metodo['id']: self.elimina_metodo_pagamento(mid, payment_dialog))
                actions_layout.addWidget(delete_btn)

                header_layout.addLayout(actions_layout)
                card_layout.addLayout(header_layout)

                # Dettagli metodo
                details_layout = QVBoxLayout()
                details_layout.setSpacing(5)

                titolare_label = QLabel(f"Titolare: {metodo['titolare']}")
                titolare_label.setFont(QFont('SF Pro Text', 14))
                details_layout.addWidget(titolare_label)

                scadenza_label = QLabel(f"Scadenza: {metodo['scadenza']}")
                scadenza_label.setFont(QFont('SF Pro Text', 14))
                details_layout.addWidget(scadenza_label)

                card_layout.addLayout(details_layout)
                payment_layout.addWidget(card_widget)
        else:
            # Nessun metodo
            no_payment_label = QLabel("Non hai ancora salvato metodi di pagamento.")
            no_payment_label.setFont(QFont('SF Pro Text', 16))
            no_payment_label.setStyleSheet("color: #86868b; text-align: center;")
            no_payment_label.setAlignment(Qt.AlignCenter)
            payment_layout.addWidget(no_payment_label)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Pulsanti footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(15)

        # Aggiungi nuovo metodo
        add_btn = QPushButton('➕ Aggiungi Nuovo Metodo')
        add_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        add_btn.setMinimumHeight(45)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007aff, stop:1 #0056cc);
                color: white;
                border: none;
                border-radius: 22px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056cc, stop:1 #004499);
            }
        """)
        add_btn.clicked.connect(lambda: self.aggiungi_metodo_pagamento(payment_dialog))
        footer_layout.addWidget(add_btn)

        footer_layout.addStretch()

        # Chiudi
        close_btn = QPushButton('Chiudi')
        close_btn.setFont(QFont('SF Pro Text', 14))
        close_btn.setMinimumHeight(45)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        close_btn.clicked.connect(payment_dialog.accept)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

        payment_dialog.setLayout(layout)
        payment_dialog.exec_()

    def aggiungi_metodo_pagamento(self, parent_dialog):
        """Aggiunge un nuovo metodo di pagamento"""
        # Crea dialog per nuovo metodo
        add_dialog = QDialog(parent_dialog)
        add_dialog.setWindowTitle('Aggiungi Nuovo Metodo di Pagamento')
        add_dialog.setModal(True)
        add_dialog.resize(500, 500)

        layout = QVBoxLayout(add_dialog)

        # Titolo
        title = QLabel('Nuovo Metodo di Pagamento')
        title.setFont(QFont('SF Pro Display', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Tipo carta
        tipo_combo = QComboBox()
        tipo_combo.addItems(['Carta di Credito', 'Carta di Debito', 'PayPal', 'Bonifico'])
        tipo_combo.setFont(QFont('SF Pro Text', 14))
        tipo_combo.setMinimumHeight(40)
        tipo_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
            }
        """)
        form_layout.addRow('Tipo:', tipo_combo)

        # Numero carta
        numero_edit = QLineEdit()
        numero_edit.setPlaceholderText('1234 5678 9012 3456')
        numero_edit.setFont(QFont('SF Pro Text', 14))
        numero_edit.setMinimumHeight(40)
        numero_edit.setStyleSheet(get_input_stylesheet())
        numero_edit.setMaxLength(19)  # Per formato XXXX XXXX XXXX XXXX
        numero_edit.textChanged.connect(lambda: self.format_numero_carta(numero_edit))
        form_layout.addRow('Numero Carta:', numero_edit)

        # Titolare
        titolare_edit = QLineEdit()
        titolare_edit.setPlaceholderText('Nome e Cognome del Titolare')
        titolare_edit.setFont(QFont('SF Pro Text', 14))
        titolare_edit.setMinimumHeight(40)
        titolare_edit.setStyleSheet(get_input_stylesheet())
        form_layout.addRow('Titolare:', titolare_edit)

        # Scadenza
        scadenza_edit = QLineEdit()
        scadenza_edit.setPlaceholderText('MM/AA')
        scadenza_edit.setFont(QFont('SF Pro Text', 14))
        scadenza_edit.setMinimumHeight(40)
        scadenza_edit.setStyleSheet(get_input_stylesheet())
        scadenza_edit.setMaxLength(5)
        scadenza_edit.textChanged.connect(lambda: self.format_scadenza(scadenza_edit))
        form_layout.addRow('Scadenza:', scadenza_edit)

        # CVV
        cvv_edit = QLineEdit()
        cvv_edit.setPlaceholderText('123')
        cvv_edit.setFont(QFont('SF Pro Text', 14))
        cvv_edit.setMinimumHeight(40)
        cvv_edit.setStyleSheet(get_input_stylesheet())
        cvv_edit.setMaxLength(4)
        cvv_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow('CVV:', cvv_edit)

        # Checkbox metodo predefinito
        default_check = QCheckBox('Imposta come metodo predefinito')
        default_check.setFont(QFont('SF Pro Text', 14))
        default_check.setStyleSheet("color: #1d1d1f;")
        form_layout.addRow('', default_check)

        layout.addLayout(form_layout)

        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        cancel_btn = QPushButton('Annulla')
        cancel_btn.setFont(QFont('SF Pro Text', 14))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        cancel_btn.clicked.connect(add_dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton('Salva Metodo')
        save_btn.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet(get_primary_button_stylesheet())
        save_btn.clicked.connect(lambda: self.salva_nuovo_metodo_pagamento(
            tipo_combo.currentText(), numero_edit.text(), titolare_edit.text(),
            scadenza_edit.text(), cvv_edit.text(), default_check.isChecked(),
            add_dialog, parent_dialog
        ))
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        add_dialog.setLayout(layout)
        add_dialog.exec_()

    def format_numero_carta(self, edit):
        """Formatta il numero della carta con spazi"""
        text = edit.text().replace(' ', '')
        formatted = ' '.join([text[i:i+4] for i in range(0, len(text), 4)])
        edit.setText(formatted[:19])  # Limita a 19 caratteri

    def format_scadenza(self, edit):
        """Formatta la data di scadenza MM/AA"""
        text = edit.text().replace('/', '')
        if len(text) >= 2:
            formatted = text[:2] + '/' + text[2:4]
            edit.setText(formatted[:5])
        else:
            edit.setText(text)

    def salva_nuovo_metodo_pagamento(self, tipo, numero_carta, titolare, scadenza, cvv, is_default, add_dialog, parent_dialog):
        """Salva un nuovo metodo di pagamento"""
        if not all([tipo, numero_carta, titolare, scadenza]):
            QMessageBox.warning(add_dialog, 'Campi obbligatori', 'Tutti i campi sono obbligatori.')
            return

        # Validazione numero carta (semplice)
        numero_clean = numero_carta.replace(' ', '')
        if len(numero_clean) < 13 or not numero_clean.isdigit():
            QMessageBox.warning(add_dialog, 'Numero carta non valido', 'Inserisci un numero di carta valido.')
            return

        # Validazione scadenza
        if len(scadenza) != 5 or scadenza[2] != '/':
            QMessageBox.warning(add_dialog, 'Scadenza non valida', 'Il formato della scadenza deve essere MM/AA.')
            return

        success, message = self.db.salva_metodo_pagamento(
            self.current_user['id'], tipo, numero_clean, titolare, scadenza, is_default
        )

        if success:
            QMessageBox.information(add_dialog, 'Successo', 'Metodo di pagamento salvato con successo!')
            add_dialog.accept()
            # Ricarica la lista metodi
            parent_dialog.close()
            self.gestisci_metodi_pagamento()
        else:
            QMessageBox.warning(add_dialog, 'Errore', message)

    def imposta_metodo_predefinito(self, metodo_id, parent_dialog):
        """Imposta un metodo di pagamento come predefinito"""
        success, message = self.db.imposta_metodo_predefinito(self.current_user['id'], metodo_id)
        if success:
            QMessageBox.information(parent_dialog, 'Successo', 'Metodo impostato come predefinito!')
            parent_dialog.close()
            self.gestisci_metodi_pagamento()
        else:
            QMessageBox.warning(parent_dialog, 'Errore', message)

    def elimina_metodo_pagamento(self, metodo_id, parent_dialog):
        """Elimina un metodo di pagamento"""
        reply = QMessageBox.question(parent_dialog, 'Conferma Eliminazione',
                                   'Sei sicuro di voler eliminare questo metodo di pagamento?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, message = self.db.elimina_metodo_pagamento(metodo_id)
            if success:
                QMessageBox.information(parent_dialog, 'Successo', 'Metodo di pagamento eliminato!')
                parent_dialog.close()
                self.gestisci_metodi_pagamento()
            else:
                QMessageBox.warning(parent_dialog, 'Errore', message)

    def checkout(self, cart_dialog):
        """Procedura di checkout"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per procedere al checkout.')
            return

        if not self.carrello:
            QMessageBox.warning(self, 'Carrello vuoto', 'Il tuo carrello è vuoto.')
            return

        # Verifica indirizzi disponibili
        indirizzi = self.db.get_indirizzi_utente(self.current_user['id'])
        if not indirizzi:
            reply = QMessageBox.question(self, 'Nessun indirizzo',
                                       'Non hai indirizzi di spedizione salvati. Vuoi aggiungerne uno ora?',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                cart_dialog.accept()
                self.gestisci_indirizzi()
            return

        # Crea dialog checkout
        checkout_dialog = QDialog(self)
        checkout_dialog.setWindowTitle('Checkout')
        checkout_dialog.setModal(True)
        checkout_dialog.resize(1000, 800)

        layout = QVBoxLayout(checkout_dialog)

        # Titolo
        title = QLabel('Completa il tuo Acquisto')
        title.setFont(QFont('SF Pro Display', 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Scroll area per contenuto
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        content_layout = QVBoxLayout(scroll_widget)
        content_layout.setSpacing(20)

        # Sezione riepilogo ordine
        summary_group = QGroupBox('Riepilogo Ordine')
        summary_group.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e5e7;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)

        summary_layout = QVBoxLayout(summary_group)

        # Lista libri
        books_layout = QVBoxLayout()
        books_layout.setSpacing(10)

        totale = 0
        for item in self.carrello:
            libro = item['libro']
            book_widget = QWidget()
            book_widget.setStyleSheet("""
                QWidget {
                    background: #f5f5f7;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)

            book_layout = QHBoxLayout(book_widget)

            info_layout = QVBoxLayout()
            title_label = QLabel(f"{libro.titolo} ({item['condizione']})")
            title_label.setFont(QFont('SF Pro Text', 14, QFont.Bold))
            info_layout.addWidget(title_label)

            author_label = QLabel(f"di {libro.autore}")
            author_label.setFont(QFont('SF Pro Text', 12))
            author_label.setStyleSheet("color: #86868b;")
            info_layout.addWidget(author_label)

            book_layout.addLayout(info_layout)

            qty_price_layout = QVBoxLayout()
            qty_price_layout.setAlignment(Qt.AlignRight)

            qty_label = QLabel(f"Qty: {item['quantita']}")
            qty_label.setFont(QFont('SF Pro Text', 12))
            qty_price_layout.addWidget(qty_label)

            price_label = QLabel(f"€{item['prezzo_unitario'] * item['quantita']:.2f}")
            price_label.setFont(QFont('SF Pro Text', 14, QFont.Bold))
            price_label.setStyleSheet("color: #007aff;")
            qty_price_layout.addWidget(price_label)

            book_layout.addLayout(qty_price_layout)

            books_layout.addWidget(book_widget)
            totale += item['prezzo_unitario'] * item['quantita']

        summary_layout.addLayout(books_layout)

        # Totale
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel(f'Totale Ordine: €{totale:.2f}')
        total_label.setFont(QFont('SF Pro Display', 18, QFont.Bold))
        total_label.setStyleSheet("color: #1d1d1f;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        summary_layout.addLayout(total_layout)

        content_layout.addWidget(summary_group)

        # Sezione indirizzo spedizione
        address_group = QGroupBox('Indirizzo di Spedizione')
        address_group.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        address_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e5e7;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)

        address_layout = QVBoxLayout(address_group)

        # Combo box indirizzi
        self.address_combo = QComboBox()
        self.address_combo.setFont(QFont('SF Pro Text', 14))
        self.address_combo.setMinimumHeight(40)
        self.address_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)

        # Popola combo box
        for indirizzo in indirizzi:
            display_text = f"{indirizzo['nome']} {indirizzo['cognome']} - {indirizzo['indirizzo']}, {indirizzo['citta']}"
            self.address_combo.addItem(display_text, indirizzo['id'])

        address_layout.addWidget(QLabel('Seleziona indirizzo di spedizione:'))
        address_layout.addWidget(self.address_combo)

        # Pulsante aggiungi nuovo indirizzo
        add_address_btn = QPushButton('➕ Aggiungi Nuovo Indirizzo')
        add_address_btn.setFont(QFont('SF Pro Text', 14))
        add_address_btn.setStyleSheet("""
            QPushButton {
                background: #007aff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #0056cc;
            }
        """)
        add_address_btn.clicked.connect(lambda: self.aggiungi_indirizzo_checkout(checkout_dialog))
        address_layout.addWidget(add_address_btn)

        content_layout.addWidget(address_group)

        # Sezione metodo pagamento
        payment_group = QGroupBox('Metodo di Pagamento')
        payment_group.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        payment_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e5e7;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)

        payment_layout = QVBoxLayout(payment_group)

        # Radio buttons per tipo pagamento
        self.payment_type_group = QButtonGroup()

        # Carta di credito/debito
        card_radio = QRadioButton('💳 Carta di Credito/Debito')
        card_radio.setFont(QFont('SF Pro Text', 14))
        card_radio.setChecked(True)
        self.payment_type_group.addButton(card_radio, 1)
        payment_layout.addWidget(card_radio)

        # PayPal
        paypal_radio = QRadioButton('🅿️ PayPal')
        paypal_radio.setFont(QFont('SF Pro Text', 14))
        self.payment_type_group.addButton(paypal_radio, 2)
        payment_layout.addWidget(paypal_radio)

        # Bonifico
        bank_radio = QRadioButton('🏦 Bonifico Bancario')
        bank_radio.setFont(QFont('SF Pro Text', 14))
        self.payment_type_group.addButton(bank_radio, 3)
        payment_layout.addWidget(bank_radio)

        # Contrassegno
        cod_radio = QRadioButton('💵 Contrassegno')
        cod_radio.setFont(QFont('SF Pro Text', 14))
        self.payment_type_group.addButton(cod_radio, 4)
        payment_layout.addWidget(cod_radio)

        content_layout.addWidget(payment_group)

        # Sezione opzioni consegna
        delivery_group = QGroupBox('Opzioni di Consegna')
        delivery_group.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        delivery_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e5e7;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)

        delivery_layout = QVBoxLayout(delivery_group)

        # Radio buttons consegna
        self.delivery_type_group = QButtonGroup()

        # Consegna a domicilio
        home_delivery_radio = QRadioButton('🚚 Consegna a Domicilio (2-5 giorni lavorativi)')
        home_delivery_radio.setFont(QFont('SF Pro Text', 14))
        home_delivery_radio.setChecked(True)
        self.delivery_type_group.addButton(home_delivery_radio, 1)
        delivery_layout.addWidget(home_delivery_radio)

        # Ritiro in libreria
        pickup_radio = QRadioButton('🏪 Ritiro in Libreria (Disponibile entro 24h)')
        pickup_radio.setFont(QFont('SF Pro Text', 14))
        self.delivery_type_group.addButton(pickup_radio, 2)
        delivery_layout.addWidget(pickup_radio)

        content_layout.addWidget(delivery_group)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Pulsanti footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(15)

        # Torna al carrello
        back_btn = QPushButton('← Torna al Carrello')
        back_btn.setFont(QFont('SF Pro Text', 14))
        back_btn.setMinimumHeight(45)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #86868b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background: #6c6c70;
            }
        """)
        back_btn.clicked.connect(checkout_dialog.reject)
        footer_layout.addWidget(back_btn)

        footer_layout.addStretch()

        # Conferma ordine
        confirm_btn = QPushButton('✅ Conferma Ordine')
        confirm_btn.setFont(QFont('SF Pro Text', 18, QFont.Bold))
        confirm_btn.setMinimumHeight(50)
        confirm_btn.setStyleSheet(get_primary_button_stylesheet())
        confirm_btn.clicked.connect(lambda: self.conferma_ordine(checkout_dialog, cart_dialog))
        footer_layout.addWidget(confirm_btn)

        layout.addLayout(footer_layout)

        checkout_dialog.setLayout(layout)
        checkout_dialog.exec_()

    def aggiungi_indirizzo_checkout(self, checkout_dialog):
        """Aggiunge indirizzo durante checkout"""
        self.aggiungi_indirizzo(checkout_dialog)
        # Ricarica indirizzi nel combo box
        indirizzi = self.db.get_indirizzi_utente(self.current_user['id'])
        self.address_combo.clear()
        for indirizzo in indirizzi:
            display_text = f"{indirizzo['nome']} {indirizzo['cognome']} - {indirizzo['indirizzo']}, {indirizzo['citta']}"
            self.address_combo.addItem(display_text, indirizzo['id'])

    def conferma_ordine(self, checkout_dialog, cart_dialog):
        """Conferma e processa l'ordine"""
        # Ottieni indirizzo selezionato
        address_id = self.address_combo.currentData()
        if not address_id:
            QMessageBox.warning(checkout_dialog, 'Indirizzo richiesto', 'Seleziona un indirizzo di spedizione.')
            return

        # Ottieni tipo pagamento
        payment_type = self.payment_type_group.checkedId()

        # Ottieni tipo consegna
        delivery_type = self.delivery_type_group.checkedId()

        # Calcola data consegna stimata
        from datetime import datetime, timedelta
        if delivery_type == 1:  # Consegna a domicilio
            delivery_date = datetime.now() + timedelta(days=5)
        else:  # Ritiro in libreria
            delivery_date = datetime.now() + timedelta(days=1)

        # Salva ordine nel database
        success, order_id = self.db.crea_ordine(
            self.current_user['id'], self.carrello, address_id,
            payment_type, delivery_type, delivery_date
        )

        if success:
            QMessageBox.information(checkout_dialog, 'Ordine Confermato',
                                  f'Il tuo ordine #{order_id} è stato confermato!\n'
                                  f'Data consegna stimata: {delivery_date.strftime("%d/%m/%Y")}\n\n'
                                  'Riceverai una email di conferma con i dettagli.')

            # Svuota carrello
            self.carrello.clear()

            # Chiudi dialog
            checkout_dialog.accept()
            cart_dialog.accept()

            # Aggiorna interfaccia
            self.aggiorna_interfaccia_utente()
        else:
            QMessageBox.warning(checkout_dialog, 'Errore', 'Si è verificato un errore durante la creazione dell\'ordine.')

    def mostra_notifiche(self):
        """Mostra le notifiche dell'utente"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per vedere le notifiche.')
            return

        notifiche = self.db.mostra_notifiche(self.current_user['id'])
        if notifiche:
            content = "Le tue notifiche:\n\n"
            for n in notifiche:
                content += f"• [{n['tipo']}] {n['messaggio']}\n"
                content += f"  {n['data']}\n\n"

            # Segna come lette
            self.db.segna_notifiche_lette(self.current_user['id'])
        else:
            content = "Non hai nuove notifiche."

        dialog = ResultDialog("Notifiche", content, self)
        dialog.exec_()

    def mostra_profilo(self):
        """Mostra il profilo utente"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per vedere il profilo.')
            return

        user = self.current_user
        content = f"""Informazioni del profilo:

Nome: {user.get('nome', 'N/A')} {user.get('cognome', 'N/A')}
Email: {user.get('email', 'N/A')}
Nome utente: {user.get('nome_utente', 'N/A')}
Ruolo: {user.get('ruolo', 'N/A')}
Struttura: {user.get('biblioteca') or user.get('libreria') or 'Nessuna'}"""

        dialog = ResultDialog("Profilo Utente", content, self)
        dialog.exec_()

    def mostra_ordini(self):
        """Mostra gli ordini dell'utente"""
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso richiesto', 'Devi effettuare il login per vedere i tuoi ordini.')
            return

        ordini = self.db.get_acquisti_utente(self.current_user['id'])
        if ordini:
            content = "I tuoi ordini:\n\n"
            for ordine in ordini:
                content += f"Ordine #{ordine['id']} - {ordine['data_acquisto']}\n"
                content += f"Totale: €{ordine['totale']:.2f}\n"
                content += f"Stato: {ordine['stato']}\n"
                content += f"Consegna: {ordine['tipo_consegna']}\n"
                content += f"Libreria: {ordine['libreria']}\n"
                if ordine['data_consegna_prevista']:
                    content += f"Consegna prevista: {ordine['data_consegna_prevista']}\n"
                if ordine['tracking']:
                    content += f"Tracking: {ordine['tracking']}\n"
                content += "\n"
        else:
            content = "Non hai ancora effettuato ordini."

        dialog = ResultDialog("I Miei Ordini", content, self)
        dialog.exec_()

    def create_form_section(self, title):
        """Crea una sezione del form con stile Apple"""
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e5e7;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header della sezione
        header = QLabel(title)
        header.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        header.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                background: transparent;
                padding: 16px 20px 8px 20px;
            }
        """)
        layout.addWidget(header)

        # Linea separatrice
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: #e5e5e7;")
        layout.addWidget(separator)

        # Container per il contenuto
        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        layout.addWidget(content_container)

        section.setLayout(layout)
        return section, content_container

    def create_main_page(self):
        """Crea la pagina principale per bibliotecari e librai"""
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # Sfondo con gradiente
        self.main_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f5f5f7);
            }
        """)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        welcome_label = QLabel(f'Benvenuto, {self.current_user["nome"] if self.current_user else "Amministratore"}!')
        welcome_label.setFont(QFont('SF Pro Display', 24, QFont.Bold))
        welcome_label.setStyleSheet("color: #1d1d1f; background: transparent;")
        header_layout.addWidget(welcome_label)

        role_name = {
            'bibliotecario': 'Bibliotecario',
            'libraio': 'Libraio',
            'utente': 'Utente'
        }.get(self.current_role, 'Amministratore')

        subtitle_label = QLabel(f'Pannello di controllo {role_name.lower()}')
        subtitle_label.setFont(QFont('SF Pro Text', 16))
        subtitle_label.setStyleSheet("color: #86868b; background: transparent;")
        header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # Sezione azioni principali
        actions_section, actions_container = self.create_form_section("⚙️ Azioni Disponibili")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(15)
        actions_layout.setContentsMargins(20, 20, 20, 20)

        # Griglia per pulsanti
        button_grid = QGridLayout()
        button_grid.setSpacing(15)

        # Pulsanti comuni a tutti i ruoli amministrativi
        self.btn_aggiungi = QPushButton('➕ Aggiungi Libro')
        self.btn_aggiungi.setFont(QFont('SF Pro Text', 16, QFont.Bold))
        self.btn_aggiungi.setMinimumHeight(50)
        self.btn_aggiungi.setStyleSheet(get_primary_button_stylesheet())
        self.btn_aggiungi.clicked.connect(self.aggiungi_libro)
        button_grid.addWidget(self.btn_aggiungi, 0, 0)

        self.btn_rimuovi = QPushButton('🗑️ Rimuovi Libro')
        self.btn_rimuovi.setFont(QFont('SF Pro Text', 16))
        self.btn_rimuovi.setMinimumHeight(50)
        self.btn_rimuovi.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_rimuovi.clicked.connect(self.rimuovi_libro)
        button_grid.addWidget(self.btn_rimuovi, 0, 1)

        self.btn_modifica = QPushButton('✏️ Modifica Libro')
        self.btn_modifica.setFont(QFont('SF Pro Text', 16))
        self.btn_modifica.setMinimumHeight(50)
        self.btn_modifica.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_modifica.clicked.connect(self.modifica_libro)
        button_grid.addWidget(self.btn_modifica, 1, 0)

        self.btn_cerca_titolo = QPushButton('🔍 Cerca per Titolo')
        self.btn_cerca_titolo.setFont(QFont('SF Pro Text', 16))
        self.btn_cerca_titolo.setMinimumHeight(50)
        self.btn_cerca_titolo.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_cerca_titolo.clicked.connect(self.cerca_titolo)
        button_grid.addWidget(self.btn_cerca_titolo, 1, 1)

        self.btn_cerca_autore = QPushButton('👤 Cerca per Autore')
        self.btn_cerca_autore.setFont(QFont('SF Pro Text', 16))
        self.btn_cerca_autore.setMinimumHeight(50)
        self.btn_cerca_autore.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_cerca_autore.clicked.connect(self.cerca_autore)
        button_grid.addWidget(self.btn_cerca_autore, 2, 0)

        self.btn_presta = QPushButton('📚 Presta Libro')
        self.btn_presta.setFont(QFont('SF Pro Text', 16))
        self.btn_presta.setMinimumHeight(50)
        self.btn_presta.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_presta.clicked.connect(self.presta_libro)
        button_grid.addWidget(self.btn_presta, 2, 1)

        self.btn_riprendi = QPushButton('↩️ Restituisci Libro')
        self.btn_riprendi.setFont(QFont('SF Pro Text', 16))
        self.btn_riprendi.setMinimumHeight(50)
        self.btn_riprendi.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_riprendi.clicked.connect(self.riprendi_libro)
        button_grid.addWidget(self.btn_riprendi, 3, 0)

        self.btn_mostra_catalogo = QPushButton('📖 Catalogo Completo')
        self.btn_mostra_catalogo.setFont(QFont('SF Pro Text', 16))
        self.btn_mostra_catalogo.setMinimumHeight(50)
        self.btn_mostra_catalogo.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_mostra_catalogo.clicked.connect(self.mostra_catalogo)
        button_grid.addWidget(self.btn_mostra_catalogo, 3, 1)

        self.btn_mostra_prestati = QPushButton('📋 Libri Prestati')
        self.btn_mostra_prestati.setFont(QFont('SF Pro Text', 16))
        self.btn_mostra_prestati.setMinimumHeight(50)
        self.btn_mostra_prestati.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_mostra_prestati.clicked.connect(self.mostra_libri_prestati)
        button_grid.addWidget(self.btn_mostra_prestati, 4, 0)

        self.btn_mostra_autori = QPushButton('✍️ Lista Autori')
        self.btn_mostra_autori.setFont(QFont('SF Pro Text', 16))
        self.btn_mostra_autori.setMinimumHeight(50)
        self.btn_mostra_autori.setStyleSheet(get_secondary_button_stylesheet())
        self.btn_mostra_autori.clicked.connect(self.mostra_autori)
        button_grid.addWidget(self.btn_mostra_autori, 4, 1)

        actions_layout.addLayout(button_grid)
        actions_container.setLayout(actions_layout)
        layout.addWidget(actions_section)

        # Footer con logout
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        logout_btn = QPushButton('Logout')
        logout_btn.setFont(QFont('SF Pro Text', 14))
        logout_btn.setStyleSheet("""
            QPushButton {
                color: #86868b;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #007aff;
            }
        """)
        logout_btn.clicked.connect(self.perform_logout)
        footer_layout.addWidget(logout_btn)

        layout.addLayout(footer_layout)

        self.main_widget.setLayout(layout)
        self.stacked_widget.addWidget(self.main_widget)

    def show_welcome_page(self):
        """Mostra la pagina di benvenuto"""
        self.stacked_widget.setCurrentIndex(0)

    def show_main_page(self):
        """Mostra la pagina principale appropriata per il ruolo dell'utente"""
        # Controlla se l'utente è autenticato
        if not self.current_user:
            QMessageBox.warning(self, 'Accesso Negato', 'Devi effettuare il login per accedere al sistema.')
            self.show_welcome_page()
            return

        # Controlla il ruolo e mostra la pagina appropriata
        user_role = self.current_user.get('ruolo')
        if user_role == 'utente':
            # Utenti normali vanno alla pagina di ricerca
            self.stacked_widget.setCurrentWidget(self.user_search_widget)
        else:
            # Bibliotecari e librai vanno alla pagina principale amministrativa
            self.stacked_widget.setCurrentWidget(self.main_widget)

    def aggiungi_libro(self):
        """Aggiunge un nuovo libro"""
        dialog = AddBookDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                titolo, autore, genere, anno, pagine, prezzo = dialog.get_data()
                if titolo and autore and genere and anno and pagine and prezzo:
                    libro = Libro(titolo, autore, genere, int(anno), int(pagine), float(prezzo))
                    self.db.save_libro(libro)
                    QMessageBox.information(self, 'Successo', f"Libro '{titolo}' aggiunto alla biblioteca.")
                else:
                    QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori.')
            except ValueError as e:
                QMessageBox.warning(self, 'Errore', f"Dati non validi: {str(e)}. Assicurati che anno, pagine e prezzo siano numeri.")
            except Exception as e:
                QMessageBox.critical(self, 'Errore Database', f"Si è verificato un errore durante l'aggiunta: {str(e)}")

    def rimuovi_libro(self):
        """Rimuove un libro"""
        titolo, ok = QInputDialog.getText(self, 'Rimuovi Libro', 'Inserisci il titolo del libro da rimuovere:')
        if ok and titolo:
            if self.db.rimuovi_libro(titolo):
                QMessageBox.information(self, 'Successo', f"Libro '{titolo}' rimosso dalla biblioteca.")
            else:
                QMessageBox.warning(self, 'Errore', f"Nessun libro trovato con il titolo '{titolo}'.")

    def cerca_titolo(self):
        """Cerca un libro per titolo"""
        titolo, ok = QInputDialog.getText(self, 'Cerca per Titolo', 'Inserisci il titolo:')
        if ok and titolo:
            libro = self.db.cerca_titolo(titolo)
            if libro:
                self.show_result_dialog("Libro trovato", str(libro))
            else:
                self.show_result_dialog("Risultato", f"Nessun libro trovato con il titolo '{titolo}'.")

    def cerca_autore(self):
        """Cerca un libro per autore"""
        autore, ok = QInputDialog.getText(self, 'Cerca per Autore', 'Inserisci l\'autore:')
        if ok and autore:
            libro = self.db.cerca_autore(autore)
            if libro:
                self.show_result_dialog("Libro trovato", str(libro))
            else:
                self.show_result_dialog("Risultato", f"Nessun libro trovato dell'autore '{autore}'.")

    def presta_libro(self):
        """Presta un libro"""
        titolo, ok = QInputDialog.getText(self, 'Presta Libro', 'Inserisci il titolo del libro da prestare:')
        if ok and titolo:
            libro = self.db.presta_libro(titolo)
            if libro:
                self.show_result_dialog("Successo", f"Libro '{libro.titolo}' prestato con successo.")
            else:
                self.show_result_dialog("Errore", f"Il libro '{titolo}' non è disponibile per il prestito.")

    def riprendi_libro(self):
        """Restituisce un libro prestato"""
        titolo, ok = QInputDialog.getText(self, 'Riprendi Libro', 'Inserisci il titolo del libro da restituire:')
        if ok and titolo:
            libro = self.db.riprendi_libro(titolo)
            if libro:
                self.show_result_dialog("Successo", f"Libro '{libro.titolo}' restituito con successo.")
            else:
                self.show_result_dialog("Errore", f"Il libro '{titolo}' non è stato restituito con successo.")

    def mostra_libri_prestati(self):
        """Mostra i libri prestati"""
        try:
            libri = self.db.mostra_libri_prestati()
            if libri:
                self.show_result_dialog("Libri Prestati", "\n".join(libri))
            else:
                self.show_result_dialog("Libri Prestati", "Nessun libro prestato.")
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def mostra_catalogo(self):
        """Mostra il catalogo completo"""
        try:
            libri = self.db.load_libri()
            self.show_result_dialog("Catalogo della Biblioteca", "\n".join([str(libro) for libro in libri]))
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def mostra_autori(self):
        """Mostra la lista degli autori"""
        try:
            autori = self.db.mostra_autori()
            self.show_result_dialog("Lista degli Autori", "\n".join(autori))
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f"Si è verificato un errore: {str(e)}")

    def show_result_dialog(self, title, content):
        """Mostra un dialog con i risultati"""
        dialog = ResultDialog(title, content, self)
        dialog.exec_()

    def modifica_libro(self):
        """Modifica un libro esistente"""
        titolo, ok = QInputDialog.getText(self, 'Modifica Libro', 'Inserisci il titolo del libro da modificare:')
        if ok and titolo:
            libro = self.db.cerca_titolo(titolo)
            if libro:
                dialog = EditBookDialog(libro, self)
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        nuovo_titolo, autore, genere, anno, pagine, prezzo = dialog.get_data()
                        if nuovo_titolo and autore and genere and anno and pagine and prezzo:
                            nuovo_libro = Libro(nuovo_titolo, autore, genere, int(anno), int(pagine), float(prezzo))
                            nuovo_libro.disponibile = libro.disponibile  # Mantieni lo stato di disponibilità
                            if self.db.modifica_libro(titolo, nuovo_libro):
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