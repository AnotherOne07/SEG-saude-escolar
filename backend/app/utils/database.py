import os
import re
import sqlite3
from app.core.config import DB_CONFIG

_sqlite_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "saude_escolar.db")

class SQLiteCursorAdapter:
    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, query, params=None):
        # Transforma consultas de PostgreSQL para SQLite caso em fallback
        # Substitui placeholders %s por ?
        # Trata STRING_AGG se estiver na query
        clean_query = re.sub(r'%s', '?', query)
        # Remove conversões de tipo do Postgres como ::numeric
        clean_query = re.sub(r'::numeric', '', clean_query)
        # Substitui NOW() por CURRENT_TIMESTAMP
        clean_query = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', clean_query, flags=re.IGNORECASE)
        # Trata INTERVAL
        clean_query = re.sub(r"-\s*INTERVAL\s*'[^']+'", '', clean_query, flags=re.IGNORECASE)

        if params is None:
            return self._cur.execute(clean_query)
        else:
            if not isinstance(params, (list, tuple)):
                params = (params,)
            return self._cur.execute(clean_query, params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size)

    def close(self):
        return self._cur.close()

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description


class SQLiteConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorAdapter(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def _init_sqlite_db(conn):
    class StringAgg:
        def __init__(self):
            self.items = []
        def step(self, value, sep=', '):
            if value is not None and str(value).strip() and str(value) not in self.items:
                self.items.append(str(value))
        def finalize(self):
            return ', '.join(self.items)

    conn.create_aggregate("STRING_AGG", 2, StringAgg)

    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS escola (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        endereco TEXT NOT NULL,
        cnpj TEXT NOT NULL,
        telefone TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS turma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL,
        serie TEXT,
        escola_id INTEGER NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS responsavel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        telefone TEXT,
        parentesco TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS aluno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        altura TEXT,
        peso TEXT,
        endereco TEXT,
        matricula TEXT NOT NULL UNIQUE,
        data_nascimento TEXT NOT NULL,
        serie_atual INTEGER,
        responsavel_id INTEGER,
        termo_medicamento_escola INTEGER DEFAULT 1,
        termo_atendimento_medico INTEGER DEFAULT 1,
        termo_compartilhamento_dados INTEGER DEFAULT 1
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        altura REAL,
        peso REAL,
        imc REAL,
        alergias TEXT,
        atividade_fisica TEXT,
        doencas_cronicas TEXT,
        medicamentos_continuos TEXT,
        cirugiais_internacoes TEXT,
        vacinas TEXT,
        deficiencias_necessidades TEXT,
        plano_saude TEXT,
        aluno_id INTEGER NOT NULL,
        matricula TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exame_medico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        resultado TEXT,
        data_solicitacao TEXT NOT NULL,
        data_realizacao TEXT,
        aluno_id INTEGER
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gestor_escolar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        escola_id INTEGER NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS professor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profissional_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL UNIQUE,
        especialidade TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mensagem TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        responsavel_id INTEGER NOT NULL,
        visualizado INTEGER NOT NULL DEFAULT 0,
        remetente INTEGER NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS aluno_turma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        UNIQUE(aluno_id, turma_id)
    );
    """)
    cur.execute("""
    CREATE VIEW IF NOT EXISTS relatorio_individual_aluno AS
    SELECT 
        a.id AS aluno_id,
        a.matricula,
        a.data_nascimento,  
        s.altura,
        s.peso,
        s.imc,
        s.alergias,
        s.atividade_fisica,
        s.doencas_cronicas,
        s.medicamentos_continuos,
        s.cirugiais_internacoes,
        s.vacinas,
        s.deficiencias_necessidades,
        s.plano_saude,
        u.email AS email_responsavel
    FROM aluno a
    LEFT JOIN saude s ON a.id = s.aluno_id
    LEFT JOIN responsavel r ON a.responsavel_id = r.usuario_id
    LEFT JOIN usuario u ON r.usuario_id = u.id;
    """)
    cur.execute("""
    CREATE VIEW IF NOT EXISTS relatorio_geral AS
    SELECT 
        ROUND(AVG(altura), 2) AS media_altura,
        ROUND(AVG(peso), 2) AS media_peso,
        ROUND(AVG(imc), 2) AS media_imc,
        STRING_AGG(DISTINCT alergias, ', ') AS alergias,
        STRING_AGG(DISTINCT doencas_cronicas, ', ') AS doencas_cronicas,
        STRING_AGG(DISTINCT deficiencias_necessidades, ', ') AS deficiencias_necessidades
    FROM saude;
    """)
    cur.execute("""
    CREATE VIEW IF NOT EXISTS relatorio_saude_turma AS
    SELECT 
        t.id AS turma_id,
        t.codigo AS codigo_turma,
        COUNT(a.id) AS total_alunos,
        ROUND(AVG(s.altura), 2) AS media_altura,
        ROUND(AVG(s.peso), 2) AS media_peso,
        ROUND(AVG(s.imc), 2) AS media_imc,
        STRING_AGG(DISTINCT s.alergias, ', ') AS alergias,
        STRING_AGG(DISTINCT s.doencas_cronicas, ', ') AS doencas_cronicas,
        STRING_AGG(DISTINCT s.deficiencias_necessidades, ', ') AS deficiencias_necessidades
    FROM turma t
    LEFT JOIN aluno_turma at ON t.id = at.turma_id
    LEFT JOIN aluno a ON at.aluno_id = a.id
    LEFT JOIN saude s ON a.id = s.aluno_id
    GROUP BY t.id, t.codigo;
    """)

    # Pre-seed se usuario vazio
    cur.execute("SELECT COUNT(*) FROM usuario;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO escola (id, nome, endereco, cnpj, telefone) VALUES (1, 'Escola Municipal Saúde e Saber', 'Av. Principal, 1000 - Centro', '12.345.678/0001-90', '(79) 3211-1234');")
        cur.execute("INSERT INTO turma (id, codigo, serie, escola_id) VALUES (1, 'TURMA-A', '6º Ano Fundamental', 1), (2, 'TURMA-B', '7º Ano Fundamental', 1), (3, 'TURMA-C', '1º Ano Médio', 1);")
        cur.execute("""
        INSERT INTO usuario (id, nome, email, senha, tipo_usuario) VALUES
        (1, 'Gestor Carlos Silva', 'gestor@escola.com', '12345678', 'manager'),
        (2, 'Professora Mariana Santos', 'professor@escola.com', '12345678', 'instructor'),
        (3, 'Responsável Ana Oliveira', 'responsavel@gmail.com', '12345678', 'parent'),
        (4, 'Dr. Roberto Mendes', 'medico@saude.com', '12345678', 'health_professional');
        """)
        cur.execute("INSERT INTO gestor_escolar (usuario_id, escola_id) VALUES (1, 1);")
        cur.execute("INSERT INTO professor (usuario_id) VALUES (2);")
        cur.execute("INSERT INTO responsavel (usuario_id, telefone, parentesco) VALUES (3, '(79) 99876-5432', 'Mãe');")
        cur.execute("INSERT INTO profissional_saude (usuario_id, especialidade) VALUES (4, 'Pediatria e Enfermagem Escolar');")
        cur.execute("""
        INSERT INTO aluno (id, nome, altura, peso, endereco, matricula, data_nascimento, serie_atual, responsavel_id) VALUES
        (1, 'Lucas Oliveira Santos', '1.45', '38.5', 'Rua das Flores, 120', '2026001', '2012-05-14', 1, 3),
        (2, 'Beatriz Lima Costa', '1.52', '44.0', 'Rua Bela Vista, 45', '2026002', '2011-08-20', 2, 3),
        (3, 'Gabriel Souza Rocha', '1.68', '58.0', 'Av. Beira Mar, 300', '2026003', '2010-02-10', 3, 3);
        """)
        cur.execute("INSERT INTO aluno_turma (aluno_id, turma_id) VALUES (1, 1), (2, 2), (3, 3);")
        cur.execute("""
        INSERT INTO saude (id, aluno_id, matricula, altura, peso, imc, alergias, atividade_fisica, doencas_cronicas, medicamentos_continuos, cirugiais_internacoes, vacinas, deficiencias_necessidades, plano_saude) VALUES
        (1, 1, '2026001', 1.45, 38.5, 18.3, 'Amendoim, Frutos do Mar', 'Futebol 2x por semana', 'Asma leve', 'Salbutamol aerossol (SOS)', 'Nenhuma', 'Calendário Vacinal Completo', 'Nenhuma', 'Unimed'),
        (2, 2, '2026002', 1.52, 44.0, 19.0, 'Picada de abelha', 'Natação', 'Rinite alérgica', 'Anti-histamínico se crise', 'Apendicectomia aos 8 anos', 'Completo (incluindo HPV)', 'Nenhuma', 'Bradesco Saúde'),
        (3, 3, '2026003', 1.68, 58.0, 20.5, 'Dipirona', 'Basquete', 'Nenhuma', 'Nenhum', 'Nenhuma', 'Completo', 'Baixa visão (usa óculos)', 'Particular');
        """)
        cur.execute("""
        INSERT INTO alerta (mensagem, responsavel_id, visualizado, remetente) VALUES
        ('Atenção: Campanha de atualização de vacinação ocorrerá na próxima sexta-feira.', 3, 0, 0),
        ('Informo que Lucas precisou usar a bombinha de asma hoje após aula de educação física.', 3, 1, 0),
        ('Obrigada pelo aviso. Ele está bem e já enviei a receita atualizada.', 3, 1, 1);
        """)
    conn.commit()


def connect_db():
    # 1. Tenta PostgreSQL se disponível
    try:
        import psycopg2
        return psycopg2.connect(**DB_CONFIG)
    except Exception as pg_err:
        pass

    # 2. Fallback resiliente para SQLite
    try:
        conn = sqlite3.connect(_sqlite_db_path)
        _init_sqlite_db(conn)
        return SQLiteConnectionAdapter(conn)
    except Exception as sqlite_err:
        print("Erro ao conectar ao banco:", sqlite_err)
        return None
