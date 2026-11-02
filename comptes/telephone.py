import re

from django.core.exceptions import ValidationError

INDICATIF = "225"


def normaliser_telephone(valeur):
    """Ramène un numéro ivoirien à 10 chiffres commençant par 0.

    « +225 07 07 07 07 07 », « 00225 0707070707 », « 0707070707 » et
    « 707070707 » donnent tous « 0707070707 ».
    """
    chiffres = re.sub(r"\D", "", valeur or "")
    if chiffres.startswith("00" + INDICATIF):
        chiffres = chiffres[2 + len(INDICATIF):]
    elif chiffres.startswith(INDICATIF) and len(chiffres) > 10:
        chiffres = chiffres[len(INDICATIF):]
    if chiffres and not chiffres.startswith("0"):
        chiffres = "0" + chiffres
    if len(chiffres) != 10:
        raise ValidationError("Numéro de téléphone invalide : 10 chiffres attendus (ex. 07 07 07 07 07).")
    return chiffres


def identifiant_axes(request, credentials):
    """Pour django-axes : compte les essais sur le numéro normalisé."""
    brut = (credentials or {}).get("username") or request.POST.get("username", "")
    try:
        return normaliser_telephone(brut)
    except ValidationError:
        return brut
