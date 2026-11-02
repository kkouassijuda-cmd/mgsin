from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError

from .models import Utilisateur
from .telephone import normaliser_telephone


class ChampTelephoneMixin:
    def clean_telephone(self):
        telephone = normaliser_telephone(self.cleaned_data["telephone"])
        existants = Utilisateur.objects.filter(telephone=telephone)
        if self.instance.pk:
            existants = existants.exclude(pk=self.instance.pk)
        if existants.exists():
            raise ValidationError("Un compte existe déjà avec ce numéro.")
        return telephone


class InscriptionForm(ChampTelephoneMixin, BaseUserCreationForm):
    telephone = forms.CharField(
        label="Téléphone", max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "07 07 07 07 07"}),
    )

    class Meta:
        model = Utilisateur
        fields = ("prenom", "nom", "telephone", "adresse_habituelle")
        widgets = {"adresse_habituelle": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"adresse_habituelle": "Facultatif : proposée par défaut pour les livraisons."}


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        label="Téléphone", max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "autofocus": True}),
    )

    error_messages = {
        "invalid_login": "Numéro de téléphone ou mot de passe incorrect.",
        "inactive": "Ce compte est désactivé.",
    }

    def clean_username(self):
        brut = self.cleaned_data["username"]
        try:
            return normaliser_telephone(brut)
        except ValidationError:
            return brut


class ProfilForm(ChampTelephoneMixin, forms.ModelForm):
    telephone = forms.CharField(
        label="Téléphone", max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
    )

    class Meta:
        model = Utilisateur
        fields = ("prenom", "nom", "telephone", "adresse_habituelle")
        widgets = {"adresse_habituelle": forms.Textarea(attrs={"rows": 3})}
