"""Remplit la base avec un catalogue d'exemple et des comptes de test.

    python manage.py donnees_demo

À ne pas lancer en production : le vrai catalogue se saisit dans Gestion ou l'admin.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from catalogue.models import Categorie, Produit
from comptes.models import GROUPE_LIVREUR, GROUPE_MAGASIN, Utilisateur

PIECES = {
    "mecanique": [
        ("MEC-001", "Roulement à billes 6204-2RS", "20 × 47 × 14 mm, étanche deux faces", 2500, 40),
        ("MEC-002", "Courroie trapézoïdale A42", "Section A, longueur 1067 mm", 3500, 25),
        ("MEC-003", "Joint spi 35 × 52 × 7", "Caoutchouc nitrile", 1200, 60),
    ],
    "automobile": [
        ("AUT-001", "Plaquettes de frein avant", "Toyota Corolla 2008-2018", 18000, 12),
        ("AUT-002", "Filtre à huile", "Compatible Toyota, Nissan, Hyundai", 4500, 30),
        ("AUT-003", "Bougie d'allumage NGK", "Électrode nickel, lot de 1", 3000, 50),
    ],
    "moto": [
        ("MOT-001", "Kit chaîne 428", "Chaîne + pignons, motos 125 cm³", 15000, 10),
        ("MOT-002", "Câble d'embrayage", "Universel, 125 cm³", 2500, 20),
        ("MOT-003", "Plaquettes de frein moto", "Avant, 125 cm³", 5000, 2),
    ],
    "electronique": [
        ("ELN-001", "Arduino Uno R3", "ATmega328P, câble USB fourni", 12000, 8),
        ("ELN-002", "Lot de 100 résistances 1/4 W", "Valeurs assorties 10 Ω à 1 MΩ", 3500, 15),
        ("ELN-003", "Régulateur LM7805", "5 V, 1,5 A, boîtier TO-220", 500, 100),
    ],
    "electricite": [
        ("ELC-001", "Câble souple 2,5 mm² (rouleau 100 m)", "Cuivre, isolant PVC", 45000, 6),
        ("ELC-002", "Disjoncteur 16 A", "Courbe C, 1P+N", 6500, 20),
        ("BAT-001", "Prise murale 2P+T", "16 A, blanche, encastrable", 2000, 45),
        ("BAT-002", "Interrupteur va-et-vient", "10 A, blanc", 1800, 40),
        ("BAT-003", "Tableau électrique 2 rangées", "26 modules, porte opaque", 28000, 0),
    ],
    "automatisme-industriel": [
        ("AUI-001", "Contacteur 25 A", "Bobine 230 V AC, 3 pôles", 22000, 7),
        ("AUI-002", "Relais temporisé", "Multifonction, 12-240 V", 19000, 5),
        ("AUI-003", "Capteur inductif M18", "PNP NO, portée 8 mm", 14000, 9),
    ],
}

MOT_DE_PASSE = "demo-comptoir-2026"

COMPTES = [
    ("0700000001", "Magasin", "Gérant", GROUPE_MAGASIN),
    ("0700000002", "Livreur", "Koffi", GROUPE_LIVREUR),
    ("0700000003", "Client", "Awa", None),
]


class Command(BaseCommand):
    help = "Crée un catalogue d'exemple et trois comptes de test (magasin, livreur, client)."

    def handle(self, *args, **options):
        nb = 0
        for slug, pieces in PIECES.items():
            categorie = Categorie.objects.get(slug=slug)
            for ref, nom, caract, prix, stock in pieces:
                _, cree = Produit.objects.get_or_create(ref=ref, defaults={
                    "nom": nom, "caracteristiques": caract, "prix_fcfa": prix,
                    "stock": stock, "categorie": categorie,
                })
                nb += cree
        self.stdout.write(f"{nb} pièce(s) ajoutée(s).")

        for telephone, nom, prenom, groupe in COMPTES:
            if Utilisateur.objects.filter(telephone=telephone).exists():
                continue
            u = Utilisateur.objects.create_user(telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                                                adresse_habituelle="Cocody, Riviera 2" if not groupe else "")
            if groupe:
                u.groups.add(Group.objects.get(name=groupe))
            self.stdout.write(f"Compte {groupe or 'Client'} : {telephone} / {MOT_DE_PASSE}")
