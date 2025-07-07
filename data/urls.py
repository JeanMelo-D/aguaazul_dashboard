from . import views
from django.urls import path
from .views import ColheitaFilteredView, FilterOptionsView, ContratosFilteredView, ContratosFilterOptionsView,MapaTalhaoAPIView,ListaTalhoesAPIView

urlpatterns = [
    # Rotas de páginas (não são API, então não seguem a regra do 'api/')
    path("", views.home, name='home'),
    path("maps/", views.maps, name='maps'),
    
     
    # APIs de Colheita
    path('api/colheita-data/', ColheitaFilteredView.as_view(), name='colheita_api'),
    path('api/filter-options/', FilterOptionsView.as_view(), name='filter_options_colheita'),
    
    # APIs de Contratos
    path('api/contratos-data/', ContratosFilteredView.as_view(), name='contratos_data'),
    path('api/contratos-filter-options/', ContratosFilterOptionsView.as_view(), name='filter_options_contratos'),
    path('api/mapa/<str:codigo_talhao>/', MapaTalhaoAPIView.as_view(), name='api_mapa_talhao'),
    path('api/lista-talhoes/', ListaTalhoesAPIView.as_view(), name='api_lista_talhoes'),
]
