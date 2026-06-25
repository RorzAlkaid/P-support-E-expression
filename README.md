# 大学生心理支持与情绪表达平台 — 心晴校园

基于 Django + Django REST Framework + Vue 3 + Vite 的校园心理健康服务平台。面向学生、心理教师和管理员，提供情绪打卡、匿名树洞、心理测评、咨询预约、心理资源、AI 倾听、数据洞察、风险预警和后台管理等一体化功能。

## 功能总览

### 学生端
- **情绪打卡** — 记录每日情绪、强度、睡眠质量、压力来源和私密日记，自动生成近一周趋势图
- **匿名树洞** — 匿名发布倾诉内容，学生回复匿名显示为"同伴支持者"，教师回复显示真实姓名并标"教师/咨询师"徽章；点击 ♥ 一键支持同学
- **AI 倾听** — 接入兼容 OpenAI Chat Completions 的大模型，提供即时对话陪伴、情绪梳理和自助建议；支持浏览器语音识别输入
- **心理测评** — 通过量表自评生成得分、风险等级和分层建议
- **咨询预约** — 按咨询师、时间和主题提交预约，查看预约状态和咨询师匹配推荐
- **心理资源** — 浏览心理科普文章，支持标签/标题/分类搜索，自动记录浏览行为

### 教师端
- 查看情绪打卡、测评记录、树洞内容和预约队列
- 维护个人咨询师资料（职称、擅长领域、可预约时段）
- 管理教师邀请码
- 查看和处理危机预警，查看预警学生完整数据详情
- 树洞回复自动标注"教师/咨询师"身份并显示真实姓名

### 管理员端
- 将任意学生一键添加为咨询师
- 维护教师和管理员邀请码
- 管理全部数据（用户、文章、咨询师、量表、预约、预警等）
- 配置 AI 倾听服务（服务商选择、API Key、模型切换）
- 标签管理：后台可直接增删改查，支持批量启用/停用
- 标签提议审核：批量通过/驳回学生提交的标签
- 数据洞察看板 + 导出 CSV / Excel
- Django Admin 后台（SimpleUI 主题）

