# TechnoPièces

Site de vente de pièces détachées (prix en FCFA), avec gestion des commandes, retrait au magasin et livraison à domicile.

Stack : **Django 5.2 · PostgreSQL · templates HTML + CSS séparés · un peu de JavaScript · reçus PDF avec ReportLab**.

## Installation (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # puis remplir SECRET_KEY et les accès PostgreSQL
```

Créer la base PostgreSQL (une seule fois, avec `psql` ou DBeaver) :

```sql
CREATE USER comptoir WITH PASSWORD 'mot-de-passe';
CREATE DATABASE comptoir OWNER comptoir;
```

Puis :

```powershell
python manage.py migrate            # tables + 6 catégories + groupes Magasin et Livreur
python manage.py createsuperuser    # ton compte administrateur (identifiant = téléphone)
python manage.py charger_catalogue   # 22 pièces avec photos, caractéristiques et prix indicatifs
python manage.py donnees_demo       # facultatif : le même catalogue + comptes de test (jamais en production)
python manage.py runserver
```

Site : http://127.0.0.1:8000 · Administration : http://127.0.0.1:8000/admin/

> Sans PostgreSQL, mettre `DB_ENGINE=sqlite` dans `.env` pour travailler temporairement avec SQLite.

## Comptes de démonstration (`donnees_demo`)

| Rôle | Téléphone | Mot de passe |
|---|---|---|
| Magasin | 0700000001 | demo-comptoir-2026 |
| Livreur | 0700000002 | demo-comptoir-2026 |
| Client | 0700000003 | demo-comptoir-2026 |

Pour donner un rôle à un vrai compte : admin Django → Utilisateurs → groupe « Magasin » ou « Livreur ».

## Organisation du code

```
config/       réglages (lus dans .env), URLs principales
comptes/      utilisateurs (téléphone = identifiant), connexion, profil, rôles
catalogue/    catégories, pièces, stock, recherche, filtre |fcfa
commandes/    panier, commande, règles métier (services.py), reçu PDF (recu.py)
gestion/      tableau de bord du magasin, pièces et stock, clients
livraison/    espace livreur
templates/    pages HTML (aucun style dedans)
static/css/   un fichier CSS par espace : base, formulaires, boutique, commandes, gestion, livraison
static/js/    rafraîchissement des pages de suivi, formulaire de commande
```

Règle du projet : **le CSS ne se mélange jamais au HTML** (pas d'attribut `style`, pas de balise `<style>` ni de script en ligne). Un test le vérifie.

## Règles métier

- Parcours **retrait** : En attente → Validée → En préparation → Prête → Retirée (le magasin marque « Client a retiré »).
- Parcours **livraison** : En attente → Vérifiée → En préparation → En livraison → Livrée (le livreur confirme).
- Une commande n'avance que d'une étape à la fois. Toutes les modifications passent par `commandes/services.py`, dans une transaction.
- Le stock baisse à la validation (retrait) ou à la vérification (livraison) et remonte en cas d'annulation.
- Annulation possible avant la dernière étape, avec un motif visible par le client.
- Nom et prix recopiés dans chaque ligne de commande.
- Reçu PDF : tout de suite pour un retrait, après « Commande vérifiée » pour une livraison.
- Historique de chaque changement de statut (date, utilisateur).
- Numéro de commande unique : `CMD-AAMMJJ-XXXX`.

## Tests

```powershell
python manage.py test
```

## Reste à faire (étapes 6 à 8 du guide)

- Mise en ligne : hébergement, domaine, HTTPS, sauvegardes automatiques de la base.
- Paiement mobile automatique via un agrégateur (CinetPay, PayDunya ou Hub2) : application `paiements/`.
- Notifications SMS ou WhatsApp, réinitialisation du mot de passe par SMS.
