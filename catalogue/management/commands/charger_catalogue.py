"""Charge le catalogue de départ (pièces, caractéristiques, prix, photos).

    python manage.py charger_catalogue

Sans risque à relancer : une pièce dont la référence existe déjà n'est pas modifiée,
sauf pour lui ajouter sa photo si elle n'en a pas.
"""

from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from catalogue.donnees.catalogue import PIECES
from catalogue.models import Categorie, Produit

PHOTOS = Path(__file__).resolve().parents[2] / "donnees" / "photos"


class Command(BaseCommand):
    help = "Ajoute les pièces du catalogue de départ avec leurs photos."

    def handle(self, *args, **options):
        ajoutees = photos = 0
        for slug, pieces in PIECES.items():
            categorie = Categorie.objects.get(slug=slug)
            for ref, nom, caract, prix, stock in pieces:
                produit, cree = Produit.objects.get_or_create(ref=ref, defaults={
                    "nom": nom, "caracteristiques": caract, "prix_fcfa": prix,
                    "stock": stock, "categorie": categorie,
                })
                ajoutees += cree
                fichier = PHOTOS / f"{ref}.jpg"
                if not produit.photo and fichier.exists():
                    with fichier.open("rb") as f:
                        produit.photo.save(fichier.name, File(f), save=True)
                    photos += 1
        self.stdout.write(self.style.SUCCESS(f"{ajoutees} pièce(s) ajoutée(s), {photos} photo(s) posée(s)."))
