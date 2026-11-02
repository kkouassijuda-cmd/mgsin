from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from commandes.models import Commande, Paiement, Statut
from commandes.services import CommandeImpossible, avancer
from comptes.roles import livreur_requis


def _mes_livraisons(request):
    """Le livreur ne voit que les commandes en livraison qui lui sont confiées."""
    return Commande.objects.filter(statut=Statut.LIVRAISON, livreur=request.user)


@livreur_requis
def liste(request):
    return render(request, "livraison/liste.html", {
        "commandes": _mes_livraisons(request).prefetch_related("lignes").order_by("date_maj"),
    })


@livreur_requis
def detail(request, numero):
    commande = get_object_or_404(_mes_livraisons(request).prefetch_related("lignes"), numero=numero)
    return render(request, "livraison/detail.html", {
        "commande": commande,
        "especes": commande.paiement == Paiement.ESPECES,
    })


@require_POST
@livreur_requis
def confirmer(request, numero):
    commande = get_object_or_404(_mes_livraisons(request), numero=numero)
    try:
        avancer(commande, request.user, encaisse=request.POST.get("encaisse") == "on")
    except CommandeImpossible as e:
        messages.error(request, str(e))
        return redirect("livraison:detail", numero)
    messages.success(request, f"Livraison {commande.numero} confirmée.")
    return redirect("livraison:liste")