### 交互动效
- **页面淡入** — 标题、卡片、面板等元素滚动进入视口时平滑淡入升起
- **图表动画** — 折线图描摹绘制、雷达图中心扩散、饼图扇区依次弹出、柱状图底部升起，每次滚入重播
- **支持反馈** — 树洞 ♥ 按钮 hover 放大、点击即时 +1，低门槛传递同伴关怀
- **移动端响应式** — 支持手机/平板等小屏设备，汉堡菜单导航，布局自适应适配

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Django 5.2 + Django REST Framework 3.17 |
| 数据库 | SQLite（开发）/ 可切换 MySQL |
| 后台管理 | Django Admin + SimpleUI |
| 跨域 | django-cors-headers |
| 前端框架 | Vue 3（Composition API） |
| 构建工具 | Vite 8 |
| HTTP 客户端 | Axios |
| 图表 | ECharts 6 |
| 语音识别 | Web Speech API（浏览器内置） |
| 字体 | Microsoft YaHei（微软雅黑） |

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
│   │   │   ├── seed_demo.py                     # 初始化演示数据
│   │   │   ├── sync_authoritative_counselors.py # 同步咨询师
│   │   │   ├── sync_authoritative_resources.py  # 同步心理资源
│   │   │   └── sync_tags.py                     # 同步标签
│   │   ├── static/admin/js/
│   │   │   └── ai_chat_model_switcher.js        # AI 模型动态切换
│   │   ├── migrations/      # 数据库迁移
│   │   ├── admin.py         # Django Admin 配置
│   │   ├── models.py        # 数据模型
│   │   ├── serializers.py   # DRF 序列化器
│   │   ├── urls.py          # API 路由
│   │   ├── views.py         # 业务逻辑
│   │   └── tests.py         # 测试
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── assets/          # 图片、Logo
│   │   ├── App.vue          # 单文件全应用
│   │   ├── main.js          # Vue 入口
│   │   └── style.css        # 全局样式（含移动端响应式）
│   ├── dist/                # 生产构建产物
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── scripts/                 # Windows 计划任务脚本
├── requirements.txt
└── README.md
```

> 前端采用单文件组件架构，`App.vue` 通过 `currentPage` 状态切换 15+ 页面，`window.location.hash` 管理路由，Axios 发送所有 API 请求。

## 数据模型

| 模型 | 用途 |
|------|------|
| AccountProfile | 用户角色（学生 / 教师 / 管理员） |
| StudentProfile | 学生档案（学号、学院、年级、压力来源、偏好主题） |
| Counselor | 咨询师（姓名、职称、擅长领域、可预约时段） |
| Tag | 标签主数据（支持增删改查、批量启用停用） |
| TagSuggestion | 标签提议（用户提议 → 审核 → 通过/驳回） |
| Article | 心理科普文章 |
| ExternalResourceSource | 外部资源源站 |
| ResourceFetchLog | 资源抓取日志 |
| ResourceViewLog | 学生资源浏览记录 |
| MoodEntry | 情绪打卡记录 |
| TreeHolePost | 匿名树洞帖子（含 support_count 支持计数） |
| TreeHoleReply | 树洞回复（同伴支持者 / 教师/咨询师） |
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

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 初始化数据库
cd backend
python manage.py migrate

# 导入演示数据（含测试账号）
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

生产构建：`npm run build`（产物输出到 `frontend/dist/`）

### 3. 测试账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123456 | 管理员 |
| student001 | student001 | 学生 |
| teacher001 | teacher001 | 教师 |

## AI 倾听配置

支持 OpenAI、DeepSeek 及兼容 Chat Completions 格式的接口。

**方式一：后台管理界面**
管理员登录后进入"AI 倾听对话"页面 → 展开管理面板 → 选择服务商 → 从预设模型下拉框选择或输入自定义模型 → 填写 API Key。

**方式二：环境变量**
```powershell
$env:AI_CHAT_API_URL="https://api.openai.com/v1/chat/completions"
$env:AI_CHAT_API_KEY="sk-xxx"
$env:AI_CHAT_MODEL="gpt-4o-mini"
$env:AI_CHAT_TIMEOUT="30"
```

**方式三：Django Admin 后台**
进入后台 → 心理服务管理 → AI 倾听配置 → 可添加多套配置、切换服务商后模型下拉框自动更新。

> DeepSeek 请使用 `/chat/completions` 路径，不要使用 `/anthropic`。

## 账号注册与邀请码

| 角色 | 注册方式 |
|------|----------|
| 学生 | 直接注册，无需邀请码 |
| 教师 | 需要教师邀请码 |
| 管理员 | 需要管理员邀请码 |

- 邀请码由教师/管理员在"个人资料"页面维护
- 点击"生成随机码"创建 16 位邀请码，也可手动输入自定义码
- 锁定后复制分享，解锁立即失效
- 一次性使用：注册后自动消耗

## 树洞同伴支持

树洞模块提供多层次的同伴互助机制：

| 方式 | 说明 |
|------|------|
| **匿名倾诉** | 学生以"匿名同学"身份发布困扰 |
| **♥ 一键支持** | 列表和详情页均可点击支持，即时 +1 反馈 |
| **同伴回复** | 学生回复显示为"同伴支持者"，教师回复显示真实姓名并标"教师/咨询师"徽章 |
| **风险守护** | 含自伤/自杀关键词自动标记并创建危机预警通知教师 |

## API 接口

### 认证
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/register/` | 注册 |
| POST | `/api/auth/login/` | 登录 |
| POST | `/api/auth/logout/` | 登出 |
| GET | `/api/auth/me/` | 当前用户信息 |
| GET, PATCH | `/api/auth/profile/` | 个人资料 |
| GET, POST | `/api/auth/invitations/` | 邀请码管理 |
| GET, PATCH | `/api/auth/teacher-profile/` | 教师资料 |

