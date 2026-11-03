"""Catalogue de départ : pièces courantes avec photo, caractéristiques et prix indicatifs.

Prix en FCFA : estimations du marché ivoirien (Abidjan) à vérifier et ajuster
dans Gestion → Pièces. Les photos sont dans catalogue/donnees/photos/<ref>.jpg
(domaine public / CC0, voir CREDITS.md).

Chargement : python manage.py charger_catalogue
"""

# slug de la catégorie : [(réf., nom, caractéristiques, prix FCFA, stock), ...]
PIECES = {
    "mecanique": [
        ("MEC-101", "Roulement à billes 6205-2RS",
         "Roulement rigide à une rangée de billes, étanche des deux côtés (joints caoutchouc).\n"
         "Dimensions : 25 × 52 × 15 mm. Acier chromé, prélubrifié à vie.\n"
         "Usage : moteurs électriques, pompes, ventilateurs, moyeux.",
         3500, 40),
        ("MEC-102", "Courroie trapézoïdale B50",
         "Courroie de transmission profil B (17 × 11 mm), longueur intérieure 1270 mm.\n"
         "Caoutchouc renforcé de fibres polyester, résistante à l'huile et à la chaleur.\n"
         "Usage : compresseurs, pompes, machines agricoles et d'atelier.",
         6000, 25),
        ("MEC-103", "Jeu de 6 clés mixtes 8 à 17 mm",
         "Clés plates d'un côté, à œil de l'autre : 8, 10, 12, 13, 14 et 17 mm.\n"
         "Acier chrome-vanadium, finition satinée. Livré avec support de rangement.",
         12500, 15),
        ("MEC-104", "Pompe à graisse manuelle 400 g",
         "Pompe à levier pour cartouche de graisse 400 g ou remplissage en vrac.\n"
         "Livrée avec flexible et embout de graissage standard.\n"
         "Usage : graissage des roulements, articulations et engins.",
         9000, 12),
    ],
    "automobile": [
        ("AUT-101", "Batterie auto 12 V 60 Ah",
         "Batterie de démarrage plomb-acide sans entretien.\n"
         "12 V, 60 Ah, courant de démarrage 540 A (EN). Borne + à droite.\n"
         "Pour berlines et petits SUV essence ou diesel.",
         55000, 8),
        ("AUT-102", "Filtre à huile moteur",
         "Filtre vissé à cartouche papier haute filtration, clapet anti-retour.\n"
         "Compatible nombreux modèles Toyota, Nissan, Hyundai et Kia.\n"
         "À remplacer à chaque vidange.",
         4500, 30),
        ("AUT-103", "Bougies d'allumage (jeu de 4)",
         "Bougies à électrode nickel, culot 14 mm, clé de 16 mm.\n"
         "Pour moteurs essence 4 cylindres. Remplacement conseillé tous les 20 000 à 30 000 km.",
         10000, 20),
        ("AUT-104", "Plaquettes de frein avant",
         "Jeu de 4 plaquettes pour un essieu avant, garniture semi-métallique.\n"
         "Faible bruit, bonne tenue à la chaleur. Témoin d'usure inclus.\n"
         "Indiquez le modèle du véhicule au comptoir pour vérifier la compatibilité.",
         15000, 10),
    ],
    "moto": [
        ("MOT-102", "Casque moto modulable",
         "Casque à mentonnière relevable, visière transparente anti-rayures.\n"
         "Coque ABS, intérieur amovible et lavable, fermeture micrométrique.\n"
         "Tailles M, L et XL.",
         30000, 10),
        ("MOT-103", "Batterie 12 V 7 Ah AGM",
         "Batterie plomb étanche (AGM), sans entretien, se monte dans tous les sens.\n"
         "12 V, 7 Ah. Dimensions : 151 × 65 × 94 mm.\n"
         "Pour motos 125 cm³, onduleurs et alarmes.",
         13000, 14),
        ("MOT-104", "Pneu moto 100/90-17",
         "Pneu avant ou arrière pour motos 125 à 200 cm³, jante 17 pouces.\n"
         "Sculpture route, bonne adhérence sur sol sec et mouillé. Utilisation avec chambre à air.",
         18000, 12),
    ],
    "electronique": [
        ("ELN-101", "Carte Arduino Uno R3",
         "Carte de développement à microcontrôleur ATmega328P, 14 E/S numériques dont 6 PWM, 6 entrées analogiques.\n"
         "Alimentation USB ou 7 à 12 V. Câble USB fourni.\n"
         "Idéale pour l'apprentissage, les prototypes et la domotique.",
         9000, 15),
        ("ELN-102", "Multimètre numérique",
         "Mesure de tensions continue et alternative (jusqu'à 600 V), courant (10 A), résistance,\n"
         "test de continuité sonore et de diodes. Écran LCD, cordons de mesure fournis.",
         8500, 18),
        ("ELN-103", "Fer à souder réglable 65 W",
         "Température réglable de 200 à 450 °C, chauffe rapide.\n"
         "Panne fine remplaçable, livré en boîte avec support.\n"
         "Pour l'électronique et le petit câblage.",
         15000, 9),
        ("ELN-104", "Plaque d'essai 830 points",
         "Plaque de prototypage sans soudure, 830 points de connexion, 2 rails d'alimentation.\n"
         "Fond adhésif, compatible fils de 0,3 à 0,8 mm et composants traversants.",
         2500, 40),
    ],
    "electricite": [
        ("ELC-101", "Disjoncteur boîtier moulé 3P 100 A",
         "Disjoncteur tripolaire de puissance, calibre 100 A, pouvoir de coupure 25 kA.\n"
         "Protection contre les surcharges et les courts-circuits.\n"
         "Pour tableaux généraux d'ateliers, commerces et immeubles.",
         85000, 4),
        ("ELC-102", "Prise industrielle 16 A 2P+T",
         "Prise femelle normalisée CEI 60309, 230 V, 16 A, 2 pôles + terre.\n"
         "Indice de protection IP44 (projections d'eau), boîtier bleu.\n"
         "Pour chantiers, ateliers et alimentations extérieures.",
         6500, 20),
        ("ELC-103", "Ampoule LED E27 12 W",
         "Ampoule LED culot E27, 12 W (équivalent 100 W), environ 1 050 lumens.\n"
         "Lumière blanche 6500 K, durée de vie 15 000 h, 220-240 V.",
         1500, 100),
        ("ELC-104", "Multiprise 3 prises avec câble",
         "Bloc de 3 prises 16 A avec terre, câble de 1,5 m.\n"
         "Puissance maximale 3 500 W. Pour la maison et le bureau.",
         5000, 30),
    ],
    "automatisme-industriel": [
        ("AUI-101", "Contacteur modulaire 25 A 4P",
         "Contacteur pour rail DIN, 4 pôles, 25 A, bobine 230 V AC.\n"
         "Fonctionnement silencieux. Commande d'éclairage, de chauffage et de petits moteurs.",
         20000, 10),
        ("AUI-102", "Automate programmable modulaire",
         "Automate (API) en rack : unité centrale, alimentation et modules d'entrées/sorties.\n"
         "Extensible selon le besoin, programmation sur PC.\n"
         "Pour la commande de machines et de lignes de production. Configuration sur devis.",
         350000, 2),
        ("AUI-105", "Alimentation 24 V DC 5 A rail DIN",
         "Alimentation à découpage pour armoire électrique : entrée 100-240 V AC, sortie 24 V DC, 5 A (120 W).\n"
         "Protection contre les courts-circuits et les surcharges, voyant de fonctionnement.",
         45000, 6),
    ],
}
