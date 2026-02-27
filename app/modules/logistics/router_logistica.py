import io
import json
import pandas as pd
import pdfplumber
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Any

router = APIRouter()

def extract_dataframe_from_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Função auxiliar para ler o conteúdo do arquivo e converter em um DataFrame do Pandas.
    Suporta .csv, .xlsx e .pdf.
    """
    try:
        if filename.endswith('.csv'):
            # Tenta ler CSV, assumindo separador por vírgula ou ponto e vírgula
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
                        # Assume que a primeira linha da tabela é o cabeçalho
                        df = pd.DataFrame(table[1:], columns=table[0])
                        return df
            # Se percorreu todas as páginas e não achou tabela
            raise ValueError("Nenhuma tabela legível encontrada no PDF.")
        
        else:
            raise ValueError("Formato de arquivo não suportado. Envie .csv, .xlsx ou .pdf.")
            
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar o arquivo {filename}: {str(e)}")

def analisar_termos_com_ia(dados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Função mock que simula a chamada a uma LLM (ex: OpenAI) para encontrar 
    anomalias ou termos desconhecidos nos dados cruzados.
    """
    # Simulação: Vamos procurar por valores vazios, nulos ou palavras-chave suspeitas
    termos_suspeitos = ["desconhecido", "erro", "n/a", "null", "pendente"]
    anomalias_encontradas = []

    for item in dados:
        for coluna, valor in item.items():
            valor_str = str(valor).lower().strip()
            if valor_str in termos_suspeitos or valor_str == "none" or valor_str == "":
                anomalias_encontradas.append({
                    "coluna": coluna,
                    "valor_encontrado": valor,
                    "motivo": "Termo suspeito ou ausência de dado detectada pela IA",
                    "registro_completo": item
                })
                
    # Retorna no máximo 5 anomalias para simular um resumo da IA
    return anomalias_encontradas[:5]

@router.post("/analisar-colunas")
async def analisar_colunas(arquivo: UploadFile = File(...)):
    """
    Recebe um arquivo (.csv, .xlsx, .pdf), extrai a tabela e retorna as colunas disponíveis.
    """
    content = await arquivo.read()
    df = extract_dataframe_from_file(content, arquivo.filename)
    
    # Limpa nomes de colunas vazios ou nulos
    colunas = [str(col) for col in df.columns if pd.notna(col) and str(col).strip() != ""]
    
    if not colunas:
        raise HTTPException(status_code=400, detail="Não foi possível identificar colunas válidas no documento.")
        
    return {"colunas": colunas}

@router.post("/comparar-documentos")
async def comparar_documentos(
    arquivo_1: UploadFile = File(...),
    arquivo_2: UploadFile = File(...),
    colunas_selecionadas: str = Form(...)
):
    """
    Recebe dois arquivos e uma string JSON com as colunas a serem comparadas.
    Cruza os dados e retorna o que confere, o que falta em cada um e anomalias (IA).
    """
    try:
        colunas = json.loads(colunas_selecionadas)
        if not isinstance(colunas, list) or len(colunas) == 0:
            raise ValueError("A lista de colunas selecionadas está vazia ou inválida.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="O campo 'colunas_selecionadas' deve ser um JSON válido (ex: [\"Placa\", \"Motorista\"]).")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Lê os arquivos
    content_1 = await arquivo_1.read()
    content_2 = await arquivo_2.read()

    df1 = extract_dataframe_from_file(content_1, arquivo_1.filename)
    df2 = extract_dataframe_from_file(content_2, arquivo_2.filename)

    # Verifica se as colunas selecionadas existem em ambos os arquivos
    missing_in_1 = [col for col in colunas if col not in df1.columns]
    missing_in_2 = [col for col in colunas if col not in df2.columns]

    if missing_in_1 or missing_in_2:
        erro_msg = []
        if missing_in_1: erro_msg.append(f"Colunas faltando no Arquivo 1: {missing_in_1}")
        if missing_in_2: erro_msg.append(f"Colunas faltando no Arquivo 2: {missing_in_2}")
        raise HTTPException(status_code=400, detail=" | ".join(erro_msg))

    # Filtra apenas as colunas selecionadas e remove linhas totalmente vazias
    df1_subset = df1[colunas].dropna(how='all').fillna("")
    df2_subset = df2[colunas].dropna(how='all').fillna("")

    # Converte para lista de dicionários
    records1 = df1_subset.to_dict(orient='records')
    records2 = df2_subset.to_dict(orient='records')

    # Para comparar, convertemos os dicionários em tuplas de itens (que são hasheáveis)
    # Convertendo tudo para string para evitar problemas de tipagem (ex: int vs float)
    set1 = set(tuple((k, str(v).strip()) for k, v in row.items()) for row in records1)
    set2 = set(tuple((k, str(v).strip()) for k, v in row.items()) for row in records2)

    # Operações de conjunto para encontrar interseções e diferenças
    conferem_tuples = set1.intersection(set2)
    faltam_no_1_tuples = set2 - set1
    faltam_no_2_tuples = set1 - set2

    # Reconverte para dicionários
    conferem = [dict(t) for t in conferem_tuples]
    faltam_no_1 = [dict(t) for t in faltam_no_1_tuples]
    faltam_no_2 = [dict(t) for t in faltam_no_2_tuples]

    # Simula a análise de IA nos dados que não bateram (diferenças)
    dados_para_ia = faltam_no_1 + faltam_no_2
    termos_desconhecidos = analisar_termos_com_ia(dados_para_ia)

    return {
        "resumo": {
            "total_conferem": len(conferem),
            "total_faltam_no_arquivo_1": len(faltam_no_1),
            "total_faltam_no_arquivo_2": len(faltam_no_2)
        },
        "conferem": conferem,
        "faltam_no_arquivo_1": faltam_no_1,
        "faltam_no_arquivo_2": faltam_no_2,
        "termos_desconhecidos": termos_desconhecidos
    }
