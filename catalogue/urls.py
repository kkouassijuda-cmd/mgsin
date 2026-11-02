from django.urls import path

from . import views

app_name = "catalogue"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("categorie/<slug:slug>/", views.categorie, name="categorie"),
    path("piece/<int:pk>/", views.produit, name="produit"),
]
