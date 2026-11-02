from django.urls import path

from . import views

app_name = "commandes"

urlpatterns = [
    path("panier/", views.panier, name="panier"),
    path("panier/ajouter/<int:pk>/", views.panier_ajouter, name="panier_ajouter"),
    path("panier/modifier/<int:pk>/", views.panier_modifier, name="panier_modifier"),
    path("panier/retirer/<int:pk>/", views.panier_retirer, name="panier_retirer"),
    path("commander/", views.commander, name="commander"),
    path("", views.mes_commandes, name="mes_commandes"),
    path("etat/", views.mes_commandes_etat, name="mes_commandes_etat"),
    path("<str:numero>/", views.detail, name="detail"),
    path("<str:numero>/etat/", views.etat, name="etat"),
    path("<str:numero>/recu.pdf", views.recu, name="recu"),
]
