import io
import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from catalogue.donnees.catalogue import PIECES
from catalogue.models import Produit

MEDIA_TEST = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class ChargerCatalogueTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def test_toutes_les_pieces_avec_photo_et_sans_doublon(self):
        attendu = sum(len(p) for p in PIECES.values())
        call_command("charger_catalogue", stdout=io.StringIO())
        call_command("charger_catalogue", stdout=io.StringIO())
        self.assertEqual(Produit.objects.count(), attendu)
        self.assertEqual(Produit.objects.filter(photo="").count(), 0, "chaque pièce a sa photo")
        page = self.client.get("/").content.decode()
        self.assertIn("/media/produits/", page)
