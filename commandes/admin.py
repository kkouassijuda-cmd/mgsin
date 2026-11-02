from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Commande, HistoriqueStatut, LigneCommande


class LigneInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = ("produit", "ref", "nom", "prix_unitaire", "quantite")
    can_delete = False


class HistoriqueInline(admin.TabularInline):
    model = HistoriqueStatut
    extra = 0
    readonly_fields = ("statut", "date", "utilisateur", "commentaire")
    can_delete = False


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    """Consultation seulement : les changements d'étape se font dans l'espace Gestion,
    qui applique les règles de stock et d'historique."""

    list_display = ("numero", "date_creation", "client_prenom", "client_nom", "mode", "statut", "total_fcfa", "encaisse", "traiter")
    list_filter = ("statut", "mode", "paiement", "encaisse")
    search_fields = ("numero", "client_nom", "client_prenom", "client_telephone")
    inlines = [LigneInline, HistoriqueInline]

    @admin.display(description="Action")
    def traiter(self, obj):
        return format_html('<a href="{}">Traiter dans la Gestion →</a>', self.view_on_site(obj))

    def view_on_site(self, obj):
        return reverse("gestion:commande", args=[obj.numero])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
