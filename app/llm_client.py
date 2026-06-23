# backend/app/llm_client.py
import websocket
import hashlib
import base64
import json
import time
import ssl
from urllib.parse import urlencode
from .config import XFYUN_APPID, XFYUN_API_KEY, XFYUN_API_SECRET

class SparkLLM:
    def __init__(self):
        # 初始化配置
        self.APPID = XFYUN_APPID
        self.API_KEY = XFYUN_API_KEY
        self.API_SECRET = XFYUN_API_SECRET
        self.Host = "spark-api-open.xf-yun.com"
        self.Path = "/v1/chat/completions"
        self.URL = f"wss://{self.Host}{self.Path}"

    def create_url(self):
        # 生成鉴权URL
        now = time.time()
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now))

        signature_origin = f"host: {self.Host}\ndate: {date}\nGET {self.Path} HTTP/1.1"
        signature_sha = hashlib.sha256(signature_origin.encode('utf-8')).digest()
        signature = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        params = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        return self.URL + "?" + urlencode(params)

    def chat(self, message):
        """
        调用讯飞星火大模型
        :param message: 用户输入的文本
        :return: AI 返回的文本内容
        """
        url = self.create_url()
        ws = websocket.create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})

        # 构造请求数据
        data = {
            "header": {
                "app_id": self.APPID,
                "uid": "user_123" # 随便填个用户ID
            },
            "parameter": {
                "chat": {
                    "domain": "generalv3.5", # 使用的模型版本，通用 v3.5
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "system", "content": "你是一个专业的计算机组成原理助教老师，请用通俗易懂的语言回答学生的问题。"},
                        {"role": "user", "content": message}
                    ]
                }
            }
        }

        ws.send(json.dumps(data))

        full_response = ""
        try:
            while True:
                res = json.loads(ws.recv())
                if res['header']['status'] == 2:
                    # 表示对话结束
                    break
                # 拼接AI的回复内容
                if 'text' in res['payload']['choices']['text'][0]:
                    content = res['payload']['choices']['text'][0]['content']
                    full_response += content
        except Exception as e:
            print(f"接收消息出错: {e}")
        finally:
            ws.close()

        return full_response

# 测试一下
if __name__ == "__main__":
    llm = SparkLLM()
    answer = llm.chat("什么是冯诺依曼结构？")
    print("AI回复:", answer)