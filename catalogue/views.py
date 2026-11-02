from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Categorie, Produit

PRODUITS_PAR_PAGE = 24


def _liste(request, produits, categorie=None):
    recherche = request.GET.get("q", "").strip()
    if recherche:
        produits = produits.filter(
            Q(nom__icontains=recherche) | Q(ref__icontains=recherche) | Q(caracteristiques__icontains=recherche)
        )
    page = Paginator(produits.select_related("categorie"), PRODUITS_PAR_PAGE).get_page(request.GET.get("page"))
    return render(request, "catalogue/liste.html", {
        "categories": Categorie.objects.all(),
        "categorie": categorie,
        "recherche": recherche,
        "page": page,
    })


def accueil(request):
    return _liste(request, Produit.objects.en_vente())


def categorie(request, slug):
    cat = get_object_or_404(Categorie, slug=slug)
    return _liste(request, Produit.objects.en_vente().filter(categorie=cat), cat)


def produit(request, pk):
    piece = get_object_or_404(Produit.objects.en_vente().select_related("categorie"), pk=pk)
    return render(request, "catalogue/produit.html", {
        "categories": Categorie.objects.all(),
        "produit": piece,
    })
