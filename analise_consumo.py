
# Importa a função median para calcular a mediana do histórico.
from statistics import median


# ========================================
# ANÁLISE DO CONSUMO
# ========================================

def analisar_intervalo(consumo_m3, horas, historico_diario):

    """Analisa o consumo normalizado para 24h. Regras transparentes, sem afirmar vazamento."""

    # Calcula o consumo estimado considerando um período de 24 horas.
    diario = (consumo_m3 * 24 / horas) if horas > 0 else 0

    # Calcula a mediana do histórico, caso existam registros.
    base = median(historico_diario) if historico_diario else None

    # Lista que armazenará os alertas identificados.
    alertas = []

    # Verifica se o consumo diário atingiu o limite de atenção.
    if diario >= 1.0:

        alertas.append({
            "tipo": "Consumo elevado",
            "nivel": "alto" if diario >= 2.0 else "medio",
            "descricao": f"Consumo estimado de {diario:.3f} m³ em 24 horas, acima do limite de atenção de 1,000 m³/dia.",
            "orientacao": "Confira torneiras, descargas, caixa d'água e tubulações. Se possível, faça um teste com todos os pontos de água fechados."
        })

    # Compara o consumo atual com a mediana do histórico.
    if base is not None and len(historico_diario) >= 3 and diario >= max(1.0, base * 2.5):

        alertas.append({
            "tipo": "Possível vazamento ou consumo fora do padrão",
            "nivel": "alto",
            "descricao": f"O consumo estimado ({diario:.3f} m³/dia) está pelo menos 2,5 vezes acima da mediana recente ({base:.3f} m³/dia).",
            "orientacao": "Verifique se há fluxo contínuo. Feche torneiras e observe o hidrômetro; se continuar avançando, procure um profissional."
        })

    # Identifica um aumento de consumo em relação ao histórico.
    elif base is not None and len(historico_diario) >= 3 and diario >= base * 1.5:

        alertas.append({
            "tipo": "Aumento de consumo",
            "nivel": "medio",
            "descricao": f"Consumo estimado ({diario:.3f} m³/dia) acima do padrão recente ({base:.3f} m³/dia).",
            "orientacao": "Acompanhe as próximas leituras e confira se houve aumento de uso na residência."
        })

    # Retorna os resultados da análise.
    return {
        "consumo_diario_estimado": round(diario, 3),
        "media_historica": round(base, 3) if base is not None else None,
        "alertas": alertas
    }
