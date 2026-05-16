import requests

# 后端接口地址
BASE_URL = "http://127.0.0.1:8000/chat"

# 单次对话调用函数
def single_chat(text):
    try:
        res = requests.post(BASE_URL, json={"query": text}, timeout=10)
        return res.json()["answer"]
    except Exception as e:
        return f"调用失败：{e}"

if __name__ == "__main__":
    print("===== 简易单次调用测试 =====")
    # 测试示例1
    print("\n1. 查询天气：")
    print(single_chat("长沙今天天气"))

    # 测试示例2
    print("\n2. 保存行程：")
    print(single_chat("把五一出游计划保存到文件"))

    # 测试示例3
    print("\n3. 日常问答：")
    print(single_chat("介绍一下智能出行助手"))