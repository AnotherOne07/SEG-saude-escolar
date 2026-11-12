from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_services import authenticate_user, generate_token_for_user
from app.core.security import get_current_user

router = APIRouter()

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = authenticate_user(form_data.username, form_data.password)
    if not usuario: 
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
    
    token = generate_token_for_user(usuario)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": usuario[0],
            "nome": usuario[1],
            "email": usuario[2],
            "tipo_usuario": usuario[4]
        }
    }

@router.get("/me")
def obter_usuario_logado(current_user: dict = Depends(get_current_user)):
    return current_user
