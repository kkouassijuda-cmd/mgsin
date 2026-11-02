from django.conf import settings


def magasin(request):
    return {
        "MAGASIN": settings.MAGASIN,
        "RAFRAICHISSEMENT_SECONDES": settings.RAFRAICHISSEMENT_SECONDES,
        "SUIVI_CLIENT_SECONDES": settings.SUIVI_CLIENT_SECONDES,
    }
