"""{% statique 'css/base.css' %} : comme {% static %}, avec un numéro de version.

Le numéro est la date de modification du fichier : dès qu'un CSS ou un JS change,
son adresse change et le navigateur recharge la nouvelle version au lieu de garder
l'ancienne en cache.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def statique(chemin):
    url = static(chemin)
    fichier = finders.find(chemin)
    if fichier and os.path.exists(fichier):
        url += f"?v={int(os.path.getmtime(fichier))}"
    return url
