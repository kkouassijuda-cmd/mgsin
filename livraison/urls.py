from django.urls import path

from . import views

app_name = "livraison"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("<str:numero>/", views.detail, name="detail"),
    path("<str:numero>/confirmer/", views.confirmer, name="confirmer"),
]
