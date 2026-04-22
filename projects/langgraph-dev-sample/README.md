# LangGraph Dev Sample

这是一个最小可运行的 LangGraph + DeepSeek（OpenAI 兼容协议）聊天机器人示例。

## 1) 安装依赖

```powershell
pip install -r requirements.txt
```

## 2) 配置环境变量

```powershell
copy .env.example .env
```

然后编辑 `.env`，填入你的 `DEEPSEEK_API_KEY`。

默认配置已经是 DeepSeek 官方 OpenAI 兼容地址：

- `OPENAI_MODEL=deepseek-chat`
- `OPENAI_BASE_URL=https://api.deepseek.com/v1`

如果你有自建网关，再把 `OPENAI_BASE_URL` 改成你的地址。

## 3) 启动开发服务

```powershell
langgraph dev
```

启动后可在 LangGraph Studio 里调用图：

- graph id: `chatbot`
- 入口状态示例：

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，介绍一下你自己"
    }
  ]
}
```
