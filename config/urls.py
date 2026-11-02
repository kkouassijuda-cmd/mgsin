from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "TechnoPièces · Administration"
admin.site.site_title = "TechnoPièces"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("compte/", include("comptes.urls")),
    path("commandes/", include("commandes.urls")),
    path("gestion/", include("gestion.urls")),
    path("livraison/", include("livraison.urls")),
    path("", include("catalogue.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
