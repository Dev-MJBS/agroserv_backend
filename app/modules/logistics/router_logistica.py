import io
import json
import pandas as pd
import pdfplumber
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from app.firebase_config import get_db
from app.core.ai_service import analyze_with_ai
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

router = APIRouter()

# Schema para salvar e exportar comparações
class ComparacaoSave(BaseModel):
    nome: str
    resumo: Dict[str, Any]
    conferem: List[Dict[str, Any]]
    faltam_no_arquivo_1: List[Dict[str, Any]]
    faltam_no_arquivo_2: List[Dict[str, Any]]
    termos_desconhecidos: Optional[List[Dict[str, Any]]] = []
    analise_ia: Optional[str] = ""

def extract_dataframe_from_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Função auxiliar para ler o conteúdo do arquivo e converter em um DataFrame do Pandas.
    """
    try:
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(io.BytesIO(file_content))
            except Exception:
                df = pd.read_csv(io.BytesIO(file_content), sep=';')
            return df
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            return df
        elif filename.endswith('.pdf'):
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        return df
            raise ValueError("Nenhuma tabela legível encontrada no PDF.")
        else:
            raise ValueError("Formato não suportado. Use .csv, .xlsx ou .pdf.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar {filename}: {str(e)}")

async def analisar_termos_com_ia(dados_faltantes: List[Dict[str, Any]], mapeamento: List[Dict[str, Any]] = None) -> str:
    """
    Usa o OpenRouter + Gemini para uma análise detalhada dos itens faltantes,
    considerando instruções personalizadas por coluna (Mapeamento Inteligente).
    """
    if not dados_faltantes:
        return "Nenhum dado faltante para análise."

    # Incorpora instruções customizadas do usuário no prompt
    instrucoes_custom = ""
    if mapeamento:
        for m in mapeamento:
            if m.get("prompt"):
                instrucoes_custom += f"- Na coluna '{m['col1']}', considere esta regra: {m['prompt']}\n"

    # Criamos um prompt compacto para o modelo
    resumo_amostra = json.dumps(dados_faltantes[:12], indent=2, ensure_ascii=False)
    
    prompt = f"""
    Como especialista em logística agrícola, analise estas divergências entre dois documentos:
    
    {instrucoes_custom if instrucoes_custom else "Não há instruções customizadas para as colunas."}

    Amostra de registros que NÃO conferem:
    {resumo_amostra}
    
    TAREFA:
    1. Identifique se as divergências são erros reais ou se sua regra de instrução explica a diferença (ex: conversão de unidades).
    2. Resuma o que o gestor deve fazer (Ignorar, Corrigir ou Auditar).
    3. Seja direto e use tom profissional.
    Responda em PORTUGUÊS.
    """
    
    system_prompt = "Você é o assistente inteligente do Agroserv ERP, especialista em auditoria logística e análise de dados agrícolas."
    
    return await analyze_with_ai(prompt, system_prompt)

@router.post("/analisar-colunas")
async def analisar_colunas(arquivo: UploadFile = File(...)):
    content = await arquivo.read()
    df = extract_dataframe_from_file(content, arquivo.filename)
    colunas = [str(col) for col in df.columns if pd.notna(col) and str(col).strip()]
    return {"colunas": colunas}

@router.post("/comparar-documentos")
async def comparar_documentos(
    arquivo_1: UploadFile = File(...),
    arquivo_2: UploadFile = File(None),
    mapeamento: str = Form(...)
):
    """
    Recebe dois arquivos e um mapeamento JSON de colunas entre eles.
    """
    try:
        mapping_list = json.loads(mapeamento)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail={"code": "LOG-ERR-MAPPING-JSON", "message": f"O JSON do mapeamento é inválido: {str(e)}"}
        )

    try:
        content_1 = await arquivo_1.read()
        df1 = extract_dataframe_from_file(content_1, arquivo_1.filename)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail={"code": "LOG-ERR-FILE-1-READ", "message": f"Erro ao ler Arquivo 1: {str(e)}"}
        )
    
    try:
        if arquivo_2:
            content_2 = await arquivo_2.read()
            df2 = extract_dataframe_from_file(content_2, arquivo_2.filename)
        else:
            df2 = df1.copy()
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail={"code": "LOG-ERR-FILE-2-READ", "message": f"Erro ao ler Arquivo 2: {str(e)}"}
        )

    try:
        cols_1 = [m['col1'] for m in mapping_list]
        cols_2 = [m['col2'] for m in mapping_list]

        # Verifica se colunas existem
        missing_1 = [c for c in cols_1 if c not in df1.columns]
        missing_2 = [c for c in cols_2 if c not in df2.columns]
        
        if missing_1:
            raise ValueError(f"Colunas não encontradas no Arquivo 1: {missing_1}")
        if missing_2:
            raise ValueError(f"Colunas não encontradas no Arquivo 2: {missing_2}")

        df1_subset = df1[cols_1].fillna("").astype(str).apply(lambda x: x.str.strip())
        df2_subset = df2[cols_2].fillna("").astype(str).apply(lambda x: x.str.strip())

        rename_dict = {m['col2']: m['col1'] for m in mapping_list}
        df2_renamed = df2_subset.rename(columns=rename_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail={"code": "LOG-ERR-MAPPING-COLS", "message": str(e)}
        )

    set1 = set(tuple(row) for row in df1_subset.itertuples(index=False, name=None))
    set2 = set(tuple(row) for row in df2_renamed.itertuples(index=False, name=None))

    conferem_tuples = set1.intersection(set2)
    faltam_no_1_tuples = set2 - set1
    faltam_no_2_tuples = set1 - set2

    def to_dict_list(tuples, keys):
        return [dict(zip(keys, t)) for t in tuples]

    conferem = to_dict_list(conferem_tuples, cols_1)
    faltam_no_1 = to_dict_list(faltam_no_1_tuples, cols_1)
    faltam_no_2 = to_dict_list(faltam_no_2_tuples, cols_1)

    # Chamada real para o OpenRouter (Async) com mapeamento inteligente
    analise_ia = await analisar_termos_com_ia(faltam_no_1 + faltam_no_2, mapping_list)

    return {
        "resumo": {
            "total_conferem": len(conferem),
            "total_faltam_no_arquivo_1": len(faltam_no_1),
            "total_faltam_no_arquivo_2": len(faltam_no_2)
        },
        "conferem": conferem,
        "faltam_no_arquivo_1": faltam_no_1,
        "faltam_no_arquivo_2": faltam_no_2,
        "termos_desconhecidos": [], 
        "analise_ia": analise_ia
    }

@router.post("/salvar")
async def salvar_comparacao(data: ComparacaoSave):
    try:
        db = get_db()
        doc_ref = db.collection("logistica_comparacoes").document()
        payload = data.dict()
        payload["created_at"] = datetime.now()
        doc_ref.set(payload)
        return {"id": doc_ref.id, "message": "Comparação salva com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historico")
async def listar_comparacoes():
    try:
        db = get_db()
        docs = db.collection("logistica_comparacoes").order_by("created_at", direction="DESCENDING").stream()
        return [{**doc.to_dict(), "id": doc.id, "created_at": doc.to_dict()["created_at"].isoformat()} for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/excluir/{id}")
async def excluir_comparacao(id: str):
    try:
        db = get_db()
        db.collection("logistica_comparacoes").document(id).delete()
        return {"message": "Sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exportar-pdf")
async def exportar_pdf(data: ComparacaoSave):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Relatório de Logística - {data.nome}", styles["Title"]))
    elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    resumo_data = [
        ["Categoria", "Quantidade"],
        ["Itens que Conferem", data.resumo['total_conferem']],
        ["Faltam no Arquivo 1", data.resumo['total_faltam_no_arquivo_1']],
        ["Faltam no Arquivo 2", data.resumo['total_faltam_no_arquivo_2']]
    ]
    t = Table(resumo_data, colWidths=[200, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    
    if data.analise_ia:
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Análise Inteligente (IA)", styles["Heading2"]))
        elements.append(Paragraph(data.analise_ia, styles["Normal"]))

    if data.termos_desconhecidos:
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Alertas da IA", styles["Heading2"]))
        for a in data.termos_desconhecidos:
            elements.append(Paragraph(f"<b>{a['coluna']}:</b> {a['valor_encontrado']} - {a['motivo']}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(buffer, headers={'Content-Disposition': 'attachment; filename="relatorio.pdf"'}, media_type="application/pdf")
