from fastapi import HTTPException
from app.utils.database import connect_db
from app.core.security import check_password, create_jwt_token
from datetime import timedelta

def authenticate_user(email_or_user: str, segredo: str):
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco")

    try:
        cur = conn.cursor()
        # Permite autenticação por email ou pelo nome
        query = "SELECT id, nome, email, senha, tipo_usuario FROM usuario WHERE email = %s OR nome = %s"
        cur.execute(query, (email_or_user, email_or_user))
        
        usuario = cur.fetchone()
        if not usuario or not check_password(segredo, usuario[3]):
            return None
        return usuario
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao autenticar: {e}")
    finally:
        cur.close()
        conn.close()

def generate_token_for_user(usuario):
    return create_jwt_token({
        "sub": str(usuario[0]),
        "email": usuario[2],
        "tipo_usuario": str(usuario[4])
    }, expires_delta=timedelta(days=1))
