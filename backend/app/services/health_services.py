from fastapi import HTTPException
from app.utils.database import connect_db

def create_saude_student(
    usuario_id: int, matricula: str, altura: float, peso: float,
    alergias: str, atividade_fisica: str, doencas_cronicas: str,
    medicamentos_continuos: str, cirugiais_internacoes: str,
    vacinas: str, deficiencias_necessidades: str, plano_saude: str
):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")

    try:
        cur = conn.cursor()
        # Buscar o ID do aluno pela matrícula
        cur.execute("SELECT id FROM aluno WHERE matricula = %s;", (matricula,))
        aluno = cur.fetchone()

        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado para a matrícula informada")

        aluno_id = aluno[0]

        if altura <= 0 or peso <= 0:
            raise HTTPException(status_code=400, detail="Altura e peso devem ser valores positivos")

        imc = round(peso / (altura ** 2), 2)

        # Atualiza a altura e peso também na tabela aluno
        cur.execute("UPDATE aluno SET altura = %s, peso = %s WHERE id = %s;", (str(altura), str(peso), aluno_id))

        # Verifica se já existe registro de saúde para este aluno
        cur.execute("SELECT id FROM saude WHERE aluno_id = %s;", (aluno_id,))
        existente = cur.fetchone()

        if existente:
            cur.execute("""
                UPDATE saude SET
                    altura = %s, peso = %s, imc = %s, alergias = %s,
                    atividade_fisica = %s, doencas_cronicas = %s,
                    medicamentos_continuos = %s, cirugiais_internacoes = %s,
                    vacinas = %s, deficiencias_necessidades = %s, plano_saude = %s,
                    matricula = %s
                WHERE id = %s RETURNING id;
            """, (
                altura, peso, imc, alergias, atividade_fisica, doencas_cronicas,
                medicamentos_continuos, cirugiais_internacoes, vacinas,
                deficiencias_necessidades, plano_saude, matricula, existente[0]
            ))
            saude_id = existente[0]
        else:
            cur.execute("""
                INSERT INTO saude (
                    aluno_id, matricula, altura, peso, imc, alergias,
                    atividade_fisica, doencas_cronicas, medicamentos_continuos,
                    cirugiais_internacoes, vacinas, deficiencias_necessidades, plano_saude
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """, (
                aluno_id, matricula, altura, peso, imc, alergias,
                atividade_fisica, doencas_cronicas, medicamentos_continuos,
                cirugiais_internacoes, vacinas, deficiencias_necessidades, plano_saude
            ))
            saude_res = cur.fetchone()
            saude_id = saude_res[0] if saude_res else None

        conn.commit()
        return {"message": "Dados de saúde salvos com sucesso!", "saude_id": saude_id, "imc": imc}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar dados de saúde: {e}")
    finally:
        cur.close()
        conn.close()

def get_saude_id(saude_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, altura, peso, imc, alergias, atividade_fisica, doencas_cronicas,
                   medicamentos_continuos, cirugiais_internacoes, vacinas,
                   deficiencias_necessidades, plano_saude, aluno_id, matricula
            FROM saude WHERE id = %s OR aluno_id = %s;
        """, (saude_id, saude_id))
        s = cur.fetchone()

        if s:
            return {
                "id": s[0],
                "altura": s[1],
                "peso": s[2],
                "imc": s[3],
                "alergias": s[4],
                "atividade_fisica": s[5],
                "doencas_cronicas": s[6],
                "medicamentos_continuos": s[7],
                "cirurgias_internacoes": s[8],
                "vacinas": s[9],
                "deficiencias_necessidades": s[10],
                "plano_saude": s[11],
                "aluno_id": s[12],
                "matricula": s[13]
            }
        raise HTTPException(status_code=404, detail="Dados de saúde não encontrados")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados de saúde: {e}")
    finally:
        cur.close()
        conn.close()

def update_saude_id(
    saude_id: int, altura: float, peso: float, alergias: str, atividade_fisica: str,
    doencas_cronicas: str, medicamentos_continuos: str, cirugiais_internacoes: str,
    vacinas: str, deficiencias_necessidades: str, plano_saude: str
):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        imc = round(peso / (altura ** 2), 2) if altura > 0 else 0

        cur.execute("""
            UPDATE saude SET
                altura = %s, peso = %s, imc = %s, alergias = %s,
                atividade_fisica = %s, doencas_cronicas = %s,
                medicamentos_continuos = %s, cirugiais_internacoes = %s,
                vacinas = %s, deficiencias_necessidades = %s, plano_saude = %s
            WHERE id = %s RETURNING id;
        """, (
            altura, peso, imc, alergias, atividade_fisica, doencas_cronicas,
            medicamentos_continuos, cirugiais_internacoes, vacinas,
            deficiencias_necessidades, plano_saude, saude_id
        ))
        res = cur.fetchone()
        conn.commit()

        if res:
            return {"message": "Dados de saúde atualizados com sucesso!", "id": res[0]}
        raise HTTPException(status_code=404, detail="Registro de saúde não encontrado")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar dados de saúde: {e}")
    finally:
        cur.close()
        conn.close()

def delete_saude_id(saude_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM saude WHERE id = %s RETURNING id;", (saude_id,))
        res = cur.fetchone()
        conn.commit()

        if res:
            return {"message": "Dados de saúde removidos com sucesso"}
        raise HTTPException(status_code=404, detail="Dados de saúde não encontrados")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir saúde: {e}")
    finally:
        cur.close()
        conn.close()
