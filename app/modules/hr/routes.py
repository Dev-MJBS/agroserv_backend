import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from app.firebase_config import get_db
from app.core.ai_service import analyze_with_ai

router = APIRouter()

class Employee(BaseModel):
    nome: str
    cpf: str
    cargo: str
    departamento: str
    salario: float
    data_admissao: str
    status: str = "Ativo"

@router.post("/funcionarios")
async def cadastrar_funcionario(emp: Employee):
    try:
        db = get_db()
        doc_ref = db.collection("hr_funcionarios").document()
        payload = emp.dict()
        payload["created_at"] = datetime.now()
        doc_ref.set(payload)
        return {"id": doc_ref.id, "message": "Funcionário cadastrado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/funcionarios")
async def listar_funcionarios():
    try:
        db = get_db()
        docs = db.collection("hr_funcionarios").stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/funcionarios/{id}")
async def excluir_funcionario(id: str):
    try:
        db = get_db()
        db.collection("hr_funcionarios").document(id).delete()
        return {"message": "Sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analise-ia-geral")
async def analisar_equipe_ia():
    """
    Usa o Gemini Via Openrouter para analisar a estrutura da equipe.
    """
    try:
        db = get_db()
        docs = db.collection("hr_funcionarios").stream()
        funcionarios = [doc.to_dict() for doc in docs]
        
        if not funcionarios:
            return {"analise": "Nenhum funcionário cadastrado para análise."}

        resumo = json.dumps([{ "nome": f["nome"], "cargo": f["cargo"] } for f in funcionarios[:15]])
        prompt = f"Com base nos seguintes funcionários do agronegócio: {resumo}. Sugira 3 treinamentos cruciais para essa equipe este mês. Responda em PORTUGUÊS."
        
        analise = await analyze_with_ai(prompt, "Você é um consultor de RH estratégico para o agronegócio.")
        return {"analise": analise}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def hr_status():
    """
    Endpoint for testing HR module status.
    Returns a simple JSON status object.
    """
    return {
        "module": "Human Resources",
        "status": "online",
        "endpoints": [
            "/status",
            "/employees (placeholder)"
        ]
    }

@router.get("/employees")
async def get_test_employees():
    """
    Temporary endpoint returning test employees.
    """
    return [
        {"id": 1, "name": "João Silva", "role": "Supervisor de Campo"},
        {"id": 2, "name": "Maria Fernandes", "role": "Engenheira Agrônoma"}
    ]
