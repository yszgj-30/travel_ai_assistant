import logging
import os
import traceback

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("weather")

AMAP_KEY = os.getenv("AMAP_KEY")
AMAP_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

app = FastAPI(title="天气服务 (高德地图)")


class CityRequest(BaseModel):
    city: str


@app.post("/mcp/call")
def get_weather(req: CityRequest):
    city = req.city.strip()
    logger.info(f"收到天气查询请求: city={city}")

    result = _fetch_real_weather(city)
    if result:
        logger.info(f"真实天气返回成功: {city} -> {result['weather']} {result['temp']}")
        return result

    logger.warning(f"真实天气获取失败，使用兜底数据: city={city}")
    return _fallback_weather(city)


def _fetch_real_weather(city: str) -> dict | None:
    try:
        logger.info(f"请求高德天气API: city={city}")
        resp = requests.get(
            AMAP_URL,
            params={"city": city, "key": AMAP_KEY, "extensions": "base"},
            timeout=10,
        )
        logger.info(f"高德API响应状态码: {resp.status_code}")

        data = resp.json()
        logger.info(f"高德API返回: status={data.get('status')}, infocode={data.get('infocode')}")

        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            return {
                "city": live["city"],
                "temp": f"{live['temperature']}℃",
                "weather": live["weather"],
                "wind": f"{live['winddirection']}风 {live['windpower']}级",
                "humidity": f"{live['humidity']}%",
                "reporttime": live.get("reporttime", ""),
            }
        else:
            logger.warning(f"高德API业务失败: info={data.get('info')}, infocode={data.get('infocode')}")
            return None

    except requests.Timeout:
        logger.error("高德API请求超时")
        return None
    except requests.ConnectionError:
        logger.error("高德API连接失败，请检查网络")
        return None
    except Exception:
        logger.error(f"高德API异常:\n{traceback.format_exc()}")
        return None


def _fallback_weather(city: str) -> dict:
    return {
        "city": city,
        "temp": "26℃",
        "weather": "晴",
        "wind": "微风 ≤3级",
        "humidity": "55%",
        "reporttime": "",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("启动天气服务 (高德地图 API)")
    uvicorn.run(app, host="127.0.0.1", port=8001)
