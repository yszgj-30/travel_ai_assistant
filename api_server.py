from datetime import datetime
from pathlib import Path
from typing import TypedDict
import json
import logging
import os
import re
import time
import traceback
import requests

from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from agent_prompts import AGENT_SYSTEM_PROMPT, USER_PROMPT

# ---------- 日志配置 ----------
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("travel_agent")
logger.setLevel(logging.DEBUG)

# 控制台 handler（INFO 级别，简洁）
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
logger.addHandler(ch)

# 文件 handler（DEBUG 级别，完整记录）
fh = logging.FileHandler(LOG_DIR / "api_server.log", encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(fh)

# 加载环境变量
load_dotenv()

# 文件保存根目录 & 安全校验
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def safe_path(filename: str) -> Path:
    """确保文件只能写入 ./output 目录，防止路径越权"""
    if not filename or not filename.strip():
        raise ValueError("文件名为空")
    if re.search(r"[\\/]|\.\.", filename):
        raise ValueError(f"非法文件名: {filename}")
    full = (OUTPUT_DIR / filename).resolve()
    if not str(full).startswith(str(OUTPUT_DIR.resolve())):
        raise ValueError(f"路径越权: {filename}")
    return full


def validate_city(city: str) -> str:
    """校验城市名，拒绝空值、过长、含危险字符的输入"""
    city = city.strip()
    if not city:
        raise ValueError("城市名不能为空")
    if len(city) > 50:
        raise ValueError("城市名过长")
    if re.search(r"[<>{}|\\/]", city):
        raise ValueError(f"城市名含非法字符: {city}")
    return city


def validate_query(query: str) -> str:
    """校验用户查询，拒绝空值和超长输入"""
    query = query.strip()
    if not query:
        raise ValueError("查询内容不能为空")
    if len(query) > 2000:
        raise ValueError("查询内容过长（上限2000字符）")
    return query

# 加载 MCP 服务配置
with open("servers_config.json", "r", encoding="utf-8") as f:
    MCP_CONFIG = json.load(f)

# 初始化大模型
llm = ChatOpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url=os.getenv("QWEN_ENDPOINT"),
    model=os.getenv("QWEN_MODEL", "qwen-turbo"),
    temperature=0.1
)

# 定义 Agent 状态
class AgentState(TypedDict):
    query: str
    tool: str
    args: dict
    tool_result: str
    answer: str

# 请求体
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

app = FastAPI(title="智能出行Agent服务")

# --------------------------
# 节点 1：判断意图 & 选择工具
# --------------------------
def judge_intent(state: AgentState):
    query = state["query"]
    logger.info(f"[judge] 收到查询: {query[:60]}...")

    # 天气查询 → LLM 提取城市名
    if "天气" in query:
        t0 = time.time()
        city = llm.invoke(
            f"从用户问题中提取城市名，只输出城市名，不要其他内容。\n问题：{query}"
        ).content.strip()
        logger.debug(f"[judge] LLM提取城市名: {city} (耗时 {time.time()-t0:.2f}s)")
        logger.info(f"[judge] 意图=weather, city={city}")
        return {"tool": "weather", "args": {"city": city}}

    # 文件保存 → 生成带时间戳的文件名
    if "保存" in query or "文件" in query:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{ts}.txt"
        logger.info(f"[judge] 意图=write, filename={filename}")
        return {"tool": "write", "args": {"filename": filename}}

    # 地图/路线
    if "路线" in query or "地图" in query or "去哪" in query:
        logger.info(f"[judge] 意图=amap-maps")
        return {"tool": "amap-maps", "args": {"query": query}}

    logger.info(f"[judge] 意图=chat (无工具)")
    return {"tool": None, "args": {}}

