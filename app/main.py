# backend/app/main.py
from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, chat  # <--- 这里加上 , chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="中国软件杯 A3 项目后端", version="1.0.0")

app.include_router(auth.router)
app.include_router(chat.router) # <--- 这里也要加上

@app.get("/")
def root():
    return {"message": "后端服务已启动"}