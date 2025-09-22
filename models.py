"""
Modello dati per il sistema di gestione biblioteca
"""

class Libro:
    """Classe che rappresenta un libro"""
    def __init__(self, titolo, autore, genere, anno_pubblicazione, numero_pagine, prezzo, prezzo_nuovo=None, prezzo_usato=None, descrizione="", isbn=""):
        self.titolo = titolo
        self.autore = autore
        self.genere = genere
        self.anno_pubblicazione = anno_pubblicazione
        self.numero_pagine = numero_pagine
        self.prezzo = prezzo
        self.prezzo_nuovo = prezzo_nuovo
        self.prezzo_usato = prezzo_usato
        self.descrizione = descrizione
        self.isbn = isbn
        self.disponibile = True

    def __str__(self):
        prezzo_info = f"€{self.prezzo:.2f}"
        if self.prezzo_nuovo:
            prezzo_info += f" (Nuovo: €{self.prezzo_nuovo:.2f})"
        if self.prezzo_usato:
            prezzo_info += f" (Usato: €{self.prezzo_usato:.2f})"
        return f"{self.titolo} - {self.autore} ({self.anno_pubblicazione}) - {self.genere} - {self.numero_pagine} pagine - {prezzo_info}"

    def to_dict(self):
        """Converte l'oggetto in dizionario per serializzazione"""
        return {
            'titolo': self.titolo,
            'autore': self.autore,
            'genere': self.genere,
            'anno_pubblicazione': self.anno_pubblicazione,
            'numero_pagine': self.numero_pagine,
            'prezzo': self.prezzo,
            'prezzo_nuovo': self.prezzo_nuovo,
            'prezzo_usato': self.prezzo_usato,
            'descrizione': self.descrizione,
            'isbn': self.isbn,
            'disponibile': self.disponibile
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un oggetto Libro da un dizionario"""
        libro = cls(
            data['titolo'],
            data['autore'],
            data['genere'],
            data['anno_pubblicazione'],
            data['numero_pagine'],
            data['prezzo'],
            data.get('prezzo_nuovo'),
            data.get('prezzo_usato'),
            data.get('descrizione', ''),
            data.get('isbn', '')
        )
        libro.disponibile = data.get('disponibile', True)
        return libro