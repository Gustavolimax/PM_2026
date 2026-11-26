
# Importa a função responsável por analisar o consumo.
from .analise_consumo import analisar_intervalo


# ========================================
# DETECÇÃO DE ALERTAS
# ========================================

# Identifica os alertas gerados pela análise de consumo.
def detectar(consumo_m3, horas, historico_diario):

    # Executa a análise do consumo e recebe o resultado.
    resultado = analisar_intervalo(consumo_m3, horas, historico_diario)

    # Retorna somente a lista de alertas identificados.
    return resultado["alertas"]
