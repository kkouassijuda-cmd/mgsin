"""
Réglages du projet TechnoPièces.

Les secrets et les réglages propres à chaque machine sont lus dans le fichier
.env (voir .env.example). Ce fichier ne doit jamais être envoyé sur GitHub.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(nom, defaut=False):
    return os.getenv(nom, str(defaut)).strip().lower() in ("1", "true", "oui", "yes")


SECRET_KEY = os.getenv("SECRET_KEY", "")
DEBUG = env_bool("DEBUG", False)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "cle-de-developpement-uniquement"
    else:
        raise RuntimeError("SECRET_KEY doit être défini dans le fichier .env")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]


# Applications

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "axes",
    "comptes",
    "catalogue",
    "commandes",
    "gestion",
    "livraison",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Doit rester en dernier : bloque les tentatives de connexion répétées.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "comptes.context_processors.roles",
                "commandes.context_processors.panier",
                "config.context_processors.magasin",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base de données : PostgreSQL. DB_ENGINE=sqlite permet de dépanner en local
# quand PostgreSQL n'est pas disponible.

if os.getenv("DB_ENGINE", "postgresql") == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "comptoir"),
            "USER": os.getenv("DB_USER", "comptoir"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Comptes et mots de passe

AUTH_USER_MODEL = "comptes.Utilisateur"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "comptes:connexion"
LOGIN_REDIRECT_URL = "catalogue:accueil"
LOGOUT_REDIRECT_URL = "catalogue:accueil"

# django-axes : 5 essais ratés bloquent le couple (numéro, adresse IP) pendant 30 minutes.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.5
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = "comptes/bloque.html"
AXES_USERNAME_CALLABLE = "comptes.telephone.identifiant_axes"


# Langue et heure

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True


# Fichiers statiques (CSS, JavaScript) et photos des pièces

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# Informations du magasin (affichées sur le site et sur les reçus ; masquées si vides)

MAGASIN = {
    "nom": os.getenv("MAGASIN_NOM") or "TechnoPièces",
    "adresse": os.getenv("MAGASIN_ADRESSE", ""),
    "telephone": os.getenv("MAGASIN_TELEPHONE", ""),
    "horaires": os.getenv("MAGASIN_HORAIRES", ""),
}

# Délai (en secondes) entre deux rafraîchissements des pages de suivi.
RAFRAICHISSEMENT_SECONDES = int(os.getenv("RAFRAICHISSEMENT_SECONDES", "30"))

# Délai (en secondes) entre deux vérifications du suivi en temps réel côté client.
SUIVI_CLIENT_SECONDES = int(os.getenv("SUIVI_CLIENT_SECONDES", "10"))

# Seuil « stock bas » proposé par défaut dans Gestion (modifiable ensuite depuis la page Pièces).
STOCK_SEUIL_BAS = int(os.getenv("STOCK_SEUIL_BAS", "3"))


# Sécurité en production (DEBUG=False)

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
