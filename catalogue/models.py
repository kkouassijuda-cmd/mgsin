from django.db import models
from django.urls import reverse


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    ordre = models.PositiveSmallIntegerField(default=0, help_text="Position dans le menu.")

    class Meta:
        verbose_name = "catégorie"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("catalogue:categorie", args=[self.slug])


class ProduitQuerySet(models.QuerySet):
    def en_vente(self):
        return self.filter(en_vente=True)


class Produit(models.Model):
    ref = models.CharField("référence", max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="produits", verbose_name="catégorie")
    caracteristiques = models.TextField("caractéristiques", blank=True)
    prix_fcfa = models.PositiveIntegerField("prix (FCFA)")
    stock = models.PositiveIntegerField(default=0)
    en_vente = models.BooleanField("en vente", default=True)
    photo = models.ImageField(upload_to="produits/", blank=True)

    objects = ProduitQuerySet.as_manager()

    class Meta:
        verbose_name = "produit"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.ref} · {self.nom}"

    def get_absolute_url(self):
        return reverse("catalogue:produit", args=[self.pk])

    @property
    def disponible(self):
        return self.en_vente and self.stock > 0
