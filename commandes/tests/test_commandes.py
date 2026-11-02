import re

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from catalogue.models import Categorie, Produit
from commandes.models import Commande, Mode, Paiement, Statut
from commandes.services import CommandeImpossible, annuler, avancer, creer_commande
from comptes.models import GROUPE_LIVREUR, GROUPE_MAGASIN, Utilisateur


class Base(TestCase):
    def setUp(self):
        self.cat = Categorie.objects.get(slug="moto")
        self.p1 = Produit.objects.create(ref="R1", nom="Chaîne", categorie=self.cat, prix_fcfa=15000, stock=5)
        self.p2 = Produit.objects.create(ref="R2", nom="Câble", categorie=self.cat, prix_fcfa=2500, stock=10)
        self.client_u = Utilisateur.objects.create_user("0701010101", "Pi3ce-Solide!", nom="Koné", prenom="Awa")
        self.magasin = Utilisateur.objects.create_user("0702020202", "Pi3ce-Solide!", nom="Gérant", prenom="Paul")
        self.magasin.groups.add(Group.objects.get(name=GROUPE_MAGASIN))
        self.livreur = Utilisateur.objects.create_user("0703030303", "Pi3ce-Solide!", nom="Livreur", prenom="Koffi")
        self.livreur.groups.add(Group.objects.get(name=GROUPE_LIVREUR))

    def commande(self, mode=Mode.RETRAIT, articles=None, **kw):
        infos = {"prenom": "Awa", "nom": "Koné", "telephone": "0701010101"}
        if mode == Mode.LIVRAISON:
            infos.update(adresse="Cocody", paiement=Paiement.ESPECES)
        infos.update(kw)
        return creer_commande(self.client_u, articles or [(self.p1.pk, 2), (self.p2.pk, 3)], mode=mode, **infos)

    def stocks(self):
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        return self.p1.stock, self.p2.stock


class CreationTests(Base):
    def test_numero_total_et_copie_des_lignes(self):
        c = self.commande()
        self.assertRegex(c.numero, r"^CMD-\d{6}-[A-Z0-9]{4}$")
        self.assertEqual(c.total_fcfa, 2 * 15000 + 3 * 2500)
        self.assertEqual(c.statut, Statut.EN_ATTENTE)
        self.assertEqual(c.paiement, Paiement.MAGASIN)
        self.assertEqual(self.stocks(), (5, 10), "le stock ne baisse pas à la création")
        self.assertEqual(c.historique.count(), 1)

        self.p1.prix_fcfa = 99999
        self.p1.save()
        ligne = c.lignes.get(produit=self.p1)
        self.assertEqual(ligne.prix_unitaire, 15000)
        self.assertEqual(ligne.nom, "Chaîne")

    def test_numeros_uniques(self):
        numeros = {self.commande(articles=[(self.p2.pk, 1)]).numero for _ in range(5)}
        self.assertEqual(len(numeros), 5)

    def test_stock_insuffisant(self):
        with self.assertRaises(CommandeImpossible):
            self.commande(articles=[(self.p1.pk, 6)])
        self.assertEqual(Commande.objects.count(), 0)

    def test_livraison_sans_adresse(self):
        with self.assertRaises(CommandeImpossible):
            self.commande(Mode.LIVRAISON, adresse="  ")


class ParcoursTests(Base):
    def test_parcours_retrait_complet(self):
        c = self.commande()
        self.assertTrue(c.recu_disponible, "reçu disponible dès la commande pour un retrait")
        attendus = [Statut.VALIDEE, Statut.PREPARATION, Statut.PRETE, Statut.RETIREE]
        for statut in attendus:
            c = avancer(c, self.magasin)
            self.assertEqual(c.statut, statut)
            if statut == Statut.VALIDEE:
                self.assertEqual(self.stocks(), (3, 7), "stock déduit à la validation")
        self.assertTrue(c.encaisse)
        self.assertTrue(c.est_terminee)
        self.assertEqual(list(c.historique.values_list("statut", flat=True)), [Statut.EN_ATTENTE, *attendus])
        with self.assertRaises(CommandeImpossible):
            avancer(c, self.magasin)
        self.assertEqual(self.stocks(), (3, 7))

    def test_parcours_livraison_complet(self):
        c = self.commande(Mode.LIVRAISON)
        self.assertFalse(c.recu_disponible, "reçu après vérification seulement")
        c = avancer(c, self.magasin)
        self.assertEqual(c.statut, Statut.VERIFIEE)
        self.assertTrue(c.recu_disponible)
        self.assertEqual(self.stocks(), (3, 7))
        c = avancer(c, self.magasin)
        with self.assertRaises(CommandeImpossible):
            avancer(c, self.magasin)  # livreur obligatoire
        with self.assertRaises(CommandeImpossible):
            avancer(c, self.magasin, livreur=self.client_u)  # pas un livreur
        c = avancer(c, self.magasin, livreur=self.livreur)
        self.assertEqual((c.statut, c.livreur), (Statut.LIVRAISON, self.livreur))
        with self.assertRaises(CommandeImpossible):
            avancer(c, self.livreur, encaisse=False)  # espèces non encaissées
        c = avancer(c, self.livreur, encaisse=True)
        self.assertEqual(c.statut, Statut.LIVREE)
        self.assertTrue(c.encaisse)

    def test_stock_epuise_entre_commande_et_validation(self):
        c = self.commande(articles=[(self.p1.pk, 4)])
        Produit.objects.filter(pk=self.p1.pk).update(stock=3)
        with self.assertRaises(CommandeImpossible):
            avancer(c, self.magasin)
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.EN_ATTENTE)
        self.assertEqual(self.stocks()[0], 3)


