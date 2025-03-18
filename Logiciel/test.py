import sys
import numpy as np
from pyldpc import make_ldpc, encode
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QHBoxLayout, QMainWindow, QStackedWidget, QComboBox, QMessageBox
)
from PyQt6.QtGui import QClipboard


# Fonction de codage de Hamming avec logs de débogage
def hamming_encode(message):
    """Encode un message binaire en utilisant le code de Hamming (7,4)."""
    encoded_message = ""
    for i in range(0, len(message), 4):
        # Extraire 4 bits de données (ajouter des zéros si nécessaire)
        data = message[i:i+4]
        if len(data) < 4:
            data += "0" * (4 - len(data))  # Padding uniquement pour les derniers bits
        
        print(f"Bloc de données (4 bits) : {data}")  # Log pour débogage
        
        # Convertir les bits en entiers
        d1, d2, d3, d4 = map(int, data)
        
        # Calculer les bits de parité
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        
        print(f"Bits de parité : p1={p1}, p2={p2}, p3={p3}")  # Log pour débogage
        
        # Construire le mot de code (7 bits)
        codeword = f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}"
        encoded_message += codeword
        
        print(f"Mot de code Hamming : {codeword}")  # Log pour débogage
    
    return encoded_message


# Fonction de codage Turbo (inchangée)
def turbo_encode(message):
    """Encode un message binaire en utilisant un code Turbo simple."""
    def convolutional_encode(bits):
        encoded = []
        state = 0
        for bit in bits:
            output1 = bit ^ state
            output2 = bit ^ (state >> 1)
            encoded.extend([output1, output2])
            state = (state >> 1) | (bit << 1)
        return encoded
    
    encoded1 = convolutional_encode([int(bit) for bit in message])
    interleaved = [message[i] for i in range(len(message)) if i % 2 == 0] + \
                  [message[i] for i in range(len(message)) if i % 2 != 0]
    encoded2 = convolutional_encode([int(bit) for bit in interleaved])
    turbo_encoded = encoded1 + encoded2
    return ''.join(map(str, turbo_encoded))


# Fenêtre de codage source
class SourceEncodingWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Codage Source")
        self.setGeometry(100, 100, 500, 300)

        self.input_text = QTextEdit(self)
        self.encode_button = QPushButton("Appliquer codage source")

        self.source_encoded_label = QLabel("Résultat du codage source :")
        self.source_encoded_text = QTextEdit(self)
        self.source_encoded_text.setReadOnly(True)

        self.copy_button = QPushButton("Copier")
        self.next_button = QPushButton("Passer au codage canal")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Message d'entrée :"))
        layout.addWidget(self.input_text)
        layout.addWidget(self.encode_button)
        layout.addWidget(self.source_encoded_label)
        layout.addWidget(self.source_encoded_text)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.encode_button.clicked.connect(self.apply_source_encoding)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.next_button.clicked.connect(self.go_to_channel_encoding)

    def apply_source_encoding(self):
        """Convertir le message en binaire (codage ASCII)."""
        message = self.input_text.toPlainText()
        if not message:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un message.")
            return
        
        try:
            encoded_message = self.ascii_encoding(message)
            self.source_encoded_text.setPlainText(encoded_message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du codage : {str(e)}")

    def copy_to_clipboard(self):
        """Copier le message encodé dans le presse-papiers."""
        if not self.source_encoded_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Aucun message à copier.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.source_encoded_text.toPlainText())

    def go_to_channel_encoding(self):
        """Passer à la fenêtre de codage canal."""
        if not self.source_encoded_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord encoder un message.")
            return
        
        self.main_window.switch_to_window(1)

    def ascii_encoding(self, message):
        """Convertir un message en binaire (ASCII)."""
        return ''.join(format(ord(char), '08b') for char in message)


