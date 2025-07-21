from . import views
from django.urls import path
# O 'app_name' é importante para a tag {% url %} no template
app_name = 'fluxo_caixa'

urlpatterns = [
    ## renderiza a page
    path('dashboard/', views.dashboard_financeiro_view, name='dashboard'),  
    ## ViewAPI
    path('api/painel/', views.painel_financeiro_api, name='api_painel_financeiro'),
    path('fluxo_caixa_api_view/', views.fluxo_caixa_api_view, name='fluxo_caixa_api_view'),
    path('api/cpaberto/', views.contas_em_aberto_api, name='cpaberto'),
    path('api/api_fornecedores_view/', views.api_fornecedores_view , name='api_fornecedores'),
    path('download/contas-em-aberto/', views.download_contas_em_aberto_xlsx, name='download_contas_aberto'),

]