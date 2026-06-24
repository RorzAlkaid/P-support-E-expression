# 大学生心理支持与情绪表达平台

基于 Django + Django REST framework + Vue 3 + Vite 的校园心理健康服务平台。项目面向学生、心理教师和管理员，提供心理资源浏览、情绪打卡、匿名树洞、心理测评、咨询预约、风险预警、AI 倾听、数据洞察和后台管理等功能。

## 功能概览

- 公开首页：以网站形式展示平台能力，包含功能入口、登录入口、注册入口、数据洞察展示和 AI 倾听展示。
- 账号与角色：支持学生、心理教师、管理员角色；登录和注册入口按学生、教师、管理员细分，避免不同身份混用入口。
- 注册安全：教师和管理员注册必须使用对应邀请码；邀请码由管理员或教师在个人资料中生成或手动维护，学生注册不需要邀请码。
- 一次性邀请码：邀请码只有在锁定且未使用时有效；被用于一次注册后自动失效，解锁期间无效，再次锁定同一邀请码后恢复一次使用机会。
- 个人资料：学生可维护基础资料与偏好主题；教师可维护职称、咨询方向、资质说明、可预约时段和教师邀请码；管理员可维护教师邀请码和管理员邀请码。
- 心理资源：展示心理科普文章，记录学生资源浏览行为，支持同步外部公开心理资源。
- 情绪打卡：记录心情、强度、睡眠质量、压力来源和日记内容，并生成趋势数据。
- 匿名树洞：支持匿名发布、回复和教师回应，高风险表达会触发预警标记。
- 心理测评：根据量表答题生成分数、风险等级和建议。
- 咨询预约：学生提交预约，教师或管理员可查看并处理预约状态。
- 风险预警：根据低情绪、高风险文本和高风险测评生成预警，教师和管理员可查看学生详情。
- AI 倾听：接入兼容 OpenAI Chat Completions 格式的服务，支持管理员配置接口、模型和 Key；前端提供文本对话和浏览器语音转文字输入。
- 数据洞察：汇总学生、情绪、测评、预警、预约等数据，支持图表展示和 CSV / XLSX 导出。
- 后台管理：使用 Django Admin + SimpleUI 管理用户、学生档案、咨询师、文章、量表、预警和 AI 配置。

## 技术栈

后端：

- Python 3.11+
- Django 5.2
- Django REST framework
- django-cors-headers
- django-simpleui
- SQLite

前端：

- Vue 3
- Vite
- Axios
- ECharts
- Pinia
- Vue Router

## 目录结构

```text
P-support-E-expression/
├─ backend/
│  ├─ config/
│  ├─ wellness/
│  │  ├─ management/commands/
│  │  │  ├─ seed_demo.py
│  │  │  ├─ sync_authoritative_counselors.py
│  │  │  └─ sync_authoritative_resources.py
│  │  ├─ migrations/
│  │  ├─ admin.py
│  │  ├─ models.py
│  │  ├─ serializers.py
│  │  ├─ urls.py
│  │  └─ views.py
│  └─ manage.py
├─ frontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ assets/
│  │  ├─ App.vue
│  │  ├─ main.js
│  │  └─ style.css
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ scripts/
│  ├─ setup_daily_counselor_sync.ps1
│  └─ setup_daily_resource_sync.ps1
├─ requirements.txt
└─ README.md
```

本地虚拟环境、`node_modules`、构建产物、日志文件、SQLite 数据库和 AI Key 配置文件不应提交到仓库，已通过 `.gitignore` 忽略。

## 后端运行

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

后端地址：

```text
http://127.0.0.1:8000/
```

后台管理地址：

```text
http://127.0.0.1:8000/admin/
```

DRF 调试接口地址：

```text
http://127.0.0.1:8000/api/
```

`/api/` 是 Django REST framework 提供的接口调试页面，不是最终用户使用的 Vue 前台页面。前端依赖实际 `/api/...` 接口，删除接口路由会影响项目功能。

## 前端运行

