from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Utilisateur


class UtilisateurChangeForm(UserChangeForm):
    class Meta:
        model = Utilisateur
        fields = "__all__"


class UtilisateurCreationForm(AdminUserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ("telephone", "prenom", "nom")


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    form = UtilisateurChangeForm
    add_form = UtilisateurCreationForm
    list_display = ("telephone", "prenom", "nom", "is_active", "is_staff", "date_inscription")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("telephone", "nom", "prenom")
    ordering = ("nom", "prenom")
    fieldsets = (
        (None, {"fields": ("telephone", "password")}),
        ("Informations", {"fields": ("prenom", "nom", "adresse_habituelle")}),
        ("Rôles et droits", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_inscription")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("telephone", "prenom", "nom", "password1", "password2")}),
    )
