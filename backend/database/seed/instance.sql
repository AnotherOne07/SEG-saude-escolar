-- Inicialização do Banco de Dados - Plataforma de Saúde Escolar

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_type') THEN
        CREATE TYPE USER_TYPE AS ENUM ('manager', 'instructor', 'parent', 'health_professional');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'acess_level') THEN
        CREATE TYPE ACESS_LEVEL AS ENUM ('reader', 'admin', 'editor');
    END IF;
END $$;

-- Tabelas principais
CREATE TABLE IF NOT EXISTS usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(200) NOT NULL,
    tipo_usuario USER_TYPE NOT NULL
);

CREATE TABLE IF NOT EXISTS escola (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(100) NOT NULL,
    cnpj VARCHAR(100) NOT NULL,
    telefone VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS turma (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL,
    serie VARCHAR(100),
    escola_id INT NOT NULL,
    FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS responsavel (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    telefone VARCHAR(20) NULL,
    parentesco VARCHAR(50) NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS aluno (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    altura VARCHAR(10) NULL,
    peso VARCHAR(10) NULL,
    endereco VARCHAR(100) NULL,
    matricula VARCHAR(15) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    serie_atual INT NULL,
    responsavel_id INT NULL,
    termo_medicamento_escola SMALLINT NULL DEFAULT 1,
    termo_atendimento_medico SMALLINT NULL DEFAULT 1,
    termo_compartilhamento_dados SMALLINT NULL DEFAULT 1,
    FOREIGN KEY (serie_atual) REFERENCES turma(id) ON DELETE SET NULL,
    FOREIGN KEY (responsavel_id) REFERENCES usuario(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS saude ( 
    id SERIAL PRIMARY KEY,
    altura FLOAT,
    peso FLOAT,
    imc FLOAT,
    alergias VARCHAR(300),
    atividade_fisica VARCHAR(200),
    doencas_cronicas VARCHAR(100),
    medicamentos_continuos VARCHAR(100),
    cirugiais_internacoes VARCHAR(100),
    vacinas VARCHAR(200),
    deficiencias_necessidades VARCHAR(200),
    plano_saude VARCHAR(100),
    aluno_id INT NOT NULL,
    matricula VARCHAR(15),
    FOREIGN KEY (aluno_id) REFERENCES aluno(id) ON DELETE CASCADE,
    FOREIGN KEY (matricula) REFERENCES aluno(matricula) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exame_medico (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,
    resultado VARCHAR(1000),
    data_solicitacao DATE NOT NULL,
    data_realizacao DATE,
    aluno_id INT NULL,
    FOREIGN KEY (aluno_id) REFERENCES aluno(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gestor_escolar (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    escola_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS professor (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS profissional_saude (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    especialidade VARCHAR(100) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS permissao_usuario (
    id SERIAL PRIMARY KEY,
    tipo_usuario USER_TYPE NOT NULL,
    nivel_acesso ACESS_LEVEL NOT NULL
);

CREATE TABLE IF NOT EXISTS alerta (
    id SERIAL PRIMARY KEY,
    mensagem VARCHAR(500) NOT NULL,
    data_criacao TIMESTAMP NOT NULL,
    responsavel_id INT NOT NULL,
    visualizado SMALLINT NOT NULL DEFAULT 0,
    remetente SMALLINT NOT NULL, -- 1 indica que o usuário é o remetente, 0 que a gestão é remetente
    FOREIGN KEY (responsavel_id) REFERENCES responsavel(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS aluno_turma (
    id SERIAL PRIMARY KEY,
    aluno_id INT NOT NULL,
    turma_id INT NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES aluno(id) ON DELETE CASCADE,
    FOREIGN KEY (turma_id) REFERENCES turma(id) ON DELETE CASCADE,
    UNIQUE (aluno_id, turma_id)
);

-- Views Analíticas de Saúde
CREATE OR REPLACE VIEW relatorio_individual_aluno AS
SELECT 
    a.id AS aluno_id,
    a.matricula,
    a.data_nascimento,  
    saude.altura,
    saude.peso,
    saude.imc,
    saude.alergias,
    saude.atividade_fisica,
    saude.doencas_cronicas,
    saude.medicamentos_continuos,
    saude.cirugiais_internacoes,
    saude.vacinas,
    saude.deficiencias_necessidades,
    saude.plano_saude,
    u.email AS email_responsavel
FROM aluno a
LEFT JOIN saude saude ON a.id = saude.aluno_id
LEFT JOIN responsavel r ON a.responsavel_id = r.usuario_id
LEFT JOIN usuario u ON r.usuario_id = u.id;

CREATE OR REPLACE VIEW relatorio_geral AS
SELECT 
    ROUND(AVG(altura)::numeric, 2) AS media_altura,
    ROUND(AVG(peso)::numeric, 2) AS media_peso,
    ROUND(AVG(imc)::numeric, 2) AS media_imc,
    STRING_AGG(DISTINCT NULLIF(alergias, ''), ', ') AS alergias,
    STRING_AGG(DISTINCT NULLIF(doencas_cronicas, ''), ', ') AS doencas_cronicas,
    STRING_AGG(DISTINCT NULLIF(deficiencias_necessidades, ''), ', ') AS deficiencias_necessidades
FROM saude;

CREATE OR REPLACE VIEW relatorio_saude_turma AS
SELECT 
    t.id AS turma_id,
    t.codigo AS codigo_turma,
    COUNT(a.id) AS total_alunos,
    ROUND(AVG(s.altura)::numeric, 2) AS media_altura,
    ROUND(AVG(s.peso)::numeric, 2) AS media_peso,
    ROUND(AVG(s.imc)::numeric, 2) AS media_imc,
    STRING_AGG(DISTINCT NULLIF(s.alergias, ''), ', ') AS alergias,
    STRING_AGG(DISTINCT NULLIF(s.doencas_cronicas, ''), ', ') AS doencas_cronicas,
    STRING_AGG(DISTINCT NULLIF(s.deficiencias_necessidades, ''), ', ') AS deficiencias_necessidades
FROM turma t
LEFT JOIN aluno_turma at ON t.id = at.turma_id
LEFT JOIN aluno a ON at.aluno_id = a.id
LEFT JOIN saude s ON a.id = s.aluno_id
GROUP BY t.id, t.codigo;

-- Seed inicial de dados para testes imediatos
INSERT INTO escola (id, nome, endereco, cnpj, telefone) 
VALUES (1, 'Escola Municipal Saúde e Saber', 'Av. Principal, 1000 - Centro', '12.345.678/0001-90', '(79) 3211-1234')
ON CONFLICT (id) DO NOTHING;

INSERT INTO turma (id, codigo, serie, escola_id)
VALUES 
    (1, 'TURMA-A', '6º Ano Fundamental', 1),
    (2, 'TURMA-B', '7º Ano Fundamental', 1),
    (3, 'TURMA-C', '1º Ano Médio', 1)
ON CONFLICT (id) DO NOTHING;

-- Usuários: senhas padrão '12345678'
-- Hash bcrypt de '12345678'
INSERT INTO usuario (id, nome, email, senha, tipo_usuario)
VALUES
    (1, 'Gestor Carlos Silva', 'gestor@escola.com', '$2b$12$Z0bC7rJ4bYx9u5KqH/tGXeXzG5h3e8W7lQj9p2k1m3o5u7y9s1a2b', 'manager'),
    (2, 'Professora Mariana Santos', 'professor@escola.com', '$2b$12$Z0bC7rJ4bYx9u5KqH/tGXeXzG5h3e8W7lQj9p2k1m3o5u7y9s1a2b', 'instructor'),
    (3, 'Responsável Ana Oliveira', 'responsavel@gmail.com', '$2b$12$Z0bC7rJ4bYx9u5KqH/tGXeXzG5h3e8W7lQj9p2k1m3o5u7y9s1a2b', 'parent'),
    (4, 'Dr. Roberto Mendes', 'medico@saude.com', '$2b$12$Z0bC7rJ4bYx9u5KqH/tGXeXzG5h3e8W7lQj9p2k1m3o5u7y9s1a2b', 'health_professional')
ON CONFLICT (id) DO NOTHING;

INSERT INTO gestor_escolar (id, usuario_id, escola_id)
VALUES (1, 1, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO professor (id, usuario_id)
VALUES (1, 2)
ON CONFLICT (id) DO NOTHING;

INSERT INTO responsavel (id, usuario_id, telefone, parentesco)
VALUES (1, 3, '(79) 99876-5432', 'Mãe')
ON CONFLICT (id) DO NOTHING;

INSERT INTO profissional_saude (id, usuario_id, especialidade)
VALUES (1, 4, 'Pediatria e Enfermagem Escolar')
ON CONFLICT (id) DO NOTHING;

-- Alunos e Histórico de Saúde
INSERT INTO aluno (id, nome, altura, peso, endereco, matricula, data_nascimento, serie_atual, responsavel_id, termo_medicamento_escola, termo_atendimento_medico, termo_compartilhamento_dados)
VALUES 
    (1, 'Lucas Oliveira Santos', '1.45', '38.5', 'Rua das Flores, 120', '2026001', '2012-05-14', 1, 3, 1, 1, 1),
    (2, 'Beatriz Lima Costa', '1.52', '44.0', 'Rua Bela Vista, 45', '2026002', '2011-08-20', 2, 3, 1, 1, 1),
    (3, 'Gabriel Souza Rocha', '1.68', '58.0', 'Av. Beira Mar, 300', '2026003', '2010-02-10', 3, 3, 1, 1, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO aluno_turma (aluno_id, turma_id)
VALUES 
    (1, 1),
    (2, 2),
    (3, 3)
ON CONFLICT (aluno_id, turma_id) DO NOTHING;

INSERT INTO saude (id, aluno_id, matricula, altura, peso, imc, alergias, atividade_fisica, doencas_cronicas, medicamentos_continuos, cirugiais_internacoes, vacinas, deficiencias_necessidades, plano_saude)
VALUES
    (1, 1, '2026001', 1.45, 38.5, 18.3, 'Amendoim, Frutos do Mar', 'Futebol 2x por semana', 'Asma leve', 'Salbutamol aerossol (SOS)', 'Nenhuma', 'Calendário Vacinal Completo', 'Nenhuma', 'Unimed'),
    (2, 2, '2026002', 1.52, 44.0, 19.0, 'Picada de abelha', 'Natação', 'Rinite alérgica', 'Anti-histamínico se crise', 'Apendicectomia aos 8 anos', 'Completo (incluindo HPV)', 'Nenhuma', 'Bradesco Saúde'),
    (3, 3, '2026003', 1.68, 58.0, 20.5, 'Dipirona', 'Basquete', 'Nenhuma', 'Nenhum', 'Nenhuma', 'Completo', 'Baixa visão (usa óculos)', 'Particular')
ON CONFLICT (id) DO NOTHING;

INSERT INTO alerta (id, mensagem, data_criacao, responsavel_id, visualizado, remetente)
VALUES
    (1, 'Atenção: Campanha de atualização de vacinação ocorrerá na próxima sexta-feira.', NOW(), 1, 0, 0),
    (2, 'Informo que Lucas precisou usar a bombinha de asma hoje após aula de educação física.', NOW() - INTERVAL '1 day', 1, 1, 0),
    (3, 'Obrigada pelo aviso. Ele está bem e já enviei a receita atualizada.', NOW() - INTERVAL '20 hours', 1, 1, 1)
ON CONFLICT (id) DO NOTHING;

-- Ajustar sequences do Postgres
SELECT setval('escola_id_seq', (SELECT COALESCE(MAX(id), 1) FROM escola));
SELECT setval('turma_id_seq', (SELECT COALESCE(MAX(id), 1) FROM turma));
SELECT setval('usuario_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuario));
SELECT setval('responsavel_id_seq', (SELECT COALESCE(MAX(id), 1) FROM responsavel));
SELECT setval('profissional_saude_id_seq', (SELECT COALESCE(MAX(id), 1) FROM profissional_saude));
SELECT setval('aluno_id_seq', (SELECT COALESCE(MAX(id), 1) FROM aluno));
SELECT setval('saude_id_seq', (SELECT COALESCE(MAX(id), 1) FROM saude));
SELECT setval('alerta_id_seq', (SELECT COALESCE(MAX(id), 1) FROM alerta));
