# langgraph-learning

本仓库用于学习和整理 LangGraph 相关项目，包含：

- `projects/langgraph-dev-sample`：LangGraph Python 示例
- `projects/agent-chat-ui`：以 Git submodule 方式接入的前端项目

## 克隆与初始化

首次克隆后，请同步 submodule：

```bash
git clone https://github.com/angusoutlook/langgraph-learning.git
cd langgraph-learning
git submodule update --init --recursive
```

## 日常拉取更新

先拉主仓库，再同步 submodule 到主仓库记录的提交：

```bash
git pull
git submodule update --init --recursive
```

## 修改 submodule 的正确流程

当你修改 `projects/agent-chat-ui` 时，需要两次提交：

1. 在子模块仓库内提交并推送代码
2. 回到主仓库提交 submodule 指针更新

示例：

```bash
# 1) 子模块提交
cd projects/agent-chat-ui
git add .
git commit -m "feat: your change"
git push

# 2) 主仓库提交 submodule 指针
cd ../..
git add projects/agent-chat-ui
git commit -m "chore: bump agent-chat-ui submodule"
git push
```

## Submodule 远程说明

- `projects/agent-chat-ui` 当前指向：`https://github.com/angusoutlook/agent-chat-ui.git`
- 子模块内保留 `upstream` 指向官方仓库：`https://github.com/langchain-ai/agent-chat-ui.git`
