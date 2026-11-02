from django import template

register = template.Library()


def formater_fcfa(montant):
    """12500 -> « 12 500 FCFA » (prix sans décimales)."""
    return f"{int(montant or 0):,}".replace(",", "\u202f") + " FCFA"


@register.filter
def fcfa(montant):
    return formater_fcfa(montant)