class AnnulationTests(Base):
    def test_annulation_avant_deduction(self):
        c = annuler(self.commande(), self.magasin, "Client injoignable")
        self.assertEqual(c.statut, Statut.ANNULEE)
        self.assertEqual(self.stocks(), (5, 10))
        self.assertFalse(c.recu_disponible)

    def test_annulation_remet_le_stock(self):
        c = avancer(avancer(self.commande(), self.magasin), self.magasin)
        self.assertEqual(self.stocks(), (3, 7))
        c = annuler(c, self.magasin, "Pièce défectueuse")
        self.assertEqual(self.stocks(), (5, 10))
        self.assertEqual(c.motif_annulation, "Pièce défectueuse")
        self.assertEqual(c.historique.last().statut, Statut.ANNULEE)

    def test_motif_obligatoire_et_derniere_etape(self):
        c = self.commande()
        with self.assertRaises(CommandeImpossible):
            annuler(c, self.magasin, "")
        for _ in range(4):
            c = avancer(c, self.magasin)
        with self.assertRaises(CommandeImpossible):
            annuler(c, self.magasin, "trop tard")
        with self.assertRaises(CommandeImpossible):
            annuler(annuler(self.commande(articles=[(self.p2.pk, 1)]), self.magasin, "x"), self.magasin, "encore")


class AccesTests(Base):
    def test_client_ne_voit_que_ses_commandes(self):
        c = self.commande()
        autre = Utilisateur.objects.create_user("0704040404", "Pi3ce-Solide!", nom="X", prenom="Y")
        self.client.force_login(autre)
        self.assertEqual(self.client.get(reverse("commandes:detail", args=[c.numero])).status_code, 404)
        self.assertEqual(self.client.get(reverse("commandes:recu", args=[c.numero])).status_code, 404)
        self.client.force_login(self.client_u)
        self.assertContains(self.client.get(reverse("commandes:detail", args=[c.numero])), c.numero)

    def test_gestion_reservee_au_magasin(self):
        url = reverse("gestion:tableau_de_bord")
        self.assertEqual(self.client.get(url).status_code, 302)
        for u in (self.client_u, self.livreur):
            self.client.force_login(u)
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.magasin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_livreur_ne_voit_que_ses_livraisons(self):
        a_lui = avancer(avancer(avancer(self.commande(Mode.LIVRAISON), self.magasin), self.magasin), self.magasin, livreur=self.livreur)
        pas_encore = self.commande(Mode.LIVRAISON, articles=[(self.p2.pk, 1)])
        self.client.force_login(self.livreur)
        r = self.client.get(reverse("livraison:liste"))
        self.assertContains(r, a_lui.numero)
        self.assertNotContains(r, pas_encore.numero)
        self.assertEqual(self.client.get(reverse("livraison:detail", args=[pas_encore.numero])).status_code, 404)
        self.client.force_login(self.client_u)
        self.assertEqual(self.client.get(reverse("livraison:liste")).status_code, 403)


