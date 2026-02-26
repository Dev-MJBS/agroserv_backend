from app.main import app
import uvicorn
import os

if __name__ == "__main__":
    # Railway sets the PORT environmental variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
