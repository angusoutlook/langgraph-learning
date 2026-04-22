import os
from typing import Any
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_tavily._utilities import TavilySearchAPIWrapper
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

load_dotenv(override=True)
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("缺少 TAVILY_API_KEY，请先在 .env 中配置。")

search_tool = TavilySearch(
    max_results=5,
    topic="general",
    api_wrapper=TavilySearchAPIWrapper(tavily_api_key=tavily_api_key),
)

class WeatherRequest(BaseModel):
    loc: str = Field(..., min_length=1, description="城市名称，例如 Beijing")


class WeatherResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    weather: list[dict[str, Any]] = Field(default_factory=list)
    main: dict[str, Any] = Field(default_factory=dict)
    wind: dict[str, Any] = Field(default_factory=dict)
    coord: dict[str, Any] = Field(default_factory=dict)

@tool(args_schema = WeatherRequest)
def get_weather(loc):
    """根据城市名称查询当前天气信息。"""
    import requests

    req = WeatherRequest(loc=loc)
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"
    weather_url = "https://cn-api.openweathermap.org/data/2.5/weather"
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"ok": False, "error": "缺少 OPENWEATHER_API_KEY，请先在 .env 中配置。"}
    try:
        geo_params = {
            "q": req.loc,
            "limit": 1,
            "appid": api_key,
        }
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        geo_response.raise_for_status()
        geo_items = geo_response.json()
        if not geo_items:
            return {
                "ok": False,
                "error": f"未找到城市“{req.loc}”对应的经纬度。",
            }

        lat = geo_items[0].get("lat")
        lon = geo_items[0].get("lon")
        if lat is None or lon is None:
            return {"ok": False, "error": f"城市“{req.loc}”经纬度数据不完整。"}

        weather_params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "zh_cn",
        }
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        return WeatherResponse.model_validate(weather_response.json()).model_dump()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else None
        if status_code == 401:
            return {
                "ok": False,
                "error": "天气服务鉴权失败(401)。请检查或更换 OPENWEATHER_API_KEY。",
            }
        return {
            "ok": False,
            "error": f"天气服务请求失败，HTTP {status_code}。城市: {req.loc}",
        }
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"天气服务连接异常：{e}"}


class Write_Query(BaseModel):
    query: str = Field(..., description="需要写入文档的具体内容")

@tool(args_schema = Write_Query)
def write_file(query : str) -> str:
    """写入文档的具体内容。
    :param content: 需要写入文档的具体内容
    :return: 是否写入成功呢
    """
    from datetime import datetime
    from pathlib import Path

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"weather_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    file_path.write_text(query, encoding="utf-8")
    return f"写入成功：{file_path.as_posix()}"


tools = [search_tool, get_weather, write_file]

model = init_chat_model(model="deepseek-chat",model_provider="deepseek")
agent = create_agent(
    model = model,
    tools = tools,
    debug = False,
)
graph = agent

if __name__ == "__main__":
    config = {
        "recursion_limit": 25,
        "configurable": {"thread_id": "cli-demo-thread"},
    }
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "中国现在那个省会城市最热？"}]},
        config,
    )
    print("\n===== 第一轮调用链路完整输出 =====")
    for idx, msg in enumerate(response["messages"], start=1):
        print(f"\n--- 第{idx}条消息 ---")
        print(f"类型: {type(msg).__name__}")
        if hasattr(msg, "content"):
            print(f"内容: {msg.content}")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"工具调用: {msg.tool_calls}")
        if hasattr(msg, "name") and msg.name:
            print(f"工具名: {msg.name}")
        if hasattr(msg, "tool_call_id") and msg.tool_call_id:
            print(f"工具调用ID: {msg.tool_call_id}")

    follow_up = agent.invoke(
        {"messages": [{"role": "user", "content": "请基于刚才结论，给出前三名并简述原因。"}]},
        config,
    )
    print("\n===== 第二轮最终回复（同一 thread_id 验证记忆） =====")
    print(follow_up["messages"][-1].content)

    new_config = {
        "recursion_limit": 25,
        "configurable": {"thread_id": "cli-demo-thread-2"},
    }
    third_round = agent.invoke(
        {"messages": [{"role": "user", "content": "继续上面的结论，再补充前三名的体感温度。"}]},
        new_config,
    )
    print("\n===== 第三轮最终回复（新 config / 新 thread_id） =====")
    print(third_round["messages"][-1].content)
    third_text = third_round["messages"][-1].content or ""
    # 仅检查前两轮结果里的特有实体，避免“前三名”这类通用词导致假阳性。
    memory_entities = ("南宁", "海口", "广州")
    matched_entities = [city for city in memory_entities if city in third_text]
    has_memory_hint = len(matched_entities) > 0
    print(f"第三轮是否疑似引用前文: {has_memory_hint}")
    print(f"第三轮命中的前文城市: {matched_entities if matched_entities else '无'}")
