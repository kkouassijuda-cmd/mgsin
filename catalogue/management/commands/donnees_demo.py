"""Remplit la base avec le catalogue de départ (charger_catalogue) et des comptes de test.

    python manage.py donnees_demo

À ne pas lancer en production : le vrai catalogue se saisit dans Gestion ou l'admin.
"""

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from comptes.models import GROUPE_LIVREUR, GROUPE_MAGASIN, Utilisateur

MOT_DE_PASSE = "demo-comptoir-2026"

COMPTES = [
    ("0700000001", "Magasin", "Gérant", GROUPE_MAGASIN),
    ("0700000002", "Livreur", "Koffi", GROUPE_LIVREUR),
    ("0700000003", "Client", "Awa", None),
]


class Command(BaseCommand):
    help = "Crée un catalogue d'exemple et trois comptes de test (magasin, livreur, client)."

    def handle(self, *args, **options):
        call_command("charger_catalogue", stdout=self.stdout)

        for telephone, nom, prenom, groupe in COMPTES:
            if Utilisateur.objects.filter(telephone=telephone).exists():
                continue
            u = Utilisateur.objects.create_user(telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                                                adresse_habituelle="Cocody, Riviera 2" if not groupe else "")
            if groupe:
                u.groups.add(Group.objects.get(name=groupe))
            self.stdout.write(f"Compte {groupe or 'Client'} : {telephone} / {MOT_DE_PASSE}")
