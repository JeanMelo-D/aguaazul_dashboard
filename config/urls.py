from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic.base import RedirectView  # 1. Importe a RedirectView


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='data:index'), name='home-redirect'),
    path("admin/", admin.site.urls),
    path("data/", include("data.urls")),
    path('pipeline/', include('pipeline.urls', namespace='pipeline')),
    
    
]
