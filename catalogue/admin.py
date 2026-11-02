from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "ordre")
    list_editable = ("ordre",)
    prepopulated_fields = {"slug": ("nom",)}


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("ref", "nom", "categorie", "prix_fcfa", "stock", "en_vente", "supprimer")
    list_filter = ("categorie", "en_vente")
    list_editable = ("prix_fcfa", "stock", "en_vente")
    search_fields = ("ref", "nom", "caracteristiques")

    @admin.display(description="")
    def supprimer(self, obj):
        # Mène à la page de confirmation de Django : rien n'est supprimé sans validation.
        return format_html('<a class="deletelink" href="{}">Supprimer</a>',
                           reverse("admin:catalogue_produit_delete", args=[obj.pk]))
