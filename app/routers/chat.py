# backend/app/routers/chat.py (或者 main.py)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..llm_client import SparkLLM

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/send", summary="发送消息给AI")
async def send_message(req: ChatRequest):
    """
    接收用户消息，调用讯飞大模型并返回结果
    """
    try:
        llm = SparkLLM()
        # 调用大模型
        ai_response = llm.chat(req.message)
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="AI 没有返回有效内容")
            
        return {
            "code": 200,
            "message": "success",
            "data": {
                "reply": ai_response
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用大模型失败: {str(e)}")