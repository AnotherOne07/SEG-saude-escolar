from fastapi import APIRouter, HTTPException, Depends
from app.schemas.aluno import AlunoCreate, AlunoUpdate
from app.services.student_service import (
    create_aluno, get_all_alunos, get_alunos_by_responsavel,
    get_aluno_id, update_aluno_id, delete_aluno_id
)
from app.core.security import get_current_user

router = APIRouter()

@router.post("/create_alunos")
def criar_novo_aluno(aluno: AlunoCreate):
    return create_aluno(aluno)

@router.get("/")
def listar_todos_alunos():
    return get_all_alunos()

@router.get("/responsavel/{responsavel_id}")
def listar_alunos_responsavel(responsavel_id: int):
    return get_alunos_by_responsavel(responsavel_id)

@router.get("/get_aluno/{aluno_id}")
def pegar_aluno_id(aluno_id: int):
    return get_aluno_id(aluno_id)

@router.put("/update_aluno/")
def atualizar_aluno_id(aluno: AlunoUpdate):
    return update_aluno_id(aluno)

@router.delete("/delete_aluno/{aluno_id}")
def remover_aluno_id(aluno_id: int):
    return delete_aluno_id(aluno_id)
