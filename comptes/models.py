from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .telephone import normaliser_telephone

GROUPE_MAGASIN = "Magasin"
GROUPE_LIVREUR = "Livreur"


class UtilisateurManager(BaseUserManager):
    use_in_migrations = True

    def _creer(self, telephone, password, **champs):
        if not telephone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        utilisateur = self.model(telephone=normaliser_telephone(telephone), **champs)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_user(self, telephone, password=None, **champs):
        champs.setdefault("is_staff", False)
        champs.setdefault("is_superuser", False)
        return self._creer(telephone, password, **champs)

    def create_superuser(self, telephone, password=None, **champs):
        champs["is_staff"] = True
        champs["is_superuser"] = True
        return self._creer(telephone, password, **champs)

    def get_by_natural_key(self, telephone):
        try:
            telephone = normaliser_telephone(telephone)
        except Exception:
            pass
        return self.get(telephone=telephone)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """Compte du site : client, personnel du magasin, livreur ou administrateur.

    Le rôle vient des groupes Django (« Magasin », « Livreur ») ; un compte
    sans groupe est un client.
    """

    telephone = models.CharField("téléphone", max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField("prénom", max_length=100)
    adresse_habituelle = models.TextField("adresse habituelle", blank=True)
    date_inscription = models.DateTimeField("date d'inscription", default=timezone.now)
    is_active = models.BooleanField("actif", default=True)
    is_staff = models.BooleanField("accès à l'administration", default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = "telephone"
    REQUIRED_FIELDS = ["nom", "prenom"]

    class Meta:
        verbose_name = "utilisateur"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.telephone_affiche})"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    def get_short_name(self):
        return self.prenom

    @property
    def telephone_affiche(self):
        t = self.telephone
        return " ".join(t[i:i + 2] for i in range(0, len(t), 2))

    def _dans_groupe(self, nom):
        return self.groups.filter(name=nom).exists()

    @property
    def est_magasin(self):
        return self.is_superuser or self._dans_groupe(GROUPE_MAGASIN)

    @property
    def est_livreur(self):
        return self._dans_groupe(GROUPE_LIVREUR)
