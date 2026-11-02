from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalogue.models import Produit

from .forms import CommandeForm
from .models import Commande, Mode
from .panier import Panier
from .recu import generer_recu
from .services import CommandeImpossible, creer_commande


def _quantite(request, defaut):
    try:
        return int(request.POST.get("quantite", defaut))
    except (TypeError, ValueError):
        return defaut


def panier(request):
    lignes = Panier(request).lignes()
    return render(request, "commandes/panier.html", {
        "lignes": lignes,
        "total": sum(l["sous_total"] for l in lignes),
    })


@require_POST
def panier_ajouter(request, pk):
    produit = get_object_or_404(Produit.objects.en_vente(), pk=pk)
    p = Panier(request)
    demandee = p.quantite(produit) + max(1, _quantite(request, 1))
    retenue = p.definir(produit, demandee)
    if retenue == 0:
        messages.error(request, f"« {produit.nom} » est en rupture de stock.")
    elif retenue < demandee:
        messages.warning(request, f"Stock limité : {retenue} « {produit.nom} » dans votre panier.")
    else:
        messages.success(request, f"« {produit.nom} » ajouté au panier.")

    suivant = request.POST.get("suivant")
    if suivant and url_has_allowed_host_and_scheme(suivant, {request.get_host()}, request.is_secure()):
        return redirect(suivant)
    return redirect("commandes:panier")


@require_POST
def panier_modifier(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    demandee = _quantite(request, 0)
    retenue = Panier(request).definir(produit, demandee)
    if retenue < demandee:
        messages.warning(request, f"Stock limité : {retenue} « {produit.nom} » au maximum.")
    return redirect("commandes:panier")


@require_POST
def panier_retirer(request, pk):
    Panier(request).retirer(get_object_or_404(Produit, pk=pk))
    return redirect("commandes:panier")


@login_required
def commander(request):
    p = Panier(request)
    lignes = p.lignes()
    if not lignes:
        messages.info(request, "Votre panier est vide.")
        return redirect("catalogue:accueil")

    u = request.user
    form = CommandeForm(request.POST or None, initial={
        "mode": Mode.RETRAIT, "prenom": u.prenom, "nom": u.nom,
        "telephone": u.telephone, "adresse": u.adresse_habituelle,
    })
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            commande = creer_commande(
                u, p.articles(), mode=d["mode"], prenom=d["prenom"], nom=d["nom"],
                telephone=d["telephone"], adresse=d["adresse"], paiement=d["paiement"],
            )
        except CommandeImpossible as e:
            messages.error(request, str(e))
        else:
            p.vider()
            messages.success(request, f"Commande {commande.numero} enregistrée. Suivez son avancement sur cette page.")
            return redirect(commande)
    return render(request, "commandes/commander.html", {
        "form": form,
        "lignes": lignes,
        "total": sum(l["sous_total"] for l in lignes),
    })


@login_required
def mes_commandes(request):
    return render(request, "commandes/mes_commandes.html", {"commandes": request.user.commandes.all()})


@login_required
def mes_commandes_etat(request):
    """Fragment de la liste, rechargé régulièrement par actualiser.js."""
    reponse = render(request, "commandes/_liste_client.html", {"commandes": request.user.commandes.all()})
    reponse["Cache-Control"] = "no-store"
    return reponse


def _commande_du_client(request, numero):
    """Un client ne voit que ses propres commandes (404 sinon)."""
    return get_object_or_404(Commande.objects.prefetch_related("lignes"), numero=numero, client=request.user)


@login_required
def detail(request, numero):
    return render(request, "commandes/detail.html", {"commande": _commande_du_client(request, numero)})


@login_required
def etat(request, numero):
    """Fragment du suivi d'une commande, rechargé régulièrement par actualiser.js."""
    reponse = render(request, "commandes/_suivi_client.html", {"commande": _commande_du_client(request, numero)})
    reponse["Cache-Control"] = "no-store"
    return reponse


@login_required
def recu(request, numero):
    commande = get_object_or_404(Commande, numero=numero)
    if commande.client_id != request.user.pk and not request.user.est_magasin:
        raise Http404
    if not commande.recu_disponible:
        messages.info(request, "Le reçu sera disponible quand le magasin aura vérifié la commande.")
        return redirect(commande)
    reponse = HttpResponse(generer_recu(commande), content_type="application/pdf")
    reponse["Content-Disposition"] = f'attachment; filename="recu-{commande.numero}.pdf"'
    return reponse
