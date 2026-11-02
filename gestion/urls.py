from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.tableau_de_bord, name="tableau_de_bord"),
    path("commande/<str:numero>/", views.commande, name="commande"),
    path("commande/<str:numero>/avancer/", views.commande_avancer, name="commande_avancer"),
    path("commande/<str:numero>/annuler/", views.commande_annuler, name="commande_annuler"),
    path("pieces/", views.produits, name="produits"),
    path("pieces/ajouter/", views.produit_modifier, name="produit_ajouter"),
    path("pieces/<int:pk>/", views.produit_modifier, name="produit_modifier"),
    path("pieces/<int:pk>/supprimer/", views.produit_supprimer, name="produit_supprimer"),
    path("clients/", views.clients, name="clients"),
    path("clients/<int:pk>/", views.client, name="client"),
]
