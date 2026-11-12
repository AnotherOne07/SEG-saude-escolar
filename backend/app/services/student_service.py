from fastapi import HTTPException
from app.utils.database import connect_db
from app.schemas.aluno import AlunoCreate, AlunoUpdate

def create_aluno(aluno: AlunoCreate):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")

    try:
        cur = conn.cursor()
        # Verificar se usuário existe
        cur.execute("SELECT id, tipo_usuario FROM usuario WHERE id = %s;", (aluno.usuario_id,))
        user_res = cur.fetchone()

        if not user_res:
            raise HTTPException(status_code=400, detail="Usuário informado não existe")

        responsavel_id = aluno.usuario_id if user_res[1] == 'parent' else None

        # Inserir aluno na tabela aluno
        query = """
            INSERT INTO aluno (nome, endereco, matricula, data_nascimento, 
                               serie_atual, responsavel_id, termo_medicamento_escola, 
                               termo_atendimento_medico, termo_compartilhamento_dados)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        values = (
            aluno.nome,
            aluno.endereco,
            aluno.matricula,
            aluno.data_nascimento,
            aluno.serie_atual,
            responsavel_id,
            aluno.termo_medicamento_escola if aluno.termo_medicamento_escola is not None else 1,
            aluno.termo_atendimento_medico if aluno.termo_atendimento_medico is not None else 1,
            aluno.termo_compartilhamento_dados if aluno.termo_compartilhamento_dados is not None else 1,
        )

        cur.execute(query, values)
        row = cur.fetchone()
        aluno_id = row[0] if row else None

        # Se houver serie_atual, adiciona também na relação aluno_turma
        if aluno.serie_atual and aluno_id:
            try:
                cur.execute("INSERT INTO aluno_turma (aluno_id, turma_id) VALUES (%s, %s);", (aluno_id, aluno.serie_atual))
            except Exception:
                pass

        conn.commit()
        return {"message": "Aluno adicionado com sucesso!", "aluno_id": aluno_id}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar aluno: {e}")
    finally:
        cur.close()
        conn.close()

def get_all_alunos():
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.nome, a.endereco, a.matricula, a.data_nascimento, 
                   a.serie_atual, a.responsavel_id, a.termo_medicamento_escola, 
                   a.termo_atendimento_medico, a.termo_compartilhamento_dados,
                   s.altura, s.peso, s.imc, s.alergias, s.doencas_cronicas,
                   s.medicamentos_continuos, s.deficiencias_necessidades, s.plano_saude,
                   t.codigo, t.serie
            FROM aluno a
            LEFT JOIN saude s ON a.id = s.aluno_id
            LEFT JOIN turma t ON a.serie_atual = t.id
            ORDER BY a.nome ASC;
        """)
        alunos = []
        for row in cur.fetchall():
            alunos.append({
                "id": row[0],
                "nome": row[1],
                "nomeAluno": row[1],
                "endereco": row[2],
                "matricula": row[3],
                "dataNascimento": str(row[4]),
                "serie_atual": row[5],
                "responsavel_id": row[6],
                "termo_medicamento_escola": row[7],
                "termo_atendimento_medico": row[8],
                "termo_compartilhamento_dados": row[9],
                "altura": row[10],
                "peso": row[11],
                "imc": row[12],
                "alergias": row[13] or "Nenhuma",
                "doencasCronicas": row[14] or "Nenhuma",
                "medicamentos": row[15] or "Nenhum",
                "necessidadesEspeciais": row[16] or "Nenhuma",
                "planoSaude": row[17] or "Não possui",
                "turmaCodigo": row[18],
                "serieTurma": f"{row[18]} - {row[19]}" if row[18] else "Não definida",
                "escola": "Escola Municipal Saúde e Saber"
            })
        return alunos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar lista de alunos: {e}")
    finally:
        cur.close()
        conn.close()

