
# ========================================
# CÁLCULO DO CONSUMO
# ========================================

# Calcula a diferença entre a leitura atual e a leitura anterior.
def consumo_intervalo(leitura_anterior, leitura_atual):
    return round(float(leitura_atual) - float(leitura_anterior), 3)


# ========================================
# CONSUMO DIÁRIO
# ========================================

# Calcula uma estimativa de consumo para um período de 24 horas.
def consumo_diario(consumo_m3, horas):

    # Verifica se o período informado é válido.
    if horas <= 0:
        return 0.0

    return round(float(consumo_m3) * 24 / float(horas), 3)


# ========================================
# CÁLCULO DA MÉDIA
# ========================================

# Calcula a média dos valores recebidos.
def media(valores):

    # Converte os valores para números e ignora os valores vazios.
    valores = [float(v) for v in valores if v is not None]

    return round(sum(valores) / len(valores), 3) if valores else 0.0