class EspaceClientTests(Base):
    """Le client ne touche jamais à la gestion ; il suit ses commandes et récupère son reçu."""

    def test_client_bloque_hors_de_son_espace(self):
        c = self.commande()
        self.client.force_login(self.client_u)
        for url in [
            reverse("gestion:tableau_de_bord"), reverse("gestion:commande", args=[c.numero]),
            reverse("gestion:produits"), reverse("gestion:clients"), reverse("livraison:liste"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        for url, donnees in [
            (reverse("gestion:commande_avancer", args=[c.numero]), {}),
            (reverse("gestion:commande_annuler", args=[c.numero]), {"motif": "x"}),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, donnees).status_code, 403)
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.EN_ATTENTE)

        r = self.client.get(reverse("admin:index"))
        self.assertRedirects(r, reverse("admin:login") + "?next=" + reverse("admin:index"))
        r = self.client.get(reverse("catalogue:accueil"))
        self.assertNotContains(r, reverse("gestion:tableau_de_bord"))
        self.assertNotContains(r, reverse("admin:index"))

    def test_suivi_temps_reel_et_recu(self):
        c = self.commande(Mode.LIVRAISON)
        self.client.force_login(self.client_u)
        url_etat = reverse("commandes:etat", args=[c.numero])

        r = self.client.get(url_etat)
        self.assertContains(r, "le magasin va la vérifier")
        self.assertNotContains(r, "Télécharger mon reçu")
        self.assertEqual(r["Cache-Control"], "no-store")

        etapes = [
            ({}, "Votre reçu est disponible"),
            ({}, "en cours de préparation"),
            ({"livreur": self.livreur}, "en cours de livraison"),
        ]
        for options, message in etapes:
            c = avancer(c, self.magasin, **options)
            r = self.client.get(url_etat)
            with self.subTest(statut=c.statut):
                self.assertContains(r, message)
                self.assertContains(r, "Télécharger mon reçu")
        self.assertContains(self.client.get(reverse("commandes:mes_commandes_etat")), "en cours de livraison")

        r = self.client.get(reverse("commandes:recu", args=[c.numero]))
        self.assertEqual(r["Content-Type"], "application/pdf")

        autre = Utilisateur.objects.create_user("0705050505", "Pi3ce-Solide!", nom="X", prenom="Y")
        self.client.force_login(autre)
        self.assertEqual(self.client.get(url_etat).status_code, 404)
        self.assertNotContains(self.client.get(reverse("commandes:mes_commandes_etat")), c.numero)

    def test_recu_contient_les_lignes_et_le_total(self):
        from reportlab import rl_config
        from commandes.recu import generer_recu

        c = avancer(self.commande(Mode.LIVRAISON), self.magasin)
        compression = rl_config.pageCompression
        rl_config.pageCompression = 0  # texte lisible dans le PDF
        try:
            pdf = generer_recu(c)
        finally:
            rl_config.pageCompression = compression

        # Texte affiché : chaînes « (…) Tj », avec les accents en octal (\351 = é).
        morceaux = re.findall(rb"\(((?:\\.|[^\\)])*)\) Tj", pdf)
        texte = " ".join(
            re.sub(r"\\([0-7]{3}|.)", lambda m: chr(int(m.group(1), 8)) if len(m.group(1)) == 3 else m.group(1),
                   m.decode("latin-1"))
            for m in morceaux
        )
        texte = texte.replace(" ", " ")
        self.assertNotIn(" ", texte, "l'espace fine n'existe pas dans la police du PDF")
        for attendu in [c.numero, "Awa Koné", "0701010101", "Cocody", "Espèces à la livraison",
                        "Chaîne", "Câble", "15 000 FCFA", "30 000 FCFA", "2 500 FCFA",
                        "7 500 FCFA", "TOTAL", "37 500 FCFA"]:
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, texte)


class NavigationTests(Base):
    def test_boutique_sans_lien_gestion_quel_que_soit_le_role(self):
        admin = Utilisateur.objects.create_superuser("0706060606", "Pi3ce-Solide!", nom="Admin", prenom="Chef")
        for u in (self.client_u, self.magasin, self.livreur, admin):
            self.client.force_login(u)
            r = self.client.get(reverse("catalogue:accueil"))
            with self.subTest(utilisateur=u.telephone):
                self.assertNotContains(r, reverse("gestion:tableau_de_bord"))
                self.assertNotContains(r, reverse("livraison:liste"))
                self.assertNotContains(r, reverse("admin:index"))

    def test_connexion_mene_a_l_espace_du_role(self):
        admin = Utilisateur.objects.create_superuser("0706060606", "Pi3ce-Solide!", nom="Admin", prenom="Chef")
        attendus = [
            (self.client_u, reverse("catalogue:accueil")),
            (self.magasin, reverse("gestion:tableau_de_bord")),
            (admin, reverse("gestion:tableau_de_bord")),
            (self.livreur, reverse("livraison:liste")),
        ]
        for u, page in attendus:
            self.client.logout()
            r = self.client.post(reverse("comptes:connexion"), {"username": u.telephone, "password": "Pi3ce-Solide!"})
            with self.subTest(utilisateur=u.telephone):
                self.assertRedirects(r, page, fetch_redirect_response=False)
        self.client.logout()
        r = self.client.post(reverse("comptes:connexion") + "?next=/commandes/",
                             {"username": self.magasin.telephone, "password": "Pi3ce-Solide!", "next": "/commandes/"})
        self.assertRedirects(r, "/commandes/", fetch_redirect_response=False)


