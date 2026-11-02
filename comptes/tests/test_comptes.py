from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from comptes.models import Utilisateur
from comptes.telephone import normaliser_telephone


class NormalisationTelephoneTests(TestCase):
    def test_formats_equivalents(self):
        for saisie in ["0707070707", "07 07 07 07 07", "+225 07 07 07 07 07", "00225 0707070707",
                       "225 0707070707", "707070707"]:
            with self.subTest(saisie=saisie):
                self.assertEqual(normaliser_telephone(saisie), "0707070707")

    def test_numero_invalide(self):
        for saisie in ["", "123", "07070707070707"]:
            with self.subTest(saisie=saisie), self.assertRaises(ValidationError):
                normaliser_telephone(saisie)


class InscriptionConnexionTests(TestCase):
    def test_inscription_puis_connexion_avec_indicatif(self):
        r = self.client.post(reverse("comptes:inscription"), {
            "prenom": "Awa", "nom": "Koné", "telephone": "07 08 09 10 11",
            "adresse_habituelle": "", "password1": "Pi3ce-Solide!", "password2": "Pi3ce-Solide!",
        })
        self.assertRedirects(r, reverse("catalogue:accueil"))
        u = Utilisateur.objects.get()
        self.assertEqual(u.telephone, "0708091011")
        self.assertNotEqual(u.password, "Pi3ce-Solide!")
        self.assertTrue(u.password.startswith("argon2"))

        self.client.logout()
        r = self.client.post(reverse("comptes:connexion"), {"username": "+225 0708091011", "password": "Pi3ce-Solide!"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), u.pk)

    def test_numero_deja_utilise(self):
        Utilisateur.objects.create_user("0708091011", "x", nom="A", prenom="B")
        r = self.client.post(reverse("comptes:inscription"), {
            "prenom": "Awa", "nom": "Koné", "telephone": "+2250708091011",
            "password1": "Pi3ce-Solide!", "password2": "Pi3ce-Solide!",
        })
        self.assertContains(r, "Un compte existe déjà avec ce numéro.")

    def test_blocage_apres_echecs_repetes(self):
        Utilisateur.objects.create_user("0708091011", "Pi3ce-Solide!", nom="A", prenom="B")
        for _ in range(5):
            self.client.post(reverse("comptes:connexion"), {"username": "0708091011", "password": "faux"})
        r = self.client.post(reverse("comptes:connexion"), {"username": "0708091011", "password": "Pi3ce-Solide!"})
        self.assertEqual(r.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)
