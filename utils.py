"""
Modulo per funzioni di utilità dell'applicazione biblioteca
"""

def get_input_stylesheet():
    """Restituisce lo stylesheet per i campi di input"""
    return """
        QLineEdit {
            border: 2px solid #d1d1d6;
            border-radius: 10px;
            padding: 12px 16px;
            background: white;
            color: #1d1d1f;
            selection-background-color: #007aff;
        }
        QLineEdit:focus {
            border-color: #007aff;
            background: #f8f9fa;
        }
        QLineEdit:hover {
            border-color: #c7c7cc;
        }
        QLineEdit::placeholder {
            color: #8e8e93;
        }
    """


def get_combobox_stylesheet():
    """Restituisce lo stylesheet per i combobox"""
    return """
        QComboBox {
            border: 2px solid #d1d1d6;
            border-radius: 10px;
            padding: 12px 16px;
            background: white;
            color: #1d1d1f;
            min-width: 200px;
        }
        QComboBox:focus {
            border-color: #007aff;
            background: #f8f9fa;
        }
        QComboBox:hover {
            border-color: #c7c7cc;
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 16px;
            height: 16px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            background: white;
            selection-background-color: #007aff;
            selection-color: white;
            padding: 4px;
        }
    """


def get_primary_button_stylesheet():
    """Restituisce lo stylesheet per il pulsante primario"""
    return """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #007aff, stop:1 #0056cc);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 18px;
            font-weight: bold;
            padding: 0;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0056cc, stop:1 #004499);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #004499, stop:1 #003366);
        }
        QPushButton:disabled {
            background: #c7c7cc;
            color: #8e8e93;
        }
    """


def get_secondary_button_stylesheet():
    """Restituisce lo stylesheet per i pulsanti secondari"""
    return """
        QPushButton {
            background: white;
            color: #1d1d1f;
            border: 2px solid #d1d1d6;
            border-radius: 12px;
            font-size: 16px;
            padding: 0;
        }
        QPushButton:hover {
            background: #f8f9fa;
            border-color: #007aff;
            color: #007aff;
        }
        QPushButton:pressed {
            background: #e0e0e0;
        }
        QPushButton:disabled {
            background: #f5f5f5;
            color: #8e8e93;
            border-color: #c7c7cc;
        }
    """