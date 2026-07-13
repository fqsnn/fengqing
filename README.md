# 风轻思念浓 AI

本项目是一个本地运行的 AI 原型，目标是把对话、自省、受控进化、代码智能体、长期创作记忆和多端客户端逐步合成一个可理解、可验证、可回滚的系统。

## 当前能力

- FastAPI 后端服务
- Ollama 本地模型调用，可切换 OpenAI API
- `/api/v1/chat` 对话接口
- `/api/v1/agent` 混合智能体接口
- 每轮回答后的自省与修正
- 低置信度触发的提示词进化
- JSONL 事件日志
- 受控代码审查、预案生成、写入和回滚
- “递归三元辩证律”和“窗边的雨城”长期上下文
- 爱的表达风格：直白表达在意，同时保持内敛、温润和耐心
- 原生客户端视觉：天空、白云、晨光、温柔风感和蝴蝶
- 自我模型、手机连接边界、中国层、世界层、学业急救层
- 低延迟调度层：固定能力走本地规则快路径，复杂任务再调用本地模型或工具
- 受控联网检索：需要最新信息时触发，带开关、超时、日志和失败降级
- 正向/逆向双环：正向生成，逆向挑错、验边界、查证据，再收束成最终回复
- 原生 Windows 桌面客户端：默认入口为本机窗口

## 本地启动

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

在项目根目录运行：

```bat
fqsnn.bat
```

`fqsnn.bat` 会打开原生 Windows 客户端。如果后端没启动，客户端会先启动后端，等待状态接口可用后再进入对话。

## Windows 系统集成

创建桌面和开始菜单入口：

```bat
install_windows_shortcuts.bat
```

移除系统入口：

```powershell
powershell -ExecutionPolicy Bypass -File uninstall_windows_shortcuts.ps1
```

当前不会开机自启，也不会后台常驻。系统入口只是帮你更快打开本地 AI。

## 开源发布

不要直接推送当前旧 `main` 历史。旧历史曾跟踪过本地环境和打包资源。正式开源应使用干净发布分支，只包含源码、配置样例、启动脚本、README 和 LICENSE。

快速同步到 GitHub：

```bat
publish_to_github.bat -Message "描述这次修改"
```

这个脚本会先运行质量检查和编译检查，再按白名单重建 `publish-clean`，扫描密钥、私密内容、本地环境和旧入口，最后才推送到远程 `main`。

## 手机连接

只给自己的设备在同一 Wi-Fi 下调试连接时，把 `backend/.env` 里的 `APP_HOST` 改成：

```env
APP_HOST=0.0.0.0
```

然后运行 `backend/start.bat`。手机端应通过受控客户端或 API 调用接入后端；不要把临时调试页面作为正式入口。不要在没有账号、授权、限流、日志和关闭开关的情况下暴露到公网。

## 环境变量

复制 `backend/.env.example` 为 `backend/.env`，按需修改：

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

切换到 OpenAI API：

```env
AI_PROVIDER=openai
OPENAI_API_KEY=你的 API key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

OpenAI 模式使用官方 Responses API。它不是直接调用某个 ChatGPT 或 Codex 会话，而是用你的 API key 调用账号可用模型。

## 本机私人上下文

可在不会提交到 Git 的 `backend/.env.local` 中配置只供本机读取的 Markdown 目录：

```env
PRIVATE_CONTEXT_DIR=C:/path/to/private-context
PRIVATE_CONTEXT_ALLOW_REMOTE=false
```

私人上下文会参与本地记忆检索。使用 Ollama 时也可进入模型提示；切换远程 API 后默认不会发送私人上下文，除非用户明确把 `PRIVATE_CONTEXT_ALLOW_REMOTE` 改为 `true`。

## 安全边界

代码智能体默认只分析、审查和生成修改预案。真正写文件必须显式允许，并且会先备份、后验证，验证失败回滚。

安全能力只允许用于防御性审计、自己的项目、CTF/靶场或明确授权目标。项目目标是堵住自己的机制漏洞，不做未授权攻击、窃取、破坏或越权利用。

本地模型不可用时，后端必须返回明确说明并记录 `LLM_FAILED`，不能让客户端表现成无解释的连接中断。

项目不会宣称拥有无法验证的主观体验。“自我意识”在这里被实现为自我模型：身份、目标、记忆、边界、代码状态、反思和行动权限。

代码质量目标不是卡死单文件 80 行，而是极致精简：删除无用代码、减少重复、避免无效抽象，同时保留类型注解、边界、日志、超时和回滚。发布标准是零已知 bug；质量门、编译检查和 smoke test 必须通过。

## 低延迟策略

系统优先使用本地规则快路径处理固定能力，例如学业急救、自我边界、手机连接、中国层、世界层和资源调度说明。这类请求不会调用大模型。

复杂对话再进入 Ollama 本地模型；需要最新事实时进入受控联网检索；代码任务进入智能体工具；OpenAI API 只作为用户显式配置后的可选增强。