```powershell
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173/
```

生产构建：

```powershell
cd frontend
npm run build
```

## AI 倾听配置

AI 倾听接口默认使用兼容 OpenAI Chat Completions 的请求格式。可以通过环境变量或管理员页面配置：

```powershell
$env:AI_CHAT_API_URL="https://api.openai.com/v1/chat/completions"
$env:AI_CHAT_API_KEY="your-api-key"
$env:AI_CHAT_MODEL="gpt-4o-mini"
$env:AI_CHAT_TIMEOUT="30"
```

也可以登录管理员账号后，在前端 `AI 倾听对话` 页面保存 API Key、接口地址、模型和超时时间。DeepSeek 兼容接口请填写 `/chat/completions`，不要填写 `/anthropic`。

## 账号注册与邀请码

平台登录和注册入口按身份拆分：

- 学生入口：学生账号直接注册，不需要邀请码。
- 教师入口：教师注册必须填写有效的教师邀请码。
- 管理员入口：管理员入口以较小文字显示，管理员注册必须填写有效的管理员邀请码。

邀请码维护规则：

- 管理员可在个人资料中维护两个邀请码：教师邀请码、管理员邀请码。
- 教师可维护教师邀请码，不能维护管理员邀请码。
- 邀请码可以随机生成，也可以手动输入。随机生成时为 16 位随机字符；手动输入不限制长度。
- 点击锁图标会锁定邀请码并复制到粘贴板；锁定状态下邀请码输入框变暗且不可编辑。
- 点击已锁定的锁图标会解锁，解锁后该邀请码立刻失效，可重新编辑。
- 已锁定的邀请码可通过左键或右键复制，复制时会在鼠标上方显示小型提示浮窗。
- 邀请码是一次性的：被用于一次教师或管理员注册后会自动失效。只有解锁后再次锁定，才会重新获得一次注册机会。

## 常用接口

- `GET /api/health/`：服务健康检查。
- `POST /api/auth/register/`：注册账号。
- `POST /api/auth/login/`：登录账号。
- `GET/PATCH /api/auth/profile/`：读取或更新个人资料。
- `GET/POST /api/auth/invitations/`：读取、锁定或解锁当前账号可维护的邀请码。
- `GET /api/modules/`：模块中心数据。
- `POST /api/modules/moods/`：提交情绪打卡。
- `POST /api/modules/treeholes/`：发布匿名树洞。
- `POST /api/modules/assessments/`：提交心理测评。
- `POST /api/modules/appointments/`：提交咨询预约。
- `GET /api/insights/`：读取数据洞察。
- `GET /api/export-insights/csv/`：导出 CSV。
- `GET /api/export-insights/xlsx/`：导出 XLSX。
- `GET/PATCH /api/ai-chat/config/`：读取或保存 AI 倾听配置。
- `POST /api/ai-chat/`：发送 AI 倾听消息。

## 常用命令

后端检查：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py check
```

同步心理科普资源：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py sync_authoritative_resources --force
```

同步咨询师数据：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py sync_authoritative_counselors --force
```

注册每日同步计划任务：

```powershell
.\scripts\setup_daily_resource_sync.ps1
.\scripts\setup_daily_counselor_sync.ps1
```

## 数据库说明

开发环境默认使用 SQLite：

```text
backend/db.sqlite3
```

如果使用 Navicat 连接，选择 SQLite 连接类型并选中该文件即可。SQLite 本地文件模式没有数据库账号和密码。

## 部署提示

- 部署前需要关闭 `DEBUG`，配置正式 `SECRET_KEY` 和 `ALLOWED_HOSTS`。
- 根据实际环境替换 SQLite 为 MySQL、PostgreSQL 等数据库时，需要同步调整 Django 数据库配置。
- 生产环境建议将 AI Key、`SECRET_KEY` 等敏感配置放入环境变量或安全配置服务，不要写入代码仓库。
- 爬虫同步数据来自公开网页，仅用于课程设计、毕业设计或原型演示场景。