def get_alunos_by_responsavel(responsavel_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.nome, a.endereco, a.matricula, a.data_nascimento, 
                   a.serie_atual, a.responsavel_id, a.termo_medicamento_escola, 
                   a.termo_atendimento_medico, a.termo_compartilhamento_dados,
                   s.altura, s.peso, s.imc, s.alergias, s.doencas_cronicas,
                   s.medicamentos_continuos, s.deficiencias_necessidades, s.plano_saude,
                   t.codigo, t.serie
            FROM aluno a
            LEFT JOIN saude s ON a.id = s.aluno_id
            LEFT JOIN turma t ON a.serie_atual = t.id
            WHERE a.responsavel_id = %s
            ORDER BY a.nome ASC;
        """, (responsavel_id,))
        alunos = []
        for row in cur.fetchall():
            alunos.append({
                "id": row[0],
                "nome": row[1],
                "nomeAluno": row[1],
                "endereco": row[2],
                "matricula": row[3],
                "dataNascimento": str(row[4]),
                "serie_atual": row[5],
                "responsavel_id": row[6],
                "termo_medicamento_escola": row[7],
                "termo_atendimento_medico": row[8],
                "termo_compartilhamento_dados": row[9],
                "altura": row[10],
                "peso": row[11],
                "imc": row[12],
                "alergias": row[13] or "Nenhuma",
                "doencasCronicas": row[14] or "Nenhuma",
                "medicamentos": row[15] or "Nenhum",
                "necessidadesEspeciais": row[16] or "Nenhuma",
                "planoSaude": row[17] or "Não possui",
                "turmaCodigo": row[18],
                "serieTurma": f"{row[18]} - {row[19]}" if row[18] else "Não definida",
                "escola": "Escola Municipal Saúde e Saber"
            })
        return alunos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alunos do responsável: {e}")
    finally:
        cur.close()
        conn.close()

def get_aluno_id(aluno_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.nome, a.endereco, a.matricula, a.data_nascimento, a.serie_atual, 
                   a.responsavel_id, a.termo_medicamento_escola, a.termo_atendimento_medico, a.termo_compartilhamento_dados,
                   s.altura, s.peso, s.imc, s.alergias, s.doencas_cronicas,
                   s.medicamentos_continuos, s.cirugiais_internacoes, s.vacinas,
                   s.deficiencias_necessidades, s.plano_saude, s.atividade_fisica,
                   t.codigo, t.serie
            FROM aluno a
            LEFT JOIN saude s ON a.id = s.aluno_id
            LEFT JOIN turma t ON a.serie_atual = t.id
            WHERE a.id = %s;
        """, (aluno_id,))
        row = cur.fetchone()

        if row:
            return {
                "id": row[0],
                "nome": row[1],
                "nomeAluno": row[1],
                "endereco": row[2],
                "matricula": row[3],
                "data_nascimento": str(row[4]),
                "dataNascimento": str(row[4]),
                "serie_atual": row[5],
                "responsavel_id": row[6],
                "termo_medicamento_escola": row[7],
                "termo_atendimento_medico": row[8],
                "termo_compartilhamento_dados": row[9],
                "altura": row[10],
                "peso": row[11],
                "imc": row[12],
                "alergias": row[13],
                "doencasCronicas": row[14],
                "medicamentos": row[15],
                "cirurgias": row[16],
                "vacinas": row[17],
                "necessidadesEspeciais": row[18],
                "planoSaude": row[19],
                "atividade_fisica": row[20],
                "turmaCodigo": row[21],
                "serieTurma": f"{row[21]} - {row[22]}" if row[21] else "Não definida",
                "escola": "Escola Municipal Saúde e Saber"
            }
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar aluno: {e}")
    finally:
        cur.close()
        conn.close()

def update_aluno_id(aluno: AlunoUpdate):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        query = """
            UPDATE aluno 
            SET nome = %s, endereco = %s, matricula = %s, 
                data_nascimento = %s, serie_atual = %s, responsavel_id = %s, 
                termo_medicamento_escola = %s, termo_atendimento_medico = %s, 
                termo_compartilhamento_dados = %s 
            WHERE id = %s
            RETURNING *;
        """
        values = (
            aluno.nome,
            aluno.endereco,
            aluno.matricula,
            aluno.data_nascimento,
            aluno.serie_atual,
            aluno.responsavel_id,
            aluno.termo_medicamento_escola,
            aluno.termo_atendimento_medico,
            aluno.termo_compartilhamento_dados,
            aluno.id,
        )

        cur.execute(query, tuple(values))
        atualizado = cur.fetchone()
        conn.commit()
        if atualizado:
            return {"message": "Aluno atualizado com sucesso!", "id": atualizado[0]}
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar aluno: {e}")
    finally:
        cur.close()
        conn.close()

def delete_aluno_id(aluno_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM aluno WHERE id = %s RETURNING id;", (aluno_id,))
        deletado = cur.fetchone()
        conn.commit()

        if deletado:
            return {"message": "Aluno removido com sucesso"}
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir aluno: {e}")
    finally:
        cur.close()
        conn.close()
