# views.py
from django.http import JsonResponse, HttpRequest
from django.views import View
from django.shortcuts import render

from .pipeline import (
    aguaazul_pipeline_colheita,
    aguaazul_cleanup,
    calculate_kpis,
    get_unique_safra_lazy,
    get_unique_cultura_lazy,
    get_unique_talhao_lazy,
    aguaazul_travas_pipeline,
    kpis_contratos,
    get_uniq_contrato_safra,
    get_uniq_contrato_commoditie,
    get_uniq_contrato_cliente,
    
)

from .maps import(
    view_mapa_por_talhao,listar_talhoes_disponiveis,
)
import polars as pl

class ColheitaFilteredView(View):
    """View para retornar dados de colheita e KPIs filtrados."""
    def get(self, request, *args, **kwargs):
        safra = request.GET.get('safra')
        cultura = request.GET.get('cultura')
        talhao = request.GET.get('talhao')

        try:
            lazy_df = aguaazul_cleanup(
                aguaazul_pipeline_colheita(Safra=safra, cultura=cultura, Talhao=talhao)
            )

            # CORREÇÃO 2: OTIMIZAÇÃO - Executar .collect() apenas uma vez
            final_df = lazy_df.collect()

            # Passar o DataFrame já materializado (eager) para as funções
            kpis = calculate_kpis(final_df)
            table_data = final_df.to_dicts()

            response_data = {
                'kpis': kpis,
                'tableData': table_data
            }
            return JsonResponse(response_data, status=200)

        except Exception as e:
            print(f"Erro na view de colheita: {e}") 
            return JsonResponse({'error': 'Ocorreu um erro ao processar sua requisição.'}, status=500)

class FilterOptionsView(View):
    """View para fornecer os valores únicos para os filtros da UI (Safra, Cultura, Talhão)."""
    def get(self, request, *args, **kwargs):
        try:
            safras = get_unique_safra_lazy().collect().to_series().to_list()
            culturas = get_unique_cultura_lazy().collect().to_series().to_list()
            talhoes = get_unique_talhao_lazy().collect().to_series().to_list()
            
            filter_options = {
                'safras': safras,
                'culturas': culturas,
                'talhoes': talhoes
            }
            return JsonResponse(filter_options, status=200)
        except Exception as e:
            print(f"Erro ao buscar opções de filtro: {e}")
            return JsonResponse({'error': 'Erro ao carregar opções de filtro.'}, status=500)
            
            
class ContratosFilteredView(View):
    """View para retornar dados de contratos e KPIs filtrados."""
    def get(self, request, *args, **kwargs):
        # Esta view já estava perfeita, servindo como modelo.
        safra = request.GET.get('safra')
        commoditie = request.GET.get('commoditie')
        cliente = request.GET.get('cliente')

        try:
            lazy_df = aguaazul_travas_pipeline(
                Safra=safra,
                Commoditie=commoditie,
                Cliente=cliente
            )

            final_df = lazy_df.collect()

            kpis_data = kpis_contratos(final_df)
            table_data = final_df.to_dicts()

            response_data = {
                'KpiContrato': kpis_data,
                'ContratoData': table_data
            }
            return JsonResponse(response_data, status=200)
        except Exception as e:
            print(f"Erro na view de Contratos: {e}") 
            return JsonResponse({'error': 'Ocorreu um erro ao processar sua requisição.'}, status=500)

# CORREÇÃO 3: Adicionar a view para os filtros de Contratos
class ContratosFilterOptionsView(View):
    """View para fornecer os valores únicos para os filtros da UI de Contratos."""
    def get(self, request, *args, **kwargs):
        try:
            safras = get_uniq_contrato_safra().collect().to_series().to_list()
            commodities = get_uniq_contrato_commoditie().collect().to_series().to_list()
            clientes = get_uniq_contrato_cliente().collect().to_series().to_list()
            
            filter_options = {
                'safras': safras,
                'commodities': commodities,
                'clientes': clientes
            }
            return JsonResponse(filter_options, status=200)
        except Exception as e:
            print(f"Erro ao buscar opções de filtro de contratos: {e}")
            return JsonResponse({'error': 'Erro ao carregar opções de filtro.'}, status=500)
        
    
class MapaTalhaoAPIView(View):
    """
    View baseada em classe para retornar os dados de um talhão específico via API.
    """
    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        # Em Class-Based Views, os parâmetros da URL vêm no dicionário kwargs
        codigo_talhao = kwargs.get('codigo_talhao')

        # Verifica se o parâmetro foi realmente passado na URL
        if not codigo_talhao:
            return JsonResponse({'error': 'Código do talhão não fornecido na URL.'}, status=400)

        try:
            # 1. Chama a função que busca e filtra os dados no Polars
            dados_do_talhao_df = view_mapa_por_talhao(codigo_talhao=codigo_talhao)

            # 2. Verifica se o DataFrame retornado está vazio (talhão não encontrado)
            if dados_do_talhao_df.is_empty():
                return JsonResponse({'error': f'Talhão com código {codigo_talhao} não encontrado.'}, status=404)
            
            # 3. Converte o DataFrame para um dicionário (pegando o primeiro e único resultado)
            dados_json = dados_do_talhao_df.to_dicts()[0]

            # 4. Retorna os dados como uma resposta JSON com status 200 OK
            return JsonResponse(dados_json, status=200)

        except Exception as e:
            # Em caso de qualquer outro erro, retorna uma resposta de erro genérica
            print(f"Erro na view do mapa para o talhão {codigo_talhao}: {e}")
            return JsonResponse({'error': 'Ocorreu um erro interno no servidor.'}, status=500)
        
class ListaTalhoesAPIView(View):
    """
    View para fornecer a lista de todos os talhões disponíveis para os filtros.
    """
    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        try:
            talhoes_df = listar_talhoes_disponiveis()
            # Retorna a lista de dicionários diretamente
            return JsonResponse(talhoes_df.to_dicts(), safe=False)
        except Exception as e:
            print(f"Erro ao listar talhões: {e}")
            return JsonResponse({'error': 'Erro ao carregar lista de talhões.'}, status=500)


# As views que renderizam HTML permanecem as mesmas
def home(request):
    return render(request, 'index.html')

def maps(request):
    return render(request, 'maps.html')