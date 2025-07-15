from . import views
from django.urls import path
from . import views

# O 'app_name' é importante para a tag {% url %} no template
app_name = 'fluxo_caixa'

urlpatterns = [
    ## renderiza a page
    path('dashboard/', views.dashboard_financeiro_view, name='dashboard'),  
    ## ViewAPI
    path('api/painel/', views.painel_financeiro_api, name='api_painel_financeiro'),
    path('fluxo_caixa_api_view/', views.fluxo_caixa_api_view, name='fluxo_caixa_api_view'),
    

]