class ParcoursWebTests(Base):
    """Parcours complet par les pages, comme un vrai client, le magasin et le livreur."""

    def test_livraison_de_bout_en_bout(self):
        self.client.post(reverse("commandes:panier_ajouter", args=[self.p1.pk]), {"quantite": 2})
        self.client.post(reverse("commandes:panier_ajouter", args=[self.p2.pk]), {"quantite": 50})
        r = self.client.get(reverse("commandes:commander"))
        self.assertRedirects(r, reverse("comptes:connexion") + "?next=" + reverse("commandes:commander"))

        self.client.post(reverse("comptes:connexion"), {"username": "+225 07 01 01 01 01", "password": "Pi3ce-Solide!"})
        r = self.client.post(reverse("commandes:commander"), {
            "mode": "livraison", "prenom": "Awa", "nom": "Koné", "telephone": "0701010101",
            "adresse": "Yopougon, Sideci", "paiement": "wave",
        }, follow=True)
        c = Commande.objects.get()
        self.assertContains(r, c.numero)
        self.assertEqual(c.total_fcfa, 2 * 15000 + 10 * 2500, "quantité plafonnée au stock")
        self.assertEqual(len(self.client.session["panier"]), 0)
        self.assertEqual(self.client.get(reverse("commandes:recu", args=[c.numero])).status_code, 302)

        self.client.force_login(self.magasin)
        url_avancer = reverse("gestion:commande_avancer", args=[c.numero])
        self.client.post(url_avancer)
        self.client.post(url_avancer)
        self.client.post(url_avancer, {"livreur": self.livreur.pk})
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.LIVRAISON)
        self.client.post(url_avancer)  # le magasin ne peut pas confirmer à la place du livreur
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.LIVRAISON)

        self.client.force_login(self.livreur)
        self.client.post(reverse("livraison:confirmer", args=[c.numero]), {"encaisse": "on"})
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.LIVREE)

        self.client.force_login(self.client_u)
        r = self.client.get(reverse("commandes:recu", args=[c.numero]))
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_annulation_depuis_gestion(self):
        c = self.commande()
        self.client.force_login(self.magasin)
        self.client.post(reverse("gestion:commande_annuler", args=[c.numero]), {"motif": ""})
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.EN_ATTENTE)
        self.client.post(reverse("gestion:commande_annuler", args=[c.numero]), {"motif": "Rupture fournisseur"})
        self.client.force_login(self.client_u)
        self.assertContains(self.client.get(reverse("commandes:detail", args=[c.numero])), "Rupture fournisseur")

    def test_pages_principales(self):
        c = self.commande()
        self.client.force_login(self.magasin)
        for url in [
            reverse("catalogue:accueil"), reverse("catalogue:accueil") + "?q=chaîne",
            reverse("catalogue:categorie", args=["moto"]), reverse("catalogue:produit", args=[self.p1.pk]),
            reverse("commandes:panier"), reverse("gestion:commande", args=[c.numero]),
            reverse("gestion:produits"), reverse("gestion:produit_ajouter"),
            reverse("gestion:produit_modifier", args=[self.p1.pk]), reverse("gestion:clients"),
            reverse("gestion:client", args=[self.client_u.pk]), reverse("comptes:profil"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class SuppressionProduitTests(Base):
    def url(self, produit):
        return reverse("gestion:produit_supprimer", args=[produit.pk])

    def test_bouton_dans_la_liste_et_confirmation(self):
        self.client.force_login(self.magasin)
        liste = self.client.get(reverse("gestion:produits")).content.decode()
        self.assertIn(self.url(self.p1), liste)
        self.assertEqual(self.client.get(self.url(self.p1)).status_code, 200)
        self.assertTrue(Produit.objects.filter(pk=self.p1.pk).exists(), "GET ne supprime rien")

    def test_piece_deja_commandee_supprimee_commande_intacte(self):
        c = self.commande()
        avancer(c, self.magasin)
        self.client.force_login(self.magasin)
        r = self.client.post(self.url(self.p1))
        self.assertRedirects(r, reverse("gestion:produits"))
        self.assertFalse(Produit.objects.filter(pk=self.p1.pk).exists())
        ligne = c.lignes.get(ref="R1")
        self.assertIsNone(ligne.produit)
        self.assertEqual((ligne.nom, ligne.prix_unitaire), ("Chaîne", 15000))
        self.client.force_login(self.client_u)
        recu = self.client.get(reverse("commandes:recu", args=[c.numero]))
        self.assertEqual(recu.status_code, 200)

    def test_commande_en_attente_avec_piece_supprimee(self):
        c = self.commande()
        self.p1.delete()
        c.refresh_from_db()
        with self.assertRaisesMessage(CommandeImpossible, "Pièce supprimée du catalogue"):
            avancer(c, self.magasin)
        annuler(c, self.magasin, "Pièce retirée du catalogue")
        c.refresh_from_db()
        self.assertEqual(c.statut, Statut.ANNULEE)

    def test_client_ne_peut_pas_supprimer(self):
        self.client.force_login(self.client_u)
        self.assertEqual(self.client.post(self.url(self.p1)).status_code, 403)
        self.assertTrue(Produit.objects.filter(pk=self.p1.pk).exists())


class SeuilStockBasTests(Base):
    """p1 a 5 en stock, p2 en a 10 : le seuil choisi décide qui est « stock bas »."""

    def pieces_en_stock_bas(self, **params):
        r = self.client.get(reverse("gestion:produits"), {"stock": "bas", **params})
        return {p.ref for p in r.context["page"].object_list}

    def test_seuil_modifiable_et_memorise(self):
        self.client.force_login(self.magasin)
        self.assertEqual(self.pieces_en_stock_bas(), set(), "seuil par défaut : 3")
        self.assertEqual(self.pieces_en_stock_bas(seuil="5"), {"R1"})
        self.assertEqual(self.pieces_en_stock_bas(), {"R1"}, "le seuil choisi est retenu")
        self.assertEqual(self.pieces_en_stock_bas(seuil="10"), {"R1", "R2"})
        tableau = self.client.get(reverse("gestion:tableau_de_bord"))
        self.assertEqual(tableau.context["stock_bas"], 2, "l'alerte du tableau de bord suit le seuil")

    def test_valeur_invalide_ignoree(self):
        self.client.force_login(self.magasin)
        self.assertEqual(self.pieces_en_stock_bas(seuil="-4"), set())
        self.assertEqual(self.pieces_en_stock_bas(seuil="abc"), set())


class SecuriteEspacesPersonnelTests(Base):
    """Taper l'adresse de Gestion, Livraison ou de l'admin ne donne rien sans le bon rôle."""

    def urls(self):
        return [
            "/gestion/", "/gestion/pieces/", "/gestion/pieces/ajouter/",
            f"/gestion/pieces/{self.p1.pk}/", f"/gestion/pieces/{self.p1.pk}/supprimer/",
            "/gestion/clients/", "/livraison/", "/admin/",
        ]

    def test_visiteur_renvoye_vers_la_connexion(self):
        for url in self.urls():
            with self.subTest(url=url):
                for r in (self.client.get(url), self.client.post(url)):
                    self.assertEqual(r.status_code, 302)
                    self.assertIn("connexion" if not url.startswith("/admin/") else "/admin/login/", r["Location"])

    def test_client_refuse_et_rien_n_est_modifie(self):
        self.client.force_login(self.client_u)
        for url in self.urls():
            with self.subTest(url=url):
                attendu = 302 if url.startswith("/admin/") else 403
                self.assertEqual(self.client.get(url).status_code, attendu)
                self.assertEqual(self.client.post(url).status_code, attendu)
        self.assertTrue(Produit.objects.filter(pk=self.p1.pk).exists())

    def test_connexion_du_personnel_sans_creation_de_compte(self):
        inscription = reverse("comptes:inscription")
        for url in ("/gestion/", "/livraison/"):
            with self.subTest(url=url):
                page = self.client.get(url, follow=True).content.decode()
                self.assertIn("Espace personnel", page)
                self.assertNotIn(inscription, page)
        page = self.client.get(reverse("comptes:connexion")).content.decode()
        self.assertIn(inscription, page, "la connexion des clients garde « Créer un compte »")


class AucunStyleDansLeHtmlTests(TestCase):
    """Règle du projet : le CSS reste dans static/css, jamais dans les templates."""

    def test_templates_sans_style(self):
        from pathlib import Path
        from django.conf import settings
        for fichier in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            texte = fichier.read_text(encoding="utf-8")
            with self.subTest(fichier=fichier.name):
                self.assertNotRegex(texte, r"style\s*=|<style|<script>(?!</script>)")
                self.assertIsNone(re.search(r"<script(?![^>]*\bsrc=)", texte))