# Fenêtre de codage canal et bruit
class ChannelEncodingWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.n = 12
        self.d_v = 3
        self.d_c = 4
        self.seed = 42
        self.H, self.G = make_ldpc(self.n, self.d_v, self.d_c, seed=self.seed)

        self.setWindowTitle("Codage Canal et Bruit")
        self.setGeometry(100, 100, 500, 300)

        self.paste_label = QLabel("Collez ici le message codé source :")
        self.paste_text = QTextEdit(self)

        self.code_type = QComboBox()
        self.code_type.addItems(["Hamming", "LDPC", "Turbo"])

        self.apply_encoding_button = QPushButton("Appliquer codage canal")

        self.encoded_message_label = QLabel("Message après codage canal :")
        self.encoded_message_text = QTextEdit(self)
        self.encoded_message_text.setReadOnly(True)

        self.copy_encoded_button = QPushButton("Copier")

        self.noise_paste_label = QLabel("Collez ici le message après codage canal :")
        self.noise_paste_text = QTextEdit(self)

        self.noise_type = QComboBox()
        self.noise_type.addItems(["Gaussian", "Rayleigh"])

        self.noise_level = QComboBox()
        self.noise_level.addItems(["Faible", "Moyen", "Élevé"])

        self.apply_noise_button = QPushButton("Appliquer bruit")

        self.final_message_label = QLabel("Message après ajout de bruit :")
        self.final_message_text = QTextEdit(self)
        self.final_message_text.setReadOnly(True)

        self.copy_noisy_button = QPushButton("Copier le message bruité")

        self.next_button = QPushButton("Passer au décodage avec IA")
        self.back_button = QPushButton("Retour")

        layout = QVBoxLayout()
        layout.addWidget(self.paste_label)
        layout.addWidget(self.paste_text)
        layout.addWidget(QLabel("Type de code canal :"))
        layout.addWidget(self.code_type)
        layout.addWidget(self.apply_encoding_button)
        layout.addWidget(self.encoded_message_label)
        layout.addWidget(self.encoded_message_text)
        layout.addWidget(self.copy_encoded_button)

        layout.addWidget(self.noise_paste_label)
        layout.addWidget(self.noise_paste_text)
        layout.addWidget(QLabel("Type de bruit :"))
        layout.addWidget(self.noise_type)
        layout.addWidget(QLabel("Niveau de bruit :"))
        layout.addWidget(self.noise_level)
        layout.addWidget(self.apply_noise_button)
        layout.addWidget(self.final_message_label)
        layout.addWidget(self.final_message_text)
        layout.addWidget(self.copy_noisy_button)

        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.back_button)
        navigation_layout.addWidget(self.next_button)

        layout.addLayout(navigation_layout)
        self.setLayout(layout)

        self.apply_encoding_button.clicked.connect(self.apply_channel_encoding)
        self.copy_encoded_button.clicked.connect(self.copy_encoded_message)
        self.apply_noise_button.clicked.connect(self.apply_noise)
        self.copy_noisy_button.clicked.connect(self.copy_noisy_message)
        self.next_button.clicked.connect(self.go_to_decoding)
        self.back_button.clicked.connect(self.go_back)

    def apply_channel_encoding(self):
        """Appliquer le codage canal (Hamming, LDPC, Turbo)."""
        source_message = self.paste_text.toPlainText()
        if not source_message:
            QMessageBox.warning(self, "Erreur", "Veuillez coller un message binaire valide.")
            return
        
        code_type = self.code_type.currentText()

        try:
            if code_type == "Hamming":
                encoded_message = hamming_encode(source_message)
            elif code_type == "LDPC":
                encoded_message = self.ldpc_encode(source_message)
            elif code_type == "Turbo":
                encoded_message = turbo_encode(source_message)
            else:
                encoded_message = source_message

            self.encoded_message_text.setPlainText(encoded_message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du codage canal : {str(e)}")

    def ldpc_encode(self, message):
        """Encode un message binaire en utilisant le code LDPC."""
        message_bits = np.array([int(bit) for bit in message])
        k = self.G.shape[1]
        if len(message_bits) % k != 0:
            padding_length = k - (len(message_bits) % k)
            message_bits = np.pad(message_bits, (0, padding_length), 'constant')
        num_blocks = len(message_bits) // k
        encoded_blocks = []
        for i in range(num_blocks):
            block = message_bits[i * k : (i + 1) * k]
            encoded_block = encode(self.G, block, snr=100)
            encoded_blocks.append(encoded_block)
        encoded_message = np.concatenate(encoded_blocks)
        binary_message = np.where(encoded_message > 0, 1, 0)
        return ''.join(map(str, binary_message))

    def copy_encoded_message(self):
        """Copier le message encodé dans le presse-papiers."""
        if not self.encoded_message_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Aucun message à copier.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.encoded_message_text.toPlainText())

    def apply_noise(self):
        """Appliquer du bruit au message."""
        message = self.noise_paste_text.toPlainText()
        if not message:
            QMessageBox.warning(self, "Erreur", "Veuillez coller un message binaire valide.")
            return
        
        noise_type = self.noise_type.currentText()
        noise_level = self.noise_level.currentText()
        snr = {"Faible": 5, "Moyen": 10, "Élevé": 20}[noise_level]

        try:
            if noise_type == "Gaussian":
                final_message = self.gaussian_noise(message, snr)
            elif noise_type == "Rayleigh":
                final_message = self.rayleigh_noise(message, snr)
            else:
                final_message = message

            self.final_message_text.setPlainText(final_message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout de bruit : {str(e)}")

    def copy_noisy_message(self):
        """Copier le message bruité dans le presse-papiers."""
        if not self.final_message_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Aucun message à copier.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.final_message_text.toPlainText())

    def go_to_decoding(self):
        """Passer à la fenêtre de décodage."""
        if not self.final_message_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord appliquer du bruit.")
            return
        
        self.main_window.switch_to_window(2)

    def go_back(self):
        """Revenir à la fenêtre précédente."""
        self.main_window.switch_to_window(0)

    def gaussian_noise(self, message, snr):
        """Ajouter un bruit Gaussien au message."""
        message_bits = np.array([int(bit) for bit in message])
        noise = np.random.normal(0, 1 / snr, len(message_bits))
        noisy_message = message_bits + noise
        return ''.join(map(str, np.where(noisy_message > 0.5, 1, 0)))

    def rayleigh_noise(self, message, snr):
        """Ajouter un bruit Rayleigh au message."""
        message_bits = np.array([int(bit) for bit in message])
        noise = np.random.rayleigh(1 / snr, len(message_bits))
        noisy_message = message_bits + noise
        return ''.join(map(str, np.where(noisy_message > 0.5, 1, 0)))


