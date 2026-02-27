import json
import google.generativeai as genai
from app.core.config import get_settings

def analyze_with_ai_sync(prompt: str, system_prompt: str = "Você é um assistente de IA especialista em logística e gestão empresarial. SEMPRE use formatação Markdown rica (títulos ##, listas - e negritos **) para organizar a resposta de forma elegante e profissional."):
    """
    Função para chamar o Google Gemini Studio API.
    """
    settings = get_settings()
    
    if not settings.GEMINI_API_KEY:
        return "Erro: Chave do Gemini Studio não configurada."

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_prompt
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro na chamada Gemini: {str(e)}")
        return f"Erro na análise de IA: {str(e)}"

async def analyze_with_ai(prompt: str, system_prompt: str = "Você é um assistente de IA especialista em logística e gestão empresarial."):
    """
    Wrapper assíncrono para manter compatibilidade com o restante do código.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyze_with_ai_sync, prompt, system_prompt)
