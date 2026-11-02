from catalogue.models import Produit

CLE_SESSION = "panier"


class Panier:
    """Panier rangé dans la session : {identifiant produit: quantité}."""

    def __init__(self, request):
        self.session = request.session
        self.contenu = self.session.get(CLE_SESSION, {})

    def _sauver(self):
        self.session[CLE_SESSION] = self.contenu
        self.session.modified = True

    def quantite(self, produit):
        return self.contenu.get(str(produit.pk), 0)

    def definir(self, produit, quantite):
        """Fixe la quantité, plafonnée au stock. Renvoie la quantité retenue."""
        quantite = max(0, min(int(quantite), produit.stock))
        if quantite:
            self.contenu[str(produit.pk)] = quantite
        else:
            self.contenu.pop(str(produit.pk), None)
        self._sauver()
        return quantite

    def retirer(self, produit):
        self.contenu.pop(str(produit.pk), None)
        self._sauver()

    def vider(self):
        self.contenu = {}
        self._sauver()

    def lignes(self):
        """Lignes affichables ; les pièces retirées de la vente sont enlevées du panier."""
        produits = Produit.objects.en_vente().select_related("categorie").in_bulk([int(k) for k in self.contenu])
        lignes = []
        for cle, quantite in list(self.contenu.items()):
            produit = produits.get(int(cle))
            if produit is None:
                self.contenu.pop(cle)
                self._sauver()
                continue
            lignes.append({
                "produit": produit,
                "quantite": quantite,
                "sous_total": produit.prix_fcfa * quantite,
            })
        return lignes

    def articles(self):
        return [(int(k), q) for k, q in self.contenu.items()]

    def __len__(self):
        return sum(self.contenu.values())
