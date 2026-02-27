import json
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

async def analyze_with_ai(prompt: str, system_prompt: str = "Você é um assistente de IA especialista em logística e gestão empresarial."):
    """
    Função genérica para chamar o OpenRouter usando o modelo especificado.
    """
    if not settings.OPENROUTER_API_KEY:
        # Fallback para o modo offline/mock se a chave não estiver configurada
        return {"error": "Chave OpenRouter não configurada. Ative-a no .env para análise real."}
    
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": settings.OPENROUTER_REFERER,
                "X-Title": settings.OPENROUTER_TITLE,
            },
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Erro na chamada OpenRouter: {str(e)}")
        return f"Erro na análise de IA: {str(e)}"
