
# ==========================================================
# IMPORTAÇÕES
# ==========================================================

import os

from datetime import datetime, date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from .banco import (
    inicializar,
    conectar,
    criar_usuario,
    autenticar
)

from algoritmos.validacao import validar_leitura
from algoritmos.analise_consumo import analisar_intervalo


# ==========================================================
# CONFIGURAÇÕES DA APLICAÇÃO
# ==========================================================

# Caminho principal do projeto
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Criação da aplicação Flask
app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "web", "templates"),
    static_folder=os.path.join(BASE, "web", "static")
)

# Chave utilizada para proteger as sessões dos usuários
app.secret_key = os.environ.get(
    "AGUA_SECRET_KEY",
    "troque-esta-chave-em-producao"
)

# Configurações de segurança dos cookies da sessão
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# Inicializa o banco de dados e cria as tabelas necessárias
inicializar()


# ==========================================================
# CONTROLE DE ACESSO E SESSÃO
# ==========================================================

def usuario_atual():
    """Retorna os dados do usuário que está conectado."""

    return session.get("usuario")


def login_obrigatorio():
    """Verifica se existe um usuário conectado."""

    if not usuario_atual():
        return redirect(url_for("login"))

    return None


# ==========================================================
# CONSULTA DE LEITURAS
# ==========================================================

def leituras_usuario(uid):
    """Busca todas as leituras registradas por um usuário."""

    with conectar() as con:

        registros = con.execute(
            """
            SELECT *
            FROM leituras
            WHERE usuario_id = ?
            ORDER BY data_hora
            """,
            (uid,)
        ).fetchall()

        return [dict(r) for r in registros]


# ==========================================================
# CÁLCULO DE CONSUMO ENTRE LEITURAS
# ==========================================================

def calcular_intervalos(registros):
    """
    Calcula o consumo de água entre duas leituras consecutivas.

    Também calcula o intervalo de horas e uma estimativa
    de consumo diário.
    """

    resultado = []

    # Percorre os registros a partir da segunda leitura
    for i in range(1, len(registros)):

        anterior = registros[i - 1]
        atual = registros[i]

        # Converte as datas armazenadas em objetos datetime
        dt1 = datetime.fromisoformat(anterior["data_hora"])
        dt2 = datetime.fromisoformat(atual["data_hora"])

        # Calcula o tempo entre as duas leituras
        horas = (dt2 - dt1).total_seconds() / 3600

        # Calcula a diferença entre os valores do hidrômetro
        consumo = atual["leitura"] - anterior["leitura"]

        # Calcula a estimativa de consumo diário
        diario = round(consumo * 24 / horas, 3) if horas > 0 else 0

        resultado.append({
            "data_hora": atual["data_hora"],
            "consumo": round(consumo, 3),
            "horas": horas,
            "diario": diario
        })

    return resultado


# ==========================================================
# ROTA INICIAL
# ==========================================================

@app.route("/")
def index():
    """Direciona o usuário para o login ou painel principal."""

    if not usuario_atual():
        return redirect(url_for("login"))

    return redirect(url_for("dashboard"))