# --------------------------
# 节点 2：调用 MCP 工具
# --------------------------
def call_mcp(state: AgentState):
    tool = state["tool"]
    args = state["args"]

    logger.debug(f"[call] 工具={tool}, 参数={args}")

    if not tool:
        logger.debug("[call] 无工具，跳过")
        return {"tool_result": ""}

    try:
        if tool == "weather":
            city = validate_city(args.get("city", ""))
            logger.info(f"[call] 请求天气服务: city={city}")
            t0 = time.time()
            res = requests.post(
                "http://127.0.0.1:8001/mcp/call",
                json={"city": city},
                timeout=12,
            ).json()
            elapsed = time.time() - t0
            if res.get("city"):
                info = f"{res['city']}天气：{res['weather']}，温度{res['temp']}，{res['wind']}，湿度{res['humidity']}。{res.get('tip', '')}"
                logger.info(f"[call] 天气返回成功: {info[:60]}... (耗时 {elapsed:.2f}s)")
                return {"tool_result": info}
            else:
                logger.warning(f"[call] 天气API返回异常: {res}")
                return {"tool_result": "天气查询失败"}
        elif tool == "write":
            logger.debug("[call] 写入操作延后到 save_file 节点")
            return {"tool_result": ""}
        elif tool == "amap-maps":
            logger.info("[call] amap-maps 演示模式")
            return {"tool_result": "地图服务调用成功（演示模式）"}
        else:
            logger.warning(f"[call] 未知工具: {tool}")
            return {"tool_result": "未知工具"}
    except requests.Timeout:
        logger.error(f"[call] 天气服务请求超时 (city={args.get('city')})")
        return {"tool_result": "工具服务未启动"}
    except requests.ConnectionError:
        logger.error("[call] 天气服务连接失败")
        return {"tool_result": "工具服务未启动"}
    except Exception:
        logger.error(f"[call] 异常:\n{traceback.format_exc()}")
        return {"tool_result": "工具服务未启动"}

# --------------------------
# 节点 3：生成回答
# --------------------------
def generate_answer(state: AgentState):
    info = state["tool_result"]
    query = state["query"]
    tool = state["tool"]
    logger.debug(f"[answer] 工具结果: {info[:80] if info else '(空)'}")
    prompt = f"""
用户问题：{query}
工具结果：{info}
请自然、简洁地回答用户。
"""
    if tool == "write":
        filepath = f"./output/{state['args'].get('filename', 'note.txt')}"
        prompt += f"\n回答中必须包含一句「已成功保存到本地文件：{filepath}」。"
    t0 = time.time()
    answer = llm.invoke(prompt).content
    logger.info(f"[answer] 生成回答: {answer[:80]}... (耗时 {time.time()-t0:.2f}s)")
    return {"answer": answer}

# --------------------------
# 节点 4：保存文件
# --------------------------
def save_file(state: AgentState):
    if state["tool"] == "write":
        filename = state["args"].get("filename", "note.txt")
        logger.info(f"[save] 开始保存文件: {filename}")
        try:
            filepath = safe_path(filename)
            t0 = time.time()
            core = llm.invoke(
                f"从以下回答中提取要保存的旅行计划核心内容，去掉所有引导语和保存确认语，只保留计划本身：\n\n{state['answer']}"
            ).content.strip()
            filepath.write_text(core, encoding="utf-8")
            logger.info(f"[save] 文件已写入: {filepath} (内容长度: {len(core)}, 耗时 {time.time()-t0:.2f}s)")
        except ValueError as e:
            logger.error(f"[save] 路径校验失败: {e}")
        except Exception:
            logger.error(f"[save] 写入失败:\n{traceback.format_exc()}")
    return {}

# --------------------------
# 构建流程图
# --------------------------
builder = StateGraph(AgentState)
builder.add_node("judge", judge_intent)
builder.add_node("call", call_mcp)
builder.add_node("answer", generate_answer)
builder.add_node("save_file", save_file)

builder.add_edge(START, "judge")
builder.add_edge("judge", "call")
builder.add_edge("call", "answer")
builder.add_edge("answer", "save_file")
builder.add_edge("save_file", END)

graph = builder.compile()

# --------------------------
# API 接口
# --------------------------
@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"[api] 收到请求: {req.query[:60]}...")

    try:
        query = validate_query(req.query)
    except ValueError as e:
        logger.warning(f"[api] 输入校验失败: {e}")
        return {"answer": f"输入无效：{e}"}

    t0 = time.time()
    try:
        result = graph.invoke({
            "query": query,
            "tool": None,
            "args": {},
            "tool_result": "",
            "answer": ""
        })
        answer = result["answer"]
        logger.info(f"[api] 请求完成: {answer[:80]}... (总耗时 {time.time()-t0:.2f}s)")
        logger.debug(f"[api] 完整回答: {answer}")
        return {"answer": answer}
    except Exception:
        logger.error(f"[api] 服务异常:\n{traceback.format_exc()}")
        return {"answer": "服务内部错误，请稍后重试"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)