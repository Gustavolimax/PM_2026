# Água em Alerta PM

Aplicação web de acompanhamento de leituras acumuladas de hidrômetro, histórico e alertas baseados em consumo.

## Executar
1. `python -m venv venv`
2. Windows PowerShell: `.\venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. `python -m sistema.main`
5. Acesse `http://127.0.0.1:5000`

Cadastre um usuário pela tela de cadastro. Para produção, configure `AGUA_SECRET_KEY`, desative debug e implemente CSRF, confirmação de e-mail, redefinição de senha e controles administrativos.

## Alertas
- Atenção: consumo normalizado de pelo menos 1 m³/dia.
- Possível vazamento/consumo fora do padrão: pelo menos 2,5 vezes a mediana dos intervalos anteriores (mínimo de 3 intervalos) e pelo menos 1 m³/dia.
- A análise é indicativa; não comprova vazamento.
