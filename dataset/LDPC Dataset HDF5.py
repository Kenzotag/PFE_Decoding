#Génération du jeu de données LDPC pour un mots de taille fixe , codé bruité et modulé(BPSK)

import numpy as np
from pyldpc import make_ldpc, encode
import h5py

# Paramètres LDPC
n = 200           # Longueur du code
d_v = 2           # Degré des nœuds variables
d_c = 4           # Degré des nœuds de contrôle

# Générer les matrices H et G
H, G = make_ldpc(n, d_v, d_c, systematic=True, sparse=True)
k = G.shape[1]    # Nombre de bits d'information 

# Paramètres du dataset
snr_values = [0, 2, 4, 6]  # SNR en dB
samples_per_snr = 10000     # Nombre de blocs par SNR

# Fonction pour moduler en BPSK
def bpsk_modulate(bits):
    return 2 * bits - 1  

# Fonction pour ajouter du bruit AWGN
def add_awgn(signal, snr_db):
    snr_linear = 10**(snr_db / 10)
    power_signal = np.mean(signal**2)
    noise_power = power_signal / snr_linear
    noise = np.sqrt(noise_power) * np.random.randn(*signal.shape)
    return signal + noise

# Créer un fichier HDF5 pour stocker le dataset
with h5py.File(r'C:\Users\CyberVortex\PFE_Decoding\data\ldpc_dataset.h5', 'w') as hf:

    # Créer des datasets pour les symboles reçus et les bits d'information
    code_word = hf.create_dataset(
        'code_word', 
        shape=(len(snr_values) * samples_per_snr, n), 
        dtype='float32'
    )
    message = hf.create_dataset(
        'message', 
        shape=(len(snr_values) * samples_per_snr, k), 
        dtype='int8'
    )
    
    # Génération et stockage des données
    idx = 0
    for snr_db in snr_values:
        for _ in range(samples_per_snr):
            # Génération d'un message aléatoire de taille k
            bits = np.random.randint(0, 2, k)
            
            # Encodage LDPC
            codeword = encode(G, bits, snr_db)

            # Modulation BPSK
            modulated_signal = bpsk_modulate(codeword)

            # Ajout du bruit AWGN
            received_signal = add_awgn(modulated_signal, snr_db)

            # Stockage dans le fichier HDF5
            code_word[idx] = received_signal
            message[idx] = bits
            idx += 1

print("Dataset HDF5 généré avec modulation BPSK : ldpc_dataset.h5")