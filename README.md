# 大学生心理支持与情绪表达平台

基于 Django + Vue 的校园心理健康服务平台。系统面向学生、心理教师和管理员，提供心理资源浏览、情绪打卡、匿名树洞、心理测评、咨询预约、风险预警、数据洞察和后台管理等功能。

## 功能概览

- 账号体系：支持学生、心理教师、管理员角色，学生注册时可补充学号、学院、年级、压力来源和关注主题。
- 心理资源：展示心理科普文章，支持文章详情页浏览和资源浏览记录。
- 情绪打卡：记录情绪、强度、睡眠质量、压力来源和私密备注。
- 匿名树洞：支持匿名发布、回应和高风险表达标记。
- 心理测评：根据量表答题生成分数、风险等级和建议。
- 咨询预约：学生提交预约，教师可维护个人咨询资料并处理预约状态。
- 风险预警：根据低情绪、高风险文本和高风险测评生成预警，教师和管理员可查看学生详情。
- 数据洞察：展示情绪趋势、压力分布、风险分布和预约状态，并支持导出 CSV / Excel。
- 后台管理：使用 Django Admin + SimpleUI 管理用户、学生档案、咨询师、文章、量表和业务数据。
- 数据同步：提供管理命令和 Windows 计划任务脚本，同步公开心理资源和咨询师数据。

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
├── backend/
│   ├── config/
│   ├── wellness/
│   │   ├── management/commands/
│   │   │   ├── seed_demo.py
│   │   │   ├── sync_authoritative_counselors.py
│   │   │   └── sync_authoritative_resources.py
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   └── manage.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── setup_daily_counselor_sync.ps1
│   └── setup_daily_resource_sync.ps1
├── requirements.txt
└── README.md
```

本地虚拟环境、`node_modules`、构建产物、日志文件和 SQLite 数据库不应提交到仓库，已通过 `.gitignore` 忽略。

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
- 爬虫同步数据来自公开网页，仅用于课程设计、毕业设计或原型演示场景。