# ==========================================================
# CADASTRO DE USUÁRIOS
# ==========================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Realiza o cadastro de alunos e professores."""

    if request.method == "POST":

        # Recebe e organiza os dados enviados pelo formulário
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        perfil = request.form.get("perfil", "aluno")

        # Verifica se os dados obrigatórios foram preenchidos
        if (
            not nome
            or not email
            or len(senha) < 8
            or perfil not in ("aluno", "professor")
        ):
            flash(
                "Preencha os campos corretamente. "
                "A senha deve ter pelo menos 8 caracteres.",
                "erro"
            )

        else:

            try:
                # Salva o novo usuário no banco de dados
                criar_usuario(nome, email, senha, perfil)

                flash("Conta criada! Faça login.", "sucesso")

                return redirect(url_for("login"))

            except Exception:
                flash(
                    "Este e-mail já está cadastrado ou os dados são inválidos.",
                    "erro"
                )

    return render_template("cadastro.html")


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Autentica o usuário e inicia sua sessão."""

    if request.method == "POST":

        # Verifica o e-mail e a senha informados
        usuario = autenticar(
            request.form.get("email", ""),
            request.form.get("senha", "")
        )

        if usuario:

            # Limpa qualquer sessão anterior
            session.clear()

            # Armazena os dados básicos do usuário conectado
            session["usuario"] = {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "perfil": usuario["perfil"]
            }

            return redirect(url_for("dashboard"))

        # Mensagem exibida quando os dados estão incorretos
        flash("E-mail ou senha inválidos.", "erro")

    return render_template("login.html")


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():
    """Encerra a sessão do usuário."""

    session.clear()

    return redirect(url_for("login"))


# ==========================================================
# PAINEL PRINCIPAL (DASHBOARD)
# ==========================================================

@app.route("/dashboard")
def dashboard():
    """Apresenta o resumo do consumo e os alertas recentes."""

    if not usuario_atual():
        return redirect(url_for("login"))

    usuario = usuario_atual()

    # Busca as leituras e calcula os intervalos de consumo
    registros = leituras_usuario(usuario["id"])
    intervalos = calcular_intervalos(registros)

    # Identifica o mês atual
    mes = date.today().strftime("%Y-%m")

    # Soma o consumo registrado durante o mês atual
    consumo_mes = sum(
        x["consumo"]
        for x in intervalos
        if x["data_hora"][:7] == mes
    )

    # Separa os valores válidos para calcular a média diária
    diarios = [
        x["diario"]
        for x in intervalos
        if x["diario"] > 0
    ]

    # Calcula a média de consumo diário
    media = round(sum(diarios) / len(diarios), 3) if diarios else 0

    # Busca os dez alertas mais recentes do usuário
    with conectar() as con:

        alertas = [
            dict(a)
            for a in con.execute(
                """
                SELECT *
                FROM alertas
                WHERE usuario_id = ?
                ORDER BY id DESC
                LIMIT 10
                """,
                (usuario["id"],)
            ).fetchall()
        ]

    # Envia as informações para a página do painel
    return render_template(
        "dashboard.html",
        usuario=usuario,
        registros=registros,
        intervalos=intervalos,
        consumo_mes=round(consumo_mes, 3),
        media=media,
        alertas=alertas
    )


# ==========================================================
# REGISTRO DE LEITURAS
# ==========================================================

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Registra novas leituras do hidrômetro."""

    if not usuario_atual():
        return redirect(url_for("login"))

    usuario = usuario_atual()

    if request.method == "POST":

        # Recebe os dados enviados pelo formulário
        leitura = request.form.get("leitura", "")
        data_hora = request.form.get("data_hora", "")
        observacao = request.form.get("observacao", "").strip()

        # Valida os dados da leitura
        ok, msg = validar_leitura(leitura, data_hora)

        if not ok:

            flash(msg, "erro")

        else:

            # Converte o valor informado para número decimal
            valor = float(leitura)

            with conectar() as con:

                # Busca a última leitura registrada pelo usuário
                anterior = con.execute(
                    """
                    SELECT *
                    FROM leituras
                    WHERE usuario_id = ?
                    ORDER BY data_hora DESC
                    LIMIT 1
                    """,
                    (usuario["id"],)
                ).fetchone()

                # Verifica se já existe uma leitura anterior
                if anterior:

                    dt = datetime.fromisoformat(data_hora)
                    dt_ant = datetime.fromisoformat(anterior["data_hora"])

                    # A nova leitura precisa ter data e horário posteriores
                    if dt <= dt_ant:

                        flash(
                            "A nova leitura deve ter data e horário "
                            "posteriores à leitura anterior.",
                            "erro"
                        )

                        return render_template("registrar.html")

                    # Impede que o valor do hidrômetro diminua
                    if valor < anterior["leitura"]:

                        flash(
                            "A leitura não pode ser menor que a anterior. "
                            "Se o hidrômetro foi substituído ou reiniciado, "
                            "procure a opção de ajuste (ainda não implementada).",
                            "erro"
                        )

                        return render_template("registrar.html")

                    # Calcula o consumo desde a leitura anterior
                    consumo = valor - anterior["leitura"]

                    # Calcula o intervalo de tempo em horas
                    horas = (dt - dt_ant).total_seconds() / 3600

                    # Histórico utilizado para analisar o comportamento
                    # do consumo nas leituras anteriores
                    hist = []

                    rows = con.execute(
                        """
                        SELECT leitura, data_hora
                        FROM leituras
                        WHERE usuario_id = ?
                        ORDER BY data_hora
                        """,
                        (usuario["id"],)
                    ).fetchall()

                    # Calcula o consumo diário dos intervalos anteriores
                    for i in range(1, len(rows)):

                        h = (
                            datetime.fromisoformat(rows[i]["data_hora"])
                            - datetime.fromisoformat(rows[i - 1]["data_hora"])
                        ).total_seconds() / 3600

                        if h > 0:

                            consumo_diario = (
                                rows[i]["leitura"] - rows[i - 1]["leitura"]
                            ) * 24 / h

                            hist.append(consumo_diario)

                    # Analisa a nova leitura utilizando os últimos
                    # 14 intervalos disponíveis no histórico
                    analise = analisar_intervalo(
                        consumo,
                        horas,
                        hist[-14:]
                    )

                else:

                    # Primeira leitura: ainda não existe histórico
                    # suficiente para realizar uma análise
                    analise = {"alertas": []}

                # Salva a nova leitura no banco de dados
                con.execute(
                    """
                    INSERT INTO leituras (
                        usuario_id,
                        leitura,
                        data_hora,
                        observacao
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        usuario["id"],
                        valor,
                        data_hora,
                        observacao
                    )
                )

                # Recupera o ID da leitura recém-criada
                leitura_id = con.execute(
                    "SELECT last_insert_rowid()"
                ).fetchone()[0]

                # Registra os alertas identificados pela análise
                for alerta in analise["alertas"]:

                    con.execute(
                        """
                        INSERT INTO alertas (
                            usuario_id,
                            leitura_id,
                            tipo,
                            nivel,
                            descricao,
                            orientacao
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            usuario["id"],
                            leitura_id,
                            alerta["tipo"],
                            alerta["nivel"],
                            alerta["descricao"],
                            alerta["orientacao"]
                        )
                    )

            # Exibe a mensagem de acordo com o resultado da análise
            if analise["alertas"]:

                flash(
                    "Leitura registrada. O sistema identificou "
                    "alerta(s) para análise.",
                    "aviso"
                )

            else:

                flash(
                    "Leitura registrada com sucesso.",
                    "sucesso"
                )

            return redirect(url_for("dashboard"))

    return render_template("registrar.html")