# Fenêtre de décodage avec IA
class DecodingWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Décodage avec IA")
        self.setGeometry(100, 100, 500, 300)

        self.paste_label = QLabel("Collez ici le message bruyant :")
        self.paste_text = QTextEdit(self)

        self.decode_button = QPushButton("Décoder avec IA")

        self.decoded_message_label = QLabel("Message décodé :")
        self.decoded_message_text = QTextEdit(self)
        self.decoded_message_text.setReadOnly(True)

        self.copy_decoded_button = QPushButton("Copier")

        self.back_button = QPushButton("Retour")

        layout = QVBoxLayout()
        layout.addWidget(self.paste_label)
        layout.addWidget(self.paste_text)
        layout.addWidget(self.decode_button)
        layout.addWidget(self.decoded_message_label)
        layout.addWidget(self.decoded_message_text)
        layout.addWidget(self.copy_decoded_button)
        layout.addWidget(self.back_button)

        self.setLayout(layout)

        self.decode_button.clicked.connect(self.apply_ai_decoding)
        self.copy_decoded_button.clicked.connect(self.copy_decoded_message)
        self.back_button.clicked.connect(self.go_back)

    def apply_ai_decoding(self):
        """Simuler le décodage avec IA."""
        noisy_message = self.paste_text.toPlainText()
        if not noisy_message:
            QMessageBox.warning(self, "Erreur", "Veuillez coller un message binaire valide.")
            return
        
        try:
            decoded_message = self.simulate_ai_decoding(noisy_message)
            self.decoded_message_text.setPlainText(decoded_message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du décodage : {str(e)}")

    def copy_decoded_message(self):
        """Copier le message décodé dans le presse-papiers."""
        if not self.decoded_message_text.toPlainText():
            QMessageBox.warning(self, "Erreur", "Aucun message à copier.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.decoded_message_text.toPlainText())

    def go_back(self):
        """Revenir à la fenêtre précédente."""
        self.main_window.switch_to_window(1)

    def simulate_ai_decoding(self, noisy_message):
        """Simuler le décodage avec IA."""
        return "Message décodé par IA: " + noisy_message


# Application principale
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Encodage et Décodage - PFE")
        self.setGeometry(100, 100, 500, 300)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.source_encoding_window = SourceEncodingWindow(self)
        self.channel_encoding_window = ChannelEncodingWindow(self)
        self.decoding_window = DecodingWindow(self)

        self.central_widget.addWidget(self.source_encoding_window)
        self.central_widget.addWidget(self.channel_encoding_window)
        self.central_widget.addWidget(self.decoding_window)

    def switch_to_window(self, index):
        """Changer de fenêtre."""
        self.central_widget.setCurrentIndex(index)


# Exécution de l'application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec()