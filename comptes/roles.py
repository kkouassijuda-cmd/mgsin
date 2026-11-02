from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


def _role_requis(test):
    def decorateur(vue):
        @wraps(vue)
        @login_required
        def enveloppe(request, *args, **kwargs):
            if not test(request.user):
                raise PermissionDenied
            return vue(request, *args, **kwargs)
        return enveloppe
    return decorateur


magasin_requis = _role_requis(lambda u: u.est_magasin)
livreur_requis = _role_requis(lambda u: u.est_livreur)
