from django import forms

from catalogue.models import Produit
from comptes.models import GROUPE_LIVREUR, Utilisateur


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ("ref", "nom", "categorie", "caracteristiques", "prix_fcfa", "stock", "en_vente", "photo")
        widgets = {"caracteristiques": forms.Textarea(attrs={"rows": 4})}


class LivreurForm(forms.Form):
    livreur = forms.ModelChoiceField(
        label="Livreur", queryset=Utilisateur.objects.none(), empty_label="Choisir un livreur…"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["livreur"].queryset = Utilisateur.objects.filter(groups__name=GROUPE_LIVREUR, is_active=True)


class AnnulationForm(forms.Form):
    motif = forms.CharField(
        label="Motif de l'annulation (visible par le client)",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
