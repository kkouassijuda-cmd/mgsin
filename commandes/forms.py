from django import forms

from comptes.telephone import normaliser_telephone

from .models import Mode, Paiement, PAIEMENTS_LIVRAISON


class CommandeForm(forms.Form):
    mode = forms.ChoiceField(label="Mode de réception", choices=Mode.choices, widget=forms.RadioSelect)
    prenom = forms.CharField(label="Prénom", max_length=100)
    nom = forms.CharField(label="Nom", max_length=100)
    telephone = forms.CharField(label="Téléphone", max_length=20, widget=forms.TextInput(attrs={"inputmode": "tel"}))
    adresse = forms.CharField(
        label="Adresse de livraison", required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Commune, quartier, repère…"}),
    )
    paiement = forms.ChoiceField(
        label="Paiement", required=False, widget=forms.RadioSelect,
        choices=[(p.value, p.label) for p in PAIEMENTS_LIVRAISON],
    )

    def clean_telephone(self):
        return normaliser_telephone(self.cleaned_data["telephone"])

    def clean(self):
        donnees = super().clean()
        if donnees.get("mode") == Mode.LIVRAISON:
            if not donnees.get("adresse", "").strip():
                self.add_error("adresse", "L'adresse est obligatoire pour une livraison.")
            if not donnees.get("paiement"):
                self.add_error("paiement", "Choisissez un moyen de paiement.")
        elif donnees.get("mode") == Mode.RETRAIT:
            donnees["adresse"] = ""
            donnees["paiement"] = Paiement.MAGASIN
        return donnees
