import numpy as np
import random
import string
import csv
import pyldpc

# -----------------------------
# Fonctions de génération de données
# -----------------------------

def generate_random_word(min_length=3, max_length=12):
    """
    Génère un mot aléatoire avec une longueur variable entre min_length et max_length.
    """
    length = random.randint(min_length, max_length)
    letters = string.ascii_letters  # Lettres majuscules et minuscules
    return ''.join(random.choices(letters, k=length))

def text_to_binary(text):
    """
    Convertit un texte en une séquence binaire.
    Chaque caractère est encodé en ASCII sur 8 bits.
    """
    binary_seq = []
    for char in text:
        bin_char = format(ord(char), '08b')
        binary_seq.extend([int(bit) for bit in bin_char])
    return np.array(binary_seq)

def ldpc_encode(binary_seq, G):
    """
    Effectue le codage LDPC sur la séquence binaire donnée en utilisant la matrice de génération G.
    """
    return np.mod(np.dot(binary_seq, G), 2)

def bpsk_modulate(binary_seq):
    """
    Mappe les bits en symboles BPSK : 0 -> -1, 1 -> +1
    """
    return np.where(binary_seq == 0, -1.0, 1.0)

def add_awgn_noise(signal, snr_db):
    """
    Ajoute un bruit gaussien au signal modulé en fonction du SNR spécifié.
    """
    snr_linear = 10 ** (snr_db / 10.0)
    noise_std = np.sqrt(1.0 / snr_linear)
    noise = np.random.normal(0, noise_std, size=signal.shape)
    return signal + noise

def generate_example(snr_db, G, min_word_length=3, max_word_length=12):
    """
    Génère un exemple complet avec codage LDPC et bruit AWGN.
    """
    # 1. Générer un mot aléatoire
    word = generate_random_word(min_length=min_word_length, max_length=max_word_length)
    
    # 2. Convertir le mot en trame binaire
    binary_source = text_to_binary(word)
    
    # 3. Appliquer le codage LDPC
    binary_encoded = ldpc_encode(binary_source, G)
    
    # 4. Moduler la trame en BPSK
    modulated_signal = bpsk_modulate(binary_encoded)
    
    # 5. Ajouter le bruit gaussien
    noisy_signal = add_awgn_noise(modulated_signal, snr_db)
    
    return {
        'word': word,                    # Mot original
        'binary_label': binary_source,   # Trame binaire correcte
        'noisy_feature': noisy_signal    # Trame bruitée
    }

# -----------------------------
# Génération d'un grand jeu de données
# -----------------------------
def generate_dataset(num_examples=10000, snr_db_list=[0, 5, 10], min_word_length=3, max_word_length=12):
    """
    Génère un jeu de données avec un nombre spécifié d'exemples.
    """
    dataset = []
    # Définir les paramètres du code LDPC
    n = 7  # Nombre total de bits (codeword length)
    k = 4  # Nombre de bits d'information (message length)
    H, G = pyldpc.make_ldpc(n, k, 3, systematic=True)  # Matrice de parité H et matrice de génération G
    for i in range(num_examples):
        snr_db = random.choice(snr_db_list)
        example = generate_example(snr_db, G, min_word_length, max_word_length)
        example['snr_db'] = snr_db
        dataset.append(example)
        if (i + 1) % 1000 == 0:
            print(f"Exemples générés : {i + 1}")
    return dataset, G

if __name__ == '__main__':
    # Paramètres
    NUM_EXAMPLES = 10000
    SNR_DB_LIST = [0, 5, 10, 15]
    MIN_WORD_LENGTH = 3
    MAX_WORD_LENGTH = 12

    # Générer le dataset
    dataset, G = generate_dataset(
        num_examples=NUM_EXAMPLES,
        snr_db_list=SNR_DB_LIST,
        min_word_length=MIN_WORD_LENGTH,
        max_word_length=MAX_WORD_LENGTH
    )

    # Sauvegarder le dataset dans un fichier CSV
    with open('data6.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Écrire l'en-tête
        writer.writerow(['word', 'binary_label', 'noisy_feature', 'snr_db'])
        for example in dataset:
            # Convertir les listes numpy en chaînes pour l'écriture CSV
            word = example['word']
            binary_label = ''.join(map(str, example['binary_label']))
            noisy_feature = ','.join(map(str, example['noisy_feature']))
            snr_db = example['snr_db']
            writer.writerow([word, binary_label, noisy_feature, snr_db])

    print("Jeu de données généré et sauvegardé dans 'data6.csv'")
