from fastapi import FastAPI
from pydantic import BaseModel
import os

# 初始化 FastAPI 服务
app = FastAPI(title="文件写入 MCP 服务")


# 定义请求体格式
class WriteRequest(BaseModel):
    filename: str  # 文件名，例如 travel_plan.txt
    content: str  # 要写入的内容


# 写入文件接口
@app.post("/mcp/call")
async def write_to_file(req: WriteRequest):
    try:
        # 以 UTF-8 编码写入文件，防止中文乱码
        with open(req.filename, "w", encoding="utf-8") as f:
            f.write(req.content)

        return {
            "status": "success",
            "data": f"✅ 文件保存成功！\n文件名：{req.filename}\n内容已写入本地"
        }
    except Exception as e:
        return {
            "status": "error",
            "data": f"❌ 文件保存失败：{str(e)}"
        }


# 启动服务，端口 8002
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)