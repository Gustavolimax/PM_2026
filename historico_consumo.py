
# Importa datetime para trabalhar com datas e horários.
from datetime import datetime


# ========================================
# AGRUPAMENTO DE REGISTROS POR MÊS
# ========================================

# Organiza os registros de acordo com o mês e o ano.
def agrupar_por_mes(registros):

    # Cria um dicionário para armazenar os grupos.
    grupos = {}

    # Percorre todos os registros recebidos.
    for r in registros:

        # Extrai o ano e o mês da data de cada registro.
        chave = datetime.fromisoformat(r["data_hora"]).strftime("%Y-%m")

        # Adiciona o registro ao grupo correspondente.
        grupos.setdefault(chave, []).append(r)

    # Retorna os registros separados por mês.
    return grupos
