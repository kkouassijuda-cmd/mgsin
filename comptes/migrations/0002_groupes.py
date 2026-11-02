from django.contrib.auth.management import create_permissions
from django.db import migrations

# Droits du groupe Magasin dans l'admin Django : catalogue et consultation des commandes et clients.
PERMISSIONS_MAGASIN = [
    ("catalogue", "add_produit"), ("catalogue", "change_produit"), ("catalogue", "view_produit"),
    ("catalogue", "view_categorie"),
    ("commandes", "view_commande"),
    ("comptes", "view_utilisateur"),
]


def creer(apps, schema_editor):
    for config in apps.get_app_configs():
        config.models_module = True
        create_permissions(config, apps=apps, verbosity=0)
        config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    magasin, _ = Group.objects.get_or_create(name="Magasin")
    Group.objects.get_or_create(name="Livreur")
    for app_label, codename in PERMISSIONS_MAGASIN:
        perm = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
        if perm:
            magasin.permissions.add(perm)


class Migration(migrations.Migration):
    dependencies = [
        ("comptes", "0001_initial"),
        ("catalogue", "0001_initial"),
        ("commandes", "0002_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [migrations.RunPython(creer, migrations.RunPython.noop)]