### 功能模块
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/modules/` | 模块中心数据 |
| POST | `/api/modules/moods/` | 提交情绪打卡 |
| POST | `/api/modules/treeholes/` | 发布树洞 |
| POST | `/api/modules/treeholes/:id/reply/` | 回复树洞 |
| POST | `/api/modules/treeholes/:id/support/` | 支持树洞（+1） |
| POST | `/api/modules/assessments/` | 提交测评 |
| POST | `/api/modules/appointments/` | 创建预约 |

### 数据洞察
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/insights/` | 数据洞察面板 |
| GET | `/api/export-insights/csv/` | 导出 CSV |
| GET | `/api/export-insights/xlsx/` | 导出 Excel |
| GET | `/api/dashboard/` | 首页概览 |
| GET | `/api/mood-trend/` | 情绪趋势数据 |
| GET | `/api/pressure-distribution/` | 压力分布数据 |
| GET | `/api/recommendations/counselors/` | 咨询师推荐 |

### AI
| 方法 | 端点 | 说明 |
|------|------|------|
| GET, PATCH | `/api/ai-chat/config/` | AI 配置管理 |
| POST | `/api/ai-chat/` | 发送对话消息 |

### 资源 & 标签
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/articles/` | 文章列表 |
| POST | `/api/articles/:id/view-log/` | 记录浏览 |
| GET, POST, PATCH, DELETE | `/api/tags/` | 标签 CRUD |
| GET, POST, PATCH | `/api/tag-suggestions/` | 标签提议 |
| GET | `/api/health/` | 健康检查 |
| GET | `/api/alerts/:id/student-detail/` | 预警学生详情 |

> 完整 CRUD 端点（students, counselors, articles, treehole-posts, treehole-replies, crisis-alerts 等）由 DRF Router 自动注册，见 `wellness/urls.py`。

## 管理命令

```powershell
cd backend

# 系统检查
python manage.py check

# 导入演示数据
python manage.py seed_demo

# 同步标签（从 JSON 字段到 Tag 表）
python manage.py sync_tags

# 同步外部心理资源
python manage.py sync_authoritative_resources --force

# 同步咨询师数据
python manage.py sync_authoritative_counselors --force

# 运行测试
python manage.py test wellness.tests
```

## Django Admin 后台功能

后台地址：`http://127.0.0.1:8000/admin/`

### 菜单结构
| 菜单组 | 包含模块 |
|--------|----------|
| 账号与权限 | 用户、用户组、账号角色、学生档案、邀请码 |
| 心理服务管理 | 咨询师、咨询预约、情绪日记、匿名树洞、树洞回应、危机预警、AI 倾听配置 |
| 内容与数据管理 | 标签管理、标签提议、心理科普文章、外部资源源站、资源抓取记录、心理量表、量表记录、资源浏览记录 |

### 标签管理亮点
- 列表展示标签名、描述预览、启用状态、引用次数、创建者
- 列表内直接开关启用状态（行内编辑）
- 批量启用 / 批量停用
- 自动统计各标签在文章和咨询师中的引用次数

### AI 配置亮点
- 可添加多套配置，不再限制单例
- 服务商下拉选择（OpenAI / DeepSeek / 自动检测 / 自定义）
- 模型根据服务商动态过滤预设列表，也支持手动输入自定义模型名
- 自动检测模型开关

## 部署注意事项

1. **安全配置** — 生产环境设置环境变量：
   ```
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=<强随机密钥>
   DJANGO_ALLOWED_HOSTS=your-domain.com
   CORS_ALLOWED_ORIGINS=https://your-domain.com
   ```
2. **数据库** — 替换 SQLite 为 MySQL
3. **AI Key** — 通过环境变量 `AI_CHAT_API_KEY` 或 Django Admin 后台配置
4. **前端构建** — `npm run build` 后将 `dist/` 部署到 Nginx 或 Django 静态文件目录
5. **Docker 部署** — 项目支持 Docker Compose 一键部署（Django + MySQL + Nginx），详见部署文档
6. **CSRF** — 当前 SPA 开发模式使用 `CsrfExemptSessionAuthentication`，生产同域部署时可启用标准 CSRF

## 开源协作

本项目为课程设计作品，欢迎交流与改进。

GitHub: [RorzAlkaid/P-support-E-expression](https://github.com/RorzAlkaid/P-support-E-expression)

## 许可证

本项目仅用于学习和教育目的。