# ==========================================================
# HISTÓRICO DE LEITURAS
# ==========================================================

@app.route("/historico")
def historico():
    """Apresenta o histórico de leituras do usuário."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Busca as leituras e calcula os intervalos de consumo
    registros = leituras_usuario(usuario_atual()["id"])
    intervalos = calcular_intervalos(registros)

    # Inverte a ordem para mostrar os registros mais recentes primeiro
    registros = list(reversed(registros))

    return render_template(
        "historico.html",
        registros=registros,
        intervalos=intervalos
    )


# ==========================================================
# CALENDÁRIO DE LEITURAS
# ==========================================================

@app.route("/calendario")
def calendario():
    """Exibe as leituras registradas em determinado mês."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Recebe o mês solicitado ou utiliza o mês atual
    mes = request.args.get(
        "mes",
        date.today().strftime("%Y-%m")
    )

    # Valida o formato do mês informado
    try:

        ano, numero = map(int, mes.split("-"))

        if not 1 <= numero <= 12:
            raise ValueError

    except ValueError:

        ano = date.today().year
        numero = date.today().month

    # Formata o mês para realizar a consulta
    mes_formatado = f"{ano:04d}-{numero:02d}"

    with conectar() as con:

        # Busca somente as leituras do mês selecionado
        registros = [
            dict(r)
            for r in con.execute(
                """
                SELECT *
                FROM leituras
                WHERE usuario_id = ?
                AND substr(data_hora, 1, 7) = ?
                ORDER BY data_hora
                """,
                (
                    usuario_atual()["id"],
                    mes_formatado
                )
            ).fetchall()
        ]

    return render_template(
        "calendario.html",
        registros=registros,
        mes=mes_formatado
    )


# ==========================================================
# CONSULTA DE ALERTAS
# ==========================================================

@app.route("/alertas")
def alertas():
    """Exibe todos os alertas registrados para o usuário."""

    if not usuario_atual():
        return redirect(url_for("login"))

    with conectar() as con:

        # Busca os alertas em ordem do mais recente para o mais antigo
        rows = [
            dict(r)
            for r in con.execute(
                """
                SELECT *
                FROM alertas
                WHERE usuario_id = ?
                ORDER BY id DESC
                """,
                (usuario_atual()["id"],)
            ).fetchall()
        ]

    return render_template(
        "alertas.html",
        alertas=rows
    )


# ==========================================================
# RELATÓRIOS DE CONSUMO
# ==========================================================

