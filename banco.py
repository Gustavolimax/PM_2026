
import os
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ==========================================================

# Caminho principal do projeto
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pasta e arquivo do banco de dados
DB_DIR = os.path.join(BASE, "banco_de_dados")
DB_PATH = os.path.join(DB_DIR, "agua_em_alerta.db")


# ==========================================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================================

def conectar():
    """Cria e retorna uma conexão com o banco de dados."""

    # Cria a pasta do banco caso ela ainda não exista
    os.makedirs(DB_DIR, exist_ok=True)

    # Estabelece a conexão com SQLite
    con = sqlite3.connect(DB_PATH)

    # Permite acessar os resultados pelo nome das colunas
    con.row_factory = sqlite3.Row

    # Ativa a verificação dos relacionamentos entre tabelas
    con.execute("PRAGMA foreign_keys = ON")

    return con


# ==========================================================
# INICIALIZAÇÃO E CRIAÇÃO DAS TABELAS
# ==========================================================

def inicializar():
    """Cria as tabelas necessárias para o funcionamento do sistema."""

    with conectar() as con:

        con.executescript("""
            -- Tabela de usuários do sistema
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK(perfil IN ('aluno','professor')),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            -- Tabela de leituras de consumo de água
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                leitura REAL NOT NULL CHECK(leitura >= 0),
                data_hora TEXT NOT NULL,
                observacao TEXT DEFAULT '',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, data_hora)
            );

            -- Tabela de alertas gerados pelo sistema
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                leitura_id INTEGER REFERENCES leituras(id) ON DELETE CASCADE,
                tipo TEXT NOT NULL,
                nivel TEXT NOT NULL,
                descricao TEXT NOT NULL,
                orientacao TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            -- Relacionamento entre professores e alunos
            CREATE TABLE IF NOT EXISTS vinculos (
                professor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                aluno_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                PRIMARY KEY(professor_id, aluno_id)
            );

            -- Armazena os fechamentos mensais de consumo
            CREATE TABLE IF NOT EXISTS fechamentos (
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                mes TEXT NOT NULL,
                consumo REAL NOT NULL DEFAULT 0,
                media_diaria REAL NOT NULL DEFAULT 0,
                fechado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(usuario_id, mes)
            );
        """)


# ==========================================================
# CADASTRO DE USUÁRIOS
# ==========================================================

def criar_usuario(nome, email, senha, perfil):
    """Cadastra um novo usuário com senha protegida."""

    with conectar() as con:

        # Cria um hash da senha antes de armazená-la
        senha_hash = generate_password_hash(senha)

        con.execute(
            """
            INSERT INTO usuarios (nome, email, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
            """,
            (
                nome.strip(),
                email.strip().lower(),
                senha_hash,
                perfil
            )
        )


# ==========================================================
# AUTENTICAÇÃO DE USUÁRIOS
# ==========================================================

def autenticar(email, senha):
    """Verifica o e-mail e a senha informados no login."""

    with conectar() as con:

        # Procura o usuário pelo e-mail
        usuario = con.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()

    # Confere se o usuário existe e se a senha está correta
    if usuario and check_password_hash(usuario["senha_hash"], senha):
        return dict(usuario)

    # Retorna None caso os dados estejam incorretos
    return None
