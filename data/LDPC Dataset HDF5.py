#fonctionne bien

import numpy as np
from pyldpc import make_ldpc, encode
import h5py

# Paramètres LDPC
n = 200           # Longueur du code
d_v = 2           # Degré des nœuds variables
d_c = 4           # Degré des nœuds de contrôle

# Générer les matrices H et G
H, G = make_ldpc(n, d_v, d_c, systematic=True, sparse=True)
k = G.shape[1]    # Nombre de bits d'information (extrait de la matrice G)

# Paramètres du dataset
snr_values = [0, 2, 4, 6]  # SNR en dB
samples_per_snr = 1000     # Nombre de blocs par SNR

# Créer un fichier HDF5 pour stocker le dataset
with h5py.File('ldpc_dataset.h5', 'w') as hf:

    # Créer des datasets pour les symboles reçus et les bits d'information
    received_symbols = hf.create_dataset(
        'code_word', 
        shape=(len(snr_values) * samples_per_snr, n), 
        dtype='float32'
    )
    info_bits = hf.create_dataset(
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
            # Encodage LDPC avec ajout de bruit (la fonction encode ajoute le bruit en fonction du SNR)
            codeword = encode(G, bits, snr_db)
            
            # Stockage dans le fichier HDF5
            received_symbols[idx] = codeword
            info_bits[idx] = bits
            idx += 1

print("Dataset HDF5 généré : ldpc_dataset.h5")
