import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.database import connect_db
import jwt

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    pwd_context = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/site/login")

SECRET_KEY = "chave-super-secreta-saude-escolar"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

def hash_senha(senha: str) -> str:
    if pwd_context:
        try:
            return pwd_context.hash(senha)
        except Exception:
            pass
    # Fallback SHA-256 caso backend bcrypt não esteja instalado no host
    return "sha256$" + hashlib.sha256(senha.encode("utf-8")).hexdigest()

def check_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    # Suporte a texto puro para dados de seed rápido
    if password == hashed_password:
        return True
    if hashed_password.startswith("sha256$"):
        return ("sha256$" + hashlib.sha256(password.encode("utf-8")).hexdigest()) == hashed_password
    if pwd_context:
        try:
            return pwd_context.verify(password, hashed_password)
        except Exception:
            return False
    return False

def create_jwt_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Erro de autenticação: {e}")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token_jwt(token)
    usuario_id = payload.get("sub")

    if usuario_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")
    
    conn = connect_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro ao conectar com o banco de dados")
    
    try:
        cur = conn.cursor()
        query = "SELECT id, nome, email, tipo_usuario FROM usuario WHERE id = %s"
        cur.execute(query, (int(usuario_id),))
        usuario = cur.fetchone()

        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return {
            "id": usuario[0],
            "nome": usuario[1],
            "email": usuario[2],
            "tipo_usuario": usuario[3]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao identificar usuário: {e}")
    finally:
        cur.close()
        conn.close()