@app.route("/relatorios")
def relatorios():
    """Agrupa o consumo de água por mês."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Busca as leituras e calcula os intervalos
    registros = leituras_usuario(usuario_atual()["id"])
    intervalos = calcular_intervalos(registros)

    # Dicionário que armazenará o consumo de cada mês
    meses = {}

    # Soma o consumo dos intervalos pertencentes ao mesmo mês
    for intervalo in intervalos:

        mes = intervalo["data_hora"][:7]

        meses[mes] = round(
            meses.get(mes, 0) + intervalo["consumo"],
            3
        )

    return render_template(
        "relatorios.html",
        meses=meses
    )


# ==========================================================
# ÁREA DO PROFESSOR - LISTAGEM DE ALUNOS
# ==========================================================

@app.route("/alunos")
def alunos():
    """Apresenta os alunos vinculados ao professor conectado."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Verifica se o usuário possui perfil de professor
    if usuario_atual()["perfil"] != "professor":

        flash(
            "Acesso permitido somente a professores.",
            "erro"
        )

        return redirect(url_for("dashboard"))

    with conectar() as con:

        # Busca os alunos vinculados ao professor
        vinculados = [
            dict(r)
            for r in con.execute(
                """
                SELECT u.id, u.nome, u.email
                FROM usuarios u
                JOIN vinculos v ON v.aluno_id = u.id
                WHERE v.professor_id = ?
                """,
                (usuario_atual()["id"],)
            ).fetchall()
        ]

    return render_template(
        "alunos.html",
        alunos=vinculados
    )


# ==========================================================
# ÁREA DO PROFESSOR - VINCULAR ALUNO
# ==========================================================

@app.route("/vincular-aluno", methods=["POST"])
def vincular_aluno():
    """Vincula um aluno à conta do professor."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Somente professores podem realizar vínculos
    if usuario_atual()["perfil"] != "professor":

        flash("Acesso negado.", "erro")

        return redirect(url_for("dashboard"))

    # Recebe o e-mail do aluno
    email = request.form.get("email", "").strip().lower()

    with conectar() as con:

        # Procura um usuário com o e-mail informado e perfil de aluno
        aluno = con.execute(
            """
            SELECT id
            FROM usuarios
            WHERE email = ?
            AND perfil = 'aluno'
            """,
            (email,)
        ).fetchone()

        if aluno:

            # Cria o vínculo sem duplicar um relacionamento existente
            con.execute(
                """
                INSERT OR IGNORE INTO vinculos (
                    professor_id,
                    aluno_id
                )
                VALUES (?, ?)
                """,
                (
                    usuario_atual()["id"],
                    aluno["id"]
                )
            )

            flash("Aluno vinculado.", "sucesso")

        else:

            flash("Aluno não encontrado.", "erro")

    return redirect(url_for("alunos"))


# ==========================================================
# ÁREA DO PROFESSOR - DETALHES DO ALUNO
# ==========================================================

@app.route("/aluno/<int:aluno_id>")
def visualizar_aluno(aluno_id):
    """Permite ao professor consultar os dados de um aluno vinculado."""

    if not usuario_atual():
        return redirect(url_for("login"))

    # Verifica se o usuário conectado é professor
    if usuario_atual()["perfil"] != "professor":
        return redirect(url_for("dashboard"))

    with conectar() as con:

        # Verifica se existe vínculo entre professor e aluno
        vinculo = con.execute(
            """
            SELECT 1
            FROM vinculos
            WHERE professor_id = ?
            AND aluno_id = ?
            """,
            (
                usuario_atual()["id"],
                aluno_id
            )
        ).fetchone()

        # Impede o acesso aos dados de alunos não vinculados
        if not vinculo:
            return "Acesso não autorizado", 403

        # Busca o nome do aluno
        aluno = con.execute(
            """
            SELECT nome
            FROM usuarios
            WHERE id = ?
            """,
            (aluno_id,)
        ).fetchone()

        # Busca o histórico de leituras do aluno
        registros = [
            dict(r)
            for r in con.execute(
                """
                SELECT *
                FROM leituras
                WHERE usuario_id = ?
                ORDER BY data_hora
                """,
                (aluno_id,)
            ).fetchall()
        ]

        # Busca os alertas registrados para o aluno
        alertas = [
            dict(r)
            for r in con.execute(
                """
                SELECT *
                FROM alertas
                WHERE usuario_id = ?
                ORDER BY id DESC
                """,
                (aluno_id,)
            ).fetchall()
        ]

    return render_template(
        "aluno_detalhe.html",
        aluno=aluno["nome"],
        registros=registros,
        alertas=alertas
    )


# ==========================================================
# EXECUÇÃO DA APLICAÇÃO
# ==========================================================

if __name__ == "__main__":

    # Inicia o servidor local Flask
    app.run(debug=True)
