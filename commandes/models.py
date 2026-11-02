from django.conf import settings
from django.db import models
from django.urls import reverse


class Mode(models.TextChoices):
    RETRAIT = "retrait", "Retrait au magasin"
    LIVRAISON = "livraison", "Livraison à domicile"


class Paiement(models.TextChoices):
    MAGASIN = "magasin", "Au magasin, au retrait"
    ORANGE_MONEY = "orange_money", "Orange Money"
    MTN_MOMO = "mtn_momo", "MTN MoMo"
    WAVE = "wave", "Wave"
    ESPECES = "especes", "Espèces à la livraison"


PAIEMENTS_LIVRAISON = [Paiement.ORANGE_MONEY, Paiement.MTN_MOMO, Paiement.WAVE, Paiement.ESPECES]


class Statut(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    VALIDEE = "validee", "Validée"
    VERIFIEE = "verifiee", "Vérifiée"
    PREPARATION = "preparation", "En préparation"
    PRETE = "prete", "Prête au retrait"
    LIVRAISON = "livraison", "Livraison en cours"
    LIVREE = "livree", "Livrée"
    RETIREE = "retiree", "Retirée"
    ANNULEE = "annulee", "Annulée"


# Étapes de chaque parcours, dans l'ordre. Une commande n'avance que d'une étape à la fois.
PARCOURS = {
    Mode.RETRAIT: [Statut.EN_ATTENTE, Statut.VALIDEE, Statut.PREPARATION, Statut.PRETE, Statut.RETIREE],
    Mode.LIVRAISON: [Statut.EN_ATTENTE, Statut.VERIFIEE, Statut.PREPARATION, Statut.LIVRAISON, Statut.LIVREE],
}

# Étape à laquelle le stock est déduit (validation pour un retrait, vérification pour une livraison).
STATUTS_DEDUCTION_STOCK = {Statut.VALIDEE, Statut.VERIFIEE}

# Libellé du bouton qui fait passer la commande à l'étape indiquée.
ACTIONS = {
    Statut.VALIDEE: "Valider la commande",
    Statut.VERIFIEE: "Commande vérifiée",
    Statut.PREPARATION: "Commencer la préparation",
    Statut.PRETE: "Commande prête au retrait",
    Statut.LIVRAISON: "Confier au livreur",
    Statut.RETIREE: "Client a retiré",
    Statut.LIVREE: "Confirmer la livraison",
}


MESSAGES_CLIENT = {
    Statut.VALIDEE: "Votre commande est validée.",
    Statut.VERIFIEE: "Votre commande est vérifiée. Votre reçu est disponible.",
    Statut.PREPARATION: "Votre commande est en cours de préparation.",
    Statut.PRETE: "Votre commande est prête : vous pouvez venir la retirer au magasin.",
    Statut.LIVRAISON: "Votre commande est en cours de livraison.",
    Statut.LIVREE: "Votre commande a été livrée. Merci !",
    Statut.RETIREE: "Vous avez retiré votre commande. Merci !",
    Statut.ANNULEE: "Votre commande a été annulée.",
}


class Commande(models.Model):
    numero = models.CharField("numéro", max_length=20, unique=True, editable=False)
    date_creation = models.DateTimeField("date de création", auto_now_add=True)
    date_maj = models.DateTimeField("dernière mise à jour", auto_now=True)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="commandes"
    )
    mode = models.CharField(max_length=10, choices=Mode.choices)
    client_nom = models.CharField("nom", max_length=100)
    client_prenom = models.CharField("prénom", max_length=100)
    client_telephone = models.CharField("téléphone", max_length=10)
    adresse = models.TextField("adresse de livraison", blank=True)
    paiement = models.CharField(max_length=20, choices=Paiement.choices)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    total_fcfa = models.PositiveIntegerField("total (FCFA)", default=0)
    livreur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="livraisons",
    )
    encaisse = models.BooleanField("paiement encaissé", default=False)
    motif_annulation = models.TextField("motif d'annulation", blank=True)
    stock_deduit = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.numero

    def get_absolute_url(self):
        return reverse("commandes:detail", args=[self.numero])

    @property
    def etapes(self):
        return PARCOURS[self.mode]

    @property
    def etape_suivante(self):
        if self.statut == Statut.ANNULEE:
            return None
        etapes = self.etapes
        i = etapes.index(self.statut)
        return etapes[i + 1] if i + 1 < len(etapes) else None

    @property
    def action_suivante(self):
        suivante = self.etape_suivante
        return ACTIONS[suivante] if suivante else ""

    @property
    def est_terminee(self):
        return self.statut == Statut.ANNULEE or self.statut == self.etapes[-1]

    @property
    def annulable(self):
        return not self.est_terminee

    @property
    def recu_disponible(self):
        """Retrait : dès la commande. Livraison : après « Commande vérifiée »."""
        if self.statut == Statut.ANNULEE:
            return False
        if self.mode == Mode.RETRAIT:
            return True
        return self.statut != Statut.EN_ATTENTE

    @property
    def message_client(self):
        """Phrase affichée au client pour l'étape en cours."""
        if self.statut == Statut.EN_ATTENTE:
            action = "valider" if self.mode == Mode.RETRAIT else "vérifier"
            return f"Commande reçue : le magasin va la {action}."
        return MESSAGES_CLIENT.get(self.statut, "")

    def suivi(self):
        """Étapes du parcours avec leur état, pour la frise de suivi."""
        etapes = self.etapes
        rang = etapes.index(self.statut) if self.statut in etapes else -1
        return [
            {
                "libelle": Statut(s).label,
                "faite": i < rang or (i == rang and self.est_terminee),
                "en_cours": i == rang and not self.est_terminee,
            }
            for i, s in enumerate(etapes)
        ]


class LigneCommande(models.Model):
    """Le nom et le prix sont recopiés : un changement de prix ne touche pas les commandes passées.

    Si la pièce est supprimée du catalogue, la ligne reste (produit vide) : les reçus
    et l'historique gardent la référence, le nom et le prix recopiés.
    """

    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(
        "catalogue.Produit", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lignes_commande",
    )
    ref = models.CharField("référence", max_length=50)
    nom = models.CharField(max_length=200)
    prix_unitaire = models.PositiveIntegerField("prix unitaire (FCFA)")
    quantite = models.PositiveIntegerField("quantité")

    class Meta:
        verbose_name = "ligne de commande"
        verbose_name_plural = "lignes de commande"

    def __str__(self):
        return f"{self.quantite} × {self.nom}"

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite


class HistoriqueStatut(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="historique")
    statut = models.CharField(max_length=20, choices=Statut.choices)
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    commentaire = models.TextField(blank=True)

    class Meta:
        verbose_name = "historique de statut"
        verbose_name_plural = "historique des statuts"
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.commande} → {self.get_statut_display()}"
