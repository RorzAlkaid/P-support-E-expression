# 大学生心理支持与情绪表达平台 — 心晴校园

基于 Django + Django REST framework + Vue 3 + Vite 的校园心理健康服务平台。面向学生、心理教师和管理员，提供情绪打卡、匿名树洞、心理测评、咨询预约、心理资源、AI 倾听、数据洞察、风险预警和后台管理等一体化功能。

## 功能总览

### 用户端
- **情绪打卡** — 记录每日情绪、强度、睡眠质量、压力来源和私密日记，自动生成趋势图表
- **匿名树洞** — 匿名发布倾诉内容，支持同伴回应和咨询师回应；点击帖子进入详情页查看完整内容与回复墙
- **AI 倾听** — 接入兼容 OpenAI Chat Completions 的大模型，提供即时对话陪伴、情绪梳理和自助建议；支持浏览器语音转文字输入
- **心理测评** — 通过量表自评生成得分、风险等级和分层建议
- **咨询预约** — 按咨询师、时间和主题提交预约，查看预约状态
- **心理资源** — 浏览心理科普文章，支持按标签/标题/分类搜索，记录浏览行为

### 教师端
- 查看情绪打卡、测评记录、树洞内容和预约队列
- 维护个人咨询师资料（职称、擅长领域、可预约时段）
- 管理教师邀请码
- 查看和处理危机预警，查看预警学生完整数据详情

### 管理员端
- 将任意学生添加为咨询师（选择学生 → 填写资料 → 一键创建）
- 维护教师和管理员邀请码
- 管理全部数据（文章、咨询师、量表、预约、预警等）
- 配置 AI 倾听服务（API Key、接口地址、模型）
- 查看数据洞察看板并导出 CSV / Excel
- 进入 Django Admin 后台（SimpleUI）

### 标签系统
- 咨询师擅长领域和文章均可添加标签
- 点击 `+` 弹出浮动窗口：展示已有标签（前 5 个 + `...` 展开），也可输入新标签名
- 学生提交的新标签需教师/管理员审核后生效；教师和管理员直接生效
- `sync_tags` 命令将已有 JSON 标签同步到 Tag 表

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Django 5.2 + Django REST Framework 3.17 |
| 数据库 | SQLite（开发环境） |
| 后台管理 | Django Admin + SimpleUI |
| 跨域 | django-cors-headers |
| 前端框架 | Vue 3（Composition API） |
| 构建工具 | Vite 8 |
| HTTP 客户端 | Axios |
| 图表 | ECharts 6 |
| 语音识别 | Web Speech API（浏览器内置） |

## 目录结构

```text
P-support-E-expression/
├── backend/
│   ├── config/              # Django 项目配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── wellness/            # 主应用
│   │   ├── management/commands/
│   │   │   ├── seed_demo.py                     # 演示数据
│   │   │   ├── sync_authoritative_counselors.py # 同步咨询师
│   │   │   ├── sync_authoritative_resources.py  # 同步心理资源
│   │   │   └── sync_tags.py                     # 同步标签
│   │   ├── migrations/      # 数据库迁移
│   │   ├── admin.py         # Django Admin 配置
│   │   ├── models.py        # 数据模型（18 个模型）
│   │   ├── serializers.py   # DRF 序列化器
│   │   ├── urls.py          # API 路由
│   │   └── views.py         # 业务逻辑
│   ├── db.sqlite3           # SQLite 数据库
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── assets/          # 图片、Logo
│   │   ├── App.vue          # 单文件全应用（~3300 行）
│   │   ├── main.js          # Vue 入口
│   │   └── style.css        # 全局样式（~4800 行）
│   ├── dist/                # 生产构建产物
│   ├── index.html
│   └── package.json
├── scripts/                 # Windows 计划任务脚本
├── requirements.txt
└── README.md
```

> 前端采用单文件组件架构，`App.vue` 通过 `currentPage` 状态切换页面，`window.location.hash` 管理路由。所有 API 调用通过 Axios 发送到 `/api/...` 端点。

## 数据模型

| 模型 | 用途 |
|------|------|
| AccountProfile | 用户角色（学生/教师/管理员） |
| StudentProfile | 学生档案（学号、学院、年级、压力来源） |
| Counselor | 咨询师（姓名、职称、擅长领域、可预约时段） |
| Tag | 标签主数据 |
| TagSuggestion | 标签建议（用户提议→审核→应用） |
| Article | 心理科普文章 |
| ExternalResourceSource | 外部资源源站 |
| ResourceFetchLog | 资源抓取日志 |
| ResourceViewLog | 学生资源浏览记录 |
| MoodEntry | 情绪打卡记录 |
| TreeHolePost | 匿名树洞帖子 |
| TreeHoleReply | 树洞回复 |
| AssessmentScale | 心理量表 |
| AssessmentRecord | 测评记录 |
| Appointment | 咨询预约 |
| CrisisAlert | 危机预警 |
| InvitationCode | 邀请码 |
| AIChatConfig | AI 倾听配置 |

