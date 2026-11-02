from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from .forms import ConnexionForm, InscriptionForm, ProfilForm

ESPACES_PERSONNEL = ("/gestion/", "/livraison/")


def inscription(request):
    if request.user.is_authenticated:
        return redirect("catalogue:accueil")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        login(request, utilisateur, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Votre compte a été créé. Bienvenue !")
        return redirect(request.GET.get("next") or "catalogue:accueil")
    return render(request, "comptes/inscription.html", {"form": form})


def accueil_selon_role(utilisateur):
    """Page d'arrivée après connexion : chacun va dans son espace."""
    if utilisateur.est_magasin:
        return reverse("gestion:tableau_de_bord")
    if utilisateur.est_livreur:
        return reverse("livraison:liste")
    return reverse("catalogue:accueil")


class ConnexionView(auth_views.LoginView):
    template_name = "comptes/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        # Utilisée seulement quand aucune page « next » n'est demandée.
        return accueil_selon_role(self.request.user)

    def get_context_data(self, **kwargs):
        # Connexion demandée pour Gestion ou Livraison : page réservée au personnel,
        # sans proposer de créer un compte (les comptes du personnel sont créés par l'admin).
        contexte = super().get_context_data(**kwargs)
        suivant = self.request.POST.get("next") or self.request.GET.get("next") or ""
        contexte["espace_personnel"] = suivant.startswith(ESPACES_PERSONNEL)
        return contexte


class DeconnexionView(auth_views.LogoutView):
    pass


class MotDePasseView(auth_views.PasswordChangeView):
    template_name = "comptes/mot_de_passe.html"
    success_url = reverse_lazy("comptes:profil")

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe modifié.")
        return super().form_valid(form)


@login_required
def profil(request):
    form = ProfilForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vos informations ont été enregistrées.")
        return redirect("comptes:profil")
    return render(request, "comptes/profil.html", {"form": form})
