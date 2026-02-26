# RH_Agroserv ERP Backend

Backend para o Sistema ERP Agroserv desenvolvido com FastAPI e Firebase.

## Stack Técnica

- **Framework:** FastAPI
- **Banco de Dados:** Firestore (Firebase)
- **Autenticação:** Firebase Auth
- **Hospedagem:** Railway

## Estrutura de Diretórios

A estrutura é baseada em **módulos/domínios** para garantir escalabilidade:

```text
app/
├── core/               # Configurações globais e segurança
├── modules/            # Módulos de negócio
│   ├── finance/        # Financeiro
│   ├── hr/             # Recursos Humanos
│   └── logistics/      # Logística
├── utils/              # Funções utilitárias
├── firebase_config.py  # Inicialização do Firebase Admin SDK
└── main.py             # Ponto de entrada da aplicação
```

## Configuração Local

1.  **Criar ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # ou
    venv\Scripts\activate  # Windows
    ```

2.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Variáveis de Ambiente:**
    - Copie o arquivo `.env.example` para `.env`.
    - Preencha com as credenciais do seu projeto Firebase (Service Account).

4.  **Executar o servidor:**
    ```bash
    uvicorn app.main:app --reload
    ```

O servidor estará disponível em `http://localhost:8000`. A documentação interativa (Swagger) pode ser acessada em `http://localhost:8000/docs`.

## Deployment (Railway)

O projeto está configurado para ser detectado automaticamente pelo Railway. Certifique-se de configurar as variáveis de ambiente (as mesmas do `.env`) no dashboard do Railway.
