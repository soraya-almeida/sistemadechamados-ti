import sqlite3

DATABASE = "database.db"


def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():

    conn = conectar()

    # ==============================
    # USUÁRIOS
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'usuario'
        )
    """)


    # ==============================
    # CHAMADOS
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL,

            tecnico_id INTEGER,

            nome TEXT NOT NULL,

            email TEXT NOT NULL,

            setor TEXT NOT NULL,

            titulo TEXT NOT NULL,

            descricao TEXT NOT NULL,

            prioridade TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Aberto',

            solucao TEXT DEFAULT '',

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id),

            FOREIGN KEY (tecnico_id)
                REFERENCES usuarios(id)
        )
    """)


    # ==============================
    # COMENTÁRIOS
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chamado_id INTEGER NOT NULL,

            usuario_id INTEGER NOT NULL,

            mensagem TEXT NOT NULL,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (chamado_id)
                REFERENCES chamados(id),

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
        )
    """)


    # ==============================
    # HISTÓRICO
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chamado_id INTEGER NOT NULL,

            usuario_id INTEGER NOT NULL,

            acao TEXT NOT NULL,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (chamado_id)
                REFERENCES chamados(id),

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
        )
    """)


    # Migração simples para bancos antigos
    colunas = [row[1] for row in conn.execute("PRAGMA table_info(chamados)").fetchall()]
    if "solucao" not in colunas:
        conn.execute("ALTER TABLE chamados ADD COLUMN solucao TEXT DEFAULT ''")

    conn.commit()

    conn.close()