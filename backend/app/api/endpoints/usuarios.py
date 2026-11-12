from fastapi import APIRouter, Depends
from app.schemas.usuario import UserCreate, UserUpdate
from app.services.user_services import create_user, get_usuario, get_professores, get_usuario_id, update_user, delete_user
from app.core.security import get_current_user

router = APIRouter()

@router.post("/create")
def criar_novo_usuario(user: UserCreate):
    return create_user(user)

@router.get("/")
def listar_usuarios():
    return get_usuario()

@router.get("/professores")
def listar_professores():
    return get_professores()

@router.get("/get/{usuario_id}")
def pegar_usuario(usuario_id: int):
    return get_usuario_id(usuario_id)

@router.post("/update", dependencies=[Depends(get_current_user)])
def atualizar_usuario(user: UserUpdate):
    return update_user(user)

@router.delete("/delete/{usuario_id}", dependencies=[Depends(get_current_user)])
def deletar_usuario(usuario_id: int):
    return delete_user(usuario_id)
