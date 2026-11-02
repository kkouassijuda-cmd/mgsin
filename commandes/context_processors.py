from .panier import Panier


def panier(request):
    return {"nombre_articles_panier": len(Panier(request))}
