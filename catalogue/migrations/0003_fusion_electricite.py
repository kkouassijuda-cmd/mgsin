from django.db import migrations


def fusionner(apps, schema_editor):
    """« Électricité bâtiment » rejoint « Électricité » : ses produits y sont déplacés."""
    Categorie = apps.get_model("catalogue", "Categorie")
    Produit = apps.get_model("catalogue", "Produit")
    electricite, _ = Categorie.objects.get_or_create(
        slug="electricite", defaults={"nom": "Électricité", "ordre": 5})
    batiment = Categorie.objects.filter(slug="electricite-batiment").first()
    if batiment:
        Produit.objects.filter(categorie=batiment).update(categorie=electricite)
        batiment.delete()
    for ordre, categorie in enumerate(Categorie.objects.order_by("ordre", "nom"), start=1):
        if categorie.ordre != ordre:
            categorie.ordre = ordre
            categorie.save(update_fields=["ordre"])


class Migration(migrations.Migration):
    dependencies = [("catalogue", "0002_categories")]
    operations = [migrations.RunPython(fusionner, migrations.RunPython.noop)]
