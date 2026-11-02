def roles(request):
    u = request.user
    connecte = u.is_authenticated
    return {
        "est_magasin": connecte and u.est_magasin,
        "est_livreur": connecte and u.est_livreur,
    }