## 快速开始

### 1. 后端

```powershell
cd P-support-E-expression

# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖（清华源加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 初始化数据库
cd backend
python manage.py migrate

# 导入演示数据（含 admin/student001/teacher001 账号）
python manage.py seed_demo

# 启动服务
python manage.py runserver
```

后端地址：`http://127.0.0.1:8000/`
后台管理：`http://127.0.0.1:8000/admin/`
API 浏览：`http://127.0.0.1:8000/api/`

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173/`

生产构建：`npm run build`

### 3. 演示账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123456 | 管理员 |
| student001 | student001 | 学生 |
| teacher001 | teacher001 | 教师 |

## AI 倾听配置

支持 OpenAI、DeepSeek 及兼容 Chat Completions 格式的接口。管理员登录后在前端 AI 倾听页面直接配置，或通过环境变量：

```powershell
$env:AI_CHAT_API_URL="https://api.openai.com/v1/chat/completions"
$env:AI_CHAT_API_KEY="sk-xxx"
$env:AI_CHAT_MODEL="gpt-4o-mini"
$env:AI_CHAT_TIMEOUT="30"
```

> DeepSeek 请使用 `/chat/completions` 路径，不要填写 `/anthropic`。

## 账号注册与邀请码

| 角色 | 注册方式 |
|------|----------|
| 学生 | 直接注册，无需邀请码 |
| 教师 | 需要教师邀请码 |
| 管理员 | 需要管理员邀请码 |

- 邀请码由教师或管理员在个人资料中维护：可随机生成（16 位）或手动输入
- 锁定后复制到剪贴板，解锁后立即失效
- 一次性使用：注册后自动消耗，解锁再锁定恢复一次使用机会

## API 接口

### 认证
- `POST /api/auth/register/` — 注册
- `POST /api/auth/login/` — 登录
- `POST /api/auth/logout/` — 登出
- `GET /api/auth/me/` — 当前用户
- `GET/PATCH /api/auth/profile/` — 个人资料
- `GET/POST /api/auth/invitations/` — 邀请码管理
- `GET/PATCH /api/auth/teacher-profile/` — 教师资料

### 功能模块
- `GET /api/modules/` — 模块中心
- `POST /api/modules/moods/` — 提交情绪打卡
- `POST /api/modules/treeholes/` — 发布树洞
- `POST /api/modules/treeholes/:id/reply/` — 回复树洞
- `POST /api/modules/assessments/` — 提交测评
- `POST /api/modules/appointments/` — 提交预约

### 数据
- `GET /api/insights/` — 数据洞察
- `GET /api/export-insights/csv/` — 导出 CSV
- `GET /api/export-insights/xlsx/` — 导出 Excel
- `GET /api/dashboard/` — 首页概览
- `GET /api/mood-trend/` — 情绪趋势
- `GET /api/pressure-distribution/` — 压力分布
- `GET /api/recommendations/counselors/` — 咨询师推荐

### 资源 & 标签
- `GET /api/articles/` — 文章列表
- `GET /api/tags/` — 标签列表
- `POST /api/tag-suggestions/` — 提交标签建议
- `PATCH /api/tag-suggestions/:id/` — 审核标签
- `POST /api/articles/:id/view-log/` — 记录浏览

### AI
- `GET/PATCH /api/ai-chat/config/` — AI 配置
- `POST /api/ai-chat/` — AI 对话

### 其他
- `GET /api/health/` — 健康检查
- `GET /api/alerts/:id/student-detail/` — 预警学生详情

## 管理命令

```powershell
cd backend

# 系统检查
python manage.py check

# 同步标签（从 JSON 字段到 Tag 表）
python manage.py sync_tags

# 同步外部心理资源
python manage.py sync_authoritative_resources --force

# 同步咨询师数据
python manage.py sync_authoritative_counselors --force

# 运行测试
python manage.py test wellness.tests
```

## 数据库说明

开发环境使用 SQLite（`backend/db.sqlite3`）。Navicat 连接时选择 SQLite 类型并选中该文件即可，无需账号密码。

## 部署注意事项

- 关闭 `DEBUG`，配置 `SECRET_KEY` 和 `ALLOWED_HOSTS`
- 生产环境替换 SQLite 为 MySQL / PostgreSQL
- AI Key 等敏感配置放入环境变量或密钥管理服务
- 爬虫同步功能仅用于课程设计或原型演示
- 前端 `dist/` 目录可部署到 Nginx 等静态服务器，配合 Django 后端 API
