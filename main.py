"""
Punto di ingresso principale per l'applicazione di gestione biblioteca
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui import BibliotecaGUI


def main():
    """Funzione principale per avviare l'applicazione"""
    app = QApplication(sys.argv)

    # Imposta il nome dell'applicazione
    app.setApplicationName("Gestione Biblioteca Digitale")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Biblioteca Digitale")

    # Crea e mostra l'interfaccia principale
    gui = BibliotecaGUI()
    gui.show()

    # Avvia il loop degli eventi
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()