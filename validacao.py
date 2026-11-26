
# Importa datetime para validar a data e o horário informados.
from datetime import datetime


# ========================================
# VALIDAÇÃO DE LEITURA
# ========================================

# Verifica se o valor e a data/horário da leitura são válidos.
def validar_leitura(valor, data_hora):

    # Tenta converter o valor informado para número.
    try:
        valor = float(valor)

    except (TypeError, ValueError):
        return False, "Informe um valor numérico válido."

    # Verifica se a leitura possui valor negativo.
    if valor < 0:
        return False, "A leitura não pode ser negativa."

    # Verifica se a data e o horário estão em formato válido.
    try:
        datetime.fromisoformat(data_hora)

    except (TypeError, ValueError):
        return False, "Data e horário inválidos."

    # Retorna sucesso quando todas as validações passam.
    return True, ""
