import requests

# 后端 API 地址（和 api_server.py 对应）
API_URL = "http://127.0.0.1:8000/chat"


def chat_with_agent(user_input):
    try:
        # 发送请求到后端
        response = requests.post(
            API_URL,
            json={"query": user_input},
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("answer", "AI 没有返回内容")
        else:
            return f"服务异常，错误码：{response.status_code}"
    except Exception as e:
        return f"连接失败：{str(e)}"


def main():
    print("=" * 40)
    print("      智能出行 Agent 客户端")
    print("  输入 'exit' 或 'quit' 退出程序")
    print("=" * 40)

    while True:
        user_input = input("\n你：")

        # 退出条件
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("\n程序已退出！")
            break

        # 空输入过滤
        if not user_input.strip():
            print("AI：请输入有效问题~")
            continue

        # 获取回答
        reply = chat_with_agent(user_input)
        print(f"AI：{reply}")


if __name__ == "__main__":
    main()