from fastapi import HTTPException
from app.utils.database import connect_db
from app.core.security import hash_senha

ROLE_MAP = {
    "gestorescolar": "manager",
    "manager": "manager",
    "professor": "instructor",
    "instructor": "instructor",
    "responsavel": "parent",
    "parent": "parent",
    "profissionalsaude": "health_professional",
    "health_professional": "health_professional",
}

def create_user(usuario):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    senha_raw = getattr(usuario, "segredo", None) or getattr(usuario, "senha", None)
    if not senha_raw:
        raise HTTPException(status_code=400, detail="Senha é obrigatória")

    senha_hash = hash_senha(senha_raw)
    raw_tipo = str(usuario.tipo_usuario).lower().strip()
    tipo_usuario = ROLE_MAP.get(raw_tipo, raw_tipo)

    try:
        cur = conn.cursor()
        # Verificar se email já existe
        cur.execute("SELECT id FROM usuario WHERE email = %s;", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        cur.execute("""
            INSERT INTO usuario (nome, email, senha, tipo_usuario) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (usuario.nome, usuario.email, senha_hash, tipo_usuario))

        res = cur.fetchone()
        usuario_id = res[0] if res else None

        # Vincula tabela de perfil específica
        if tipo_usuario == "parent":
            cur.execute("INSERT INTO responsavel (usuario_id) VALUES (%s);", (usuario_id,))
        elif tipo_usuario == "manager":
            cur.execute("SELECT id FROM escola LIMIT 1;")
            escola_res = cur.fetchone()
            escola_id = escola_res[0] if escola_res else 1
            cur.execute("INSERT INTO gestor_escolar (usuario_id, escola_id) VALUES (%s, %s);", (usuario_id, escola_id))
        elif tipo_usuario == "instructor":
            cur.execute("INSERT INTO professor (usuario_id) VALUES (%s);", (usuario_id,))
        elif tipo_usuario == "health_professional":
            cur.execute("INSERT INTO profissional_saude (usuario_id, especialidade) VALUES (%s, %s);", (usuario_id, 'Enfermagem/Saúde Escolar'))

        conn.commit()
        return {"id": usuario_id, "nome": usuario.nome, "email": usuario.email, "tipo_usuario": tipo_usuario}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário: {e}")
    finally:
        cur.close()
        conn.close()

def get_usuario():
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, tipo_usuario FROM usuario;")
        usuarios = [{"id": u[0], "nome": u[1], "email": u[2], "tipo_usuario": u[3]} for u in cur.fetchall()]
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar usuários: {e}")
    finally:
        cur.close()
        conn.close()

def get_professores():
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, tipo_usuario FROM usuario WHERE tipo_usuario = 'instructor';")
        professores = [{"id": u[0], "nome": u[1], "email": u[2], "tipo_usuario": u[3]} for u in cur.fetchall()]
        return professores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar professores: {e}")
    finally:
        cur.close()
        conn.close()

def get_usuario_id(usuario_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, tipo_usuario FROM usuario WHERE id = %s;", (usuario_id,))
        usuario = cur.fetchone()

        if usuario:
            return {"id": usuario[0], "nome": usuario[1], "email": usuario[2], "tipo_usuario": usuario[3]}
        else:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar usuário: {e}")
    finally:
        cur.close()
        conn.close()

def update_user(usuario):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        updates = []
        valores = []
        
        if getattr(usuario, "nome", None):
            updates.append("nome = %s")
            valores.append(usuario.nome)
        if getattr(usuario, "email", None):
            updates.append("email = %s")
            valores.append(usuario.email)
        if getattr(usuario, "segredo", None):
            updates.append("senha = %s")
            valores.append(hash_senha(usuario.segredo))
        if getattr(usuario, "tipo_usuario", None):
            updates.append("tipo_usuario = %s")
            valores.append(usuario.tipo_usuario)

        if not updates:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        valores.append(usuario.id)
        query = f"UPDATE usuario SET {', '.join(updates)} WHERE id = %s RETURNING id, nome, email, tipo_usuario;"
        cur.execute(query, tuple(valores))
        atualizado = cur.fetchone()
        conn.commit()

        if atualizado:
            return {"id": atualizado[0], "nome": atualizado[1], "email": atualizado[2], "tipo_usuario": atualizado[3]}
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar usuário: {e}")
    finally:
        cur.close()
        conn.close()

def delete_user(usuario_id: int):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM usuario WHERE id = %s RETURNING id;", (usuario_id,))
        deletado = cur.fetchone()
        conn.commit()

        if deletado:
            return {"message": "Usuário removido com sucesso"}
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir usuário: {e}")
    finally:
        cur.close()
        conn.close()
