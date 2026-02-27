import json
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()

async def analyze_with_ai(prompt: str, system_prompt: str = "Você é um assistente de IA especialista em logística e gestão empresarial."):
    """
    Função genérica para chamar o OpenRouter usando o modelo especificado.
    """
    settings = get_settings()
    
    if not settings.OPENROUTER_API_KEY or "your_openrouter_key" in settings.OPENROUTER_API_KEY:
        # Fallback para o modo offline/mock se a chave não estiver configurada
        return "Erro: Chave do OpenRouter não configurada. Configure a variável OPENROUTER_API_KEY no painel de controle."
    
    try:
        # Inicializa o cliente dentro da função para garantir que usa as variáveis mais recentes
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )

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
