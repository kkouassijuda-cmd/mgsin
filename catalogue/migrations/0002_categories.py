from django.db import migrations

CATEGORIES = [
    ("Mécanique", "mecanique"),
    ("Automobile", "automobile"),
    ("Moto", "moto"),
    ("Électronique", "electronique"),
    ("Électricité", "electricite"),
    ("Électricité bâtiment", "electricite-batiment"),
    ("Automatisme industriel", "automatisme-industriel"),
]


def creer(apps, schema_editor):
    Categorie = apps.get_model("catalogue", "Categorie")
    for ordre, (nom, slug) in enumerate(CATEGORIES, start=1):
        Categorie.objects.get_or_create(slug=slug, defaults={"nom": nom, "ordre": ordre})


class Migration(migrations.Migration):
    dependencies = [("catalogue", "0001_initial")]
    operations = [migrations.RunPython(creer, migrations.RunPython.noop)]
