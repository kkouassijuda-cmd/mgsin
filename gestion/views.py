from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.models import Categorie, Produit
from commandes.models import Commande, Mode, Statut
from commandes.services import CommandeImpossible, annuler, avancer
from comptes.models import Utilisateur
from comptes.roles import magasin_requis

from .forms import AnnulationForm, LivreurForm, ProduitForm

SECTIONS = [
    ("en-attente", "En attente", [Statut.EN_ATTENTE]),
    ("validees", "Validées / vérifiées", [Statut.VALIDEE, Statut.VERIFIEE]),
    ("preparation", "En préparation", [Statut.PREPARATION]),
    ("pretes", "Prêtes au retrait", [Statut.PRETE]),
    ("livraison", "Livraison en cours", [Statut.LIVRAISON]),
    ("terminees", "Terminées récemment", [Statut.RETIREE, Statut.LIVREE]),
    ("annulees", "Annulées récemment", [Statut.ANNULEE]),
]
STATUTS_FINAUX = {Statut.RETIREE, Statut.LIVREE, Statut.ANNULEE}
LIMITE_TERMINEES = 20
CLE_SEUIL = "gestion_seuil_stock_bas"


def seuil_stock_bas(request):
    """Seuil « stock bas » : choisi dans le filtre de la page Pièces et retenu pour la session
    (il sert aussi à l'alerte du tableau de bord). Par défaut : STOCK_SEUIL_BAS du .env."""
    saisi = request.GET.get("seuil", "").strip()
    if saisi.isdigit():
        request.session[CLE_SEUIL] = min(int(saisi), 100000)
    return request.session.get(CLE_SEUIL, settings.STOCK_SEUIL_BAS)


@magasin_requis
def tableau_de_bord(request):
    commandes = Commande.objects.select_related("livreur")
    mode = request.GET.get("mode", "")
    if mode in Mode.values:
        commandes = commandes.filter(mode=mode)
    recherche = request.GET.get("q", "").strip()
    if recherche:
        commandes = commandes.filter(
            Q(numero__icontains=recherche) | Q(client_telephone__icontains=recherche.replace(" ", ""))
            | Q(client_nom__icontains=recherche) | Q(client_prenom__icontains=recherche)
        )

    sections = []
    for ancre, titre, statuts in SECTIONS:
        qs = commandes.filter(statut__in=statuts)
        if STATUTS_FINAUX.issuperset(statuts):
            qs = qs.order_by("-date_maj")[:LIMITE_TERMINEES]
        else:
            qs = qs.order_by("date_creation")
        sections.append({"ancre": ancre, "titre": titre, "commandes": list(qs)})

    return render(request, "gestion/tableau_de_bord.html", {
        "sections": sections,
        "mode": mode,
        "modes": Mode.choices,
        "recherche": recherche,
        "stock_bas": Produit.objects.en_vente().filter(stock__lte=seuil_stock_bas(request)).count(),
    })


@magasin_requis
def commande(request, numero):
    cmd = get_object_or_404(
        Commande.objects.select_related("client", "livreur").prefetch_related("lignes", "historique__utilisateur"),
        numero=numero,
    )
    return render(request, "gestion/commande.html", {
        "commande": cmd,
        "livreur_form": LivreurForm() if cmd.etape_suivante == Statut.LIVRAISON else None,
        "annulation_form": AnnulationForm() if cmd.annulable else None,
        # La dernière étape d'une livraison est confirmée par le livreur, pas par le magasin.
        "peut_avancer": cmd.etape_suivante not in (None, Statut.LIVREE),
    })


@require_POST
@magasin_requis
def commande_avancer(request, numero):
    cmd = get_object_or_404(Commande, numero=numero)
    livreur = None
    if cmd.etape_suivante == Statut.LIVREE:
        messages.error(request, "La livraison est confirmée par le livreur depuis son espace.")
        return redirect("gestion:commande", numero)
    if cmd.etape_suivante == Statut.LIVRAISON:
        form = LivreurForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Choisissez le livreur à qui confier la commande.")
            return redirect("gestion:commande", numero)
        livreur = form.cleaned_data["livreur"]
    try:
        cmd = avancer(cmd, request.user, livreur=livreur)
    except CommandeImpossible as e:
        messages.error(request, str(e))
    else:
        messages.success(request, f"{cmd.numero} : {cmd.get_statut_display()}.")
    return redirect("gestion:commande", numero)


@require_POST
@magasin_requis
def commande_annuler(request, numero):
    cmd = get_object_or_404(Commande, numero=numero)
    form = AnnulationForm(request.POST)
    try:
        annuler(cmd, request.user, form.data.get("motif", ""))
    except CommandeImpossible as e:
        messages.error(request, str(e))
    else:
        messages.success(request, f"{cmd.numero} annulée.")
    return redirect("gestion:commande", numero)


@magasin_requis
def produits(request):
    qs = Produit.objects.select_related("categorie")
    categorie = request.GET.get("categorie", "")
    if categorie:
        qs = qs.filter(categorie__slug=categorie)
    recherche = request.GET.get("q", "").strip()
    if recherche:
        qs = qs.filter(Q(nom__icontains=recherche) | Q(ref__icontains=recherche))
    seuil = seuil_stock_bas(request)
    if request.GET.get("stock") == "bas":
        qs = qs.filter(stock__lte=seuil)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "gestion/produits.html", {
        "page": page,
        "categories": Categorie.objects.all(),
        "categorie": categorie,
        "recherche": recherche,
        "stock_bas": request.GET.get("stock") == "bas",
        "seuil_stock_bas": seuil,
    })


@magasin_requis
def produit_modifier(request, pk=None):
    produit = get_object_or_404(Produit, pk=pk) if pk else None
    form = ProduitForm(request.POST or None, request.FILES or None, instance=produit)
    if request.method == "POST" and form.is_valid():
        produit = form.save()
        messages.success(request, f"Pièce « {produit.nom} » enregistrée.")
        return redirect("gestion:produits")
    return render(request, "gestion/produit_form.html", {"form": form, "produit": produit})


@magasin_requis
def produit_supprimer(request, pk):
    """GET : page de confirmation. POST : suppression définitive (photo comprise).
    Les commandes passées gardent leur copie du nom, de la référence et du prix."""
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == "POST":
        nom = produit.nom
        if produit.photo:
            produit.photo.delete(save=False)
        produit.delete()
        messages.success(request, f"Pièce « {nom} » supprimée.")
        return redirect("gestion:produits")
    return render(request, "gestion/produit_supprimer.html", {
        "produit": produit,
        "nb_commandes": Commande.objects.filter(lignes__produit=produit).distinct().count(),
        "nb_en_attente": Commande.objects.filter(
            lignes__produit=produit, statut=Statut.EN_ATTENTE).distinct().count(),
    })


@magasin_requis
def clients(request):
    qs = (
        Utilisateur.objects.filter(groups__isnull=True, is_superuser=False)
        .annotate(nb_commandes=Count("commandes"))
        .order_by("nom", "prenom")
    )
    recherche = request.GET.get("q", "").strip()
    if recherche:
        qs = qs.filter(
            Q(nom__icontains=recherche) | Q(prenom__icontains=recherche)
            | Q(telephone__icontains=recherche.replace(" ", ""))
        )
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "gestion/clients.html", {"page": page, "recherche": recherche})


@magasin_requis
def client(request, pk):
    c = get_object_or_404(Utilisateur, pk=pk)
    return render(request, "gestion/client.html", {"client": c, "commandes": c.commandes.all()})
