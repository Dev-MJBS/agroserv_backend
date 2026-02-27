import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from app.firebase_config import get_db
from app.core.ai_service import analyze_with_ai

router = APIRouter()

class Movimentacao(BaseModel):
    tipo: str # Entrada ou Saida
    valor: float
    descricao: str
    categoria: str # Insumos, Salários, Venda, etc.
    data: str

@router.post("/movimentacoes")
async def cadastrar_movimentacao(m: Movimentacao):
    try:
        db = get_db()
        doc_ref = db.collection("finance_movimentacoes").document()
        payload = m.dict()
        payload["created_at"] = datetime.now()
        doc_ref.set(payload)
        return {"id": doc_ref.id, "message": "Movimentação financeira cadastrada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movimentacoes")
async def listar_movimentacoes():
    try:
        db = get_db()
        docs = db.collection("finance_movimentacoes").order_by("created_at", direction="DESCENDING").stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analise-fluxo-ia")
async def analisar_fluxo_ia():
    """
    Usa o OpenRouter + Gemini para analisar o fluxo financeiro.
    """
    try:
        db = get_db()
        docs = db.collection("finance_movimentacoes").limit(50).stream()
        movs = [doc.to_dict() for doc in docs]
        
        if not movs:
            return {"analise": "Sem dados financeiros o suficiente para análise."}

        # Compactamos para o prompt
        resumo = json.dumps([{ "tipo": m["tipo"], "valor": m["valor"], "cat": m["categoria"] } for m in movs])
        prompt = f"Com base nessas movimentações financeiras: {resumo}. Dê 2 dicas práticas para reduzir custos ou aumentar a margem no agronegócio este trimestre. Responda em PORTUGUÊS."
        
        analise = await analyze_with_ai(prompt, "Você é um CFO de uma grande empresa do agronegócio brasileiro.")
        return {"analise": analise}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def finance_status():
    """
    Endpoint for testing Finance module status.
    """
    return {"module": "Finance", "status": "online", "endpoints": ["/status", "/movimentacoes", "/analise-fluxo-ia"]}
