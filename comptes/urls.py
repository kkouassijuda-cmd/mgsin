from django.urls import path

from . import views

app_name = "comptes"

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="deconnexion"),
    path("profil/", views.profil, name="profil"),
    path("mot-de-passe/", views.MotDePasseView.as_view(), name="mot_de_passe"),
]
