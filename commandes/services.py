"""Règles métier des commandes.

Toute modification d'une commande (création, changement d'étape, annulation)
passe par ce module, dans une transaction, pour que le stock et l'historique
restent toujours justes.
"""

import secrets

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from catalogue.models import Produit

from .models import (
    Commande, HistoriqueStatut, LigneCommande, Mode, Paiement, Statut, STATUTS_DEDUCTION_STOCK,
)

ALPHABET_NUMERO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans 0/O ni 1/I, faciles à confondre


class CommandeImpossible(Exception):
    """Action refusée ; le message est affiché tel quel à l'utilisateur."""


def generer_numero():
    """Numéro au format CMD-AAMMJJ-XXXX."""
    date = timezone.localdate().strftime("%y%m%d")
    suffixe = "".join(secrets.choice(ALPHABET_NUMERO) for _ in range(4))
    return f"CMD-{date}-{suffixe}"


def _historiser(commande, utilisateur, commentaire=""):
    HistoriqueStatut.objects.create(
        commande=commande, statut=commande.statut, utilisateur=utilisateur, commentaire=commentaire
    )


def _verifier_stock(lignes):
    """lignes : liste de (produit verrouillé, quantité)."""
    manquants = [
        f"{p.nom} (demandé : {q}, en stock : {p.stock})"
        for p, q in lignes if not p.en_vente or p.stock < q
    ]
    if manquants:
        raise CommandeImpossible("Stock insuffisant pour : " + " ; ".join(manquants))


def creer_commande(client, articles, *, mode, prenom, nom, telephone, adresse="", paiement=None):
    """articles : liste de (produit_id, quantité). Le stock est contrôlé mais pas encore déduit."""
    if not articles:
        raise CommandeImpossible("Le panier est vide.")
    if mode == Mode.RETRAIT:
        paiement, adresse = Paiement.MAGASIN, ""
    elif not adresse.strip():
        raise CommandeImpossible("L'adresse de livraison est obligatoire.")

    quantites = {int(pid): int(q) for pid, q in articles if int(q) > 0}
    with transaction.atomic():
        produits = Produit.objects.select_for_update().in_bulk(quantites.keys())
        if len(produits) != len(quantites):
            raise CommandeImpossible("Une pièce du panier n'existe plus.")
        lignes = [(produits[pid], q) for pid, q in quantites.items()]
        _verifier_stock(lignes)

        for _ in range(10):
            try:
                with transaction.atomic():
                    commande = Commande.objects.create(
                        numero=generer_numero(), client=client, mode=mode,
                        client_prenom=prenom, client_nom=nom, client_telephone=telephone,
                        adresse=adresse, paiement=paiement,
                        total_fcfa=sum(p.prix_fcfa * q for p, q in lignes),
                    )
                break
            except IntegrityError:
                continue
        else:
            raise CommandeImpossible("Impossible d'attribuer un numéro de commande, réessayez.")

        LigneCommande.objects.bulk_create([
            LigneCommande(commande=commande, produit=p, ref=p.ref, nom=p.nom, prix_unitaire=p.prix_fcfa, quantite=q)
            for p, q in lignes
        ])
        _historiser(commande, client)
    return commande


def _deduire_stock(commande):
    lignes = list(commande.lignes.all())
    supprimees = [l.nom for l in lignes if l.produit_id is None]
    if supprimees:
        raise CommandeImpossible(
            "Pièce supprimée du catalogue : " + " ; ".join(supprimees)
            + ". Annulez cette commande et prévenez le client."
        )
    produits = Produit.objects.select_for_update().in_bulk([l.produit_id for l in lignes])
    besoins = {}
    for l in lignes:
        besoins[l.produit_id] = besoins.get(l.produit_id, 0) + l.quantite
    _verifier_stock([(produits[pid], q) for pid, q in besoins.items()])
    for pid, q in besoins.items():
        Produit.objects.filter(pk=pid).update(stock=F("stock") - q)
    commande.stock_deduit = True


def _remettre_stock(commande):
    for l in commande.lignes.all():
        Produit.objects.filter(pk=l.produit_id).update(stock=F("stock") + l.quantite)
    commande.stock_deduit = False


def avancer(commande, utilisateur, *, livreur=None, encaisse=None):
    """Fait passer la commande à l'étape suivante de son parcours."""
    with transaction.atomic():
        commande = Commande.objects.select_for_update().get(pk=commande.pk)
        suivante = commande.etape_suivante
        if suivante is None:
            raise CommandeImpossible("Cette commande est déjà terminée.")

        if suivante in STATUTS_DEDUCTION_STOCK:
            _deduire_stock(commande)
        if suivante == Statut.LIVRAISON:
            if livreur is None or not livreur.est_livreur:
                raise CommandeImpossible("Choisissez le livreur à qui confier la commande.")
            commande.livreur = livreur
        if suivante == Statut.LIVREE:
            if commande.paiement == Paiement.ESPECES and not encaisse:
                raise CommandeImpossible("Confirmez l'encaissement des espèces avant de valider la livraison.")
            commande.encaisse = bool(encaisse) or commande.encaisse
        if suivante == Statut.RETIREE:
            commande.encaisse = True  # payé au magasin, au retrait

        commande.statut = suivante
        commande.save()
        _historiser(commande, utilisateur)
    return commande


def annuler(commande, utilisateur, motif):
    """Annule la commande avant sa dernière étape ; le stock déjà déduit est remis en place."""
    motif = (motif or "").strip()
    if not motif:
        raise CommandeImpossible("Indiquez le motif de l'annulation : il sera visible par le client.")
    with transaction.atomic():
        commande = Commande.objects.select_for_update().get(pk=commande.pk)
        if not commande.annulable:
            raise CommandeImpossible("Cette commande ne peut plus être annulée.")
        if commande.stock_deduit:
            _remettre_stock(commande)
        commande.statut = Statut.ANNULEE
        commande.motif_annulation = motif
        commande.save()
        _historiser(commande, utilisateur, motif)
    return commande
