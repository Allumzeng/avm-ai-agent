import uvicorn
from fastapi import FastAPI
from src.webhook.handler import router

app = FastAPI(title="AVM Webhook Server")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
