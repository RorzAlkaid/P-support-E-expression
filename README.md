# 大学生心理支持与情绪表达平台

基于 Django + Vue 的大学生心理健康服务平台，围绕“隐私化、专业化、便捷化”的目标，提供心理资源、情绪记录、匿名树洞、心理测评、咨询预约、数据可视化、风险预警和后台管理等功能。

## 项目功能

- 用户登录注册：支持未登录浏览、学生、教师、管理员等不同访问权限。
- 首页功能简介：用户可以从首页功能中心进入各业务模块。
- 模块详情页：集中展示平台各模块用途，方便学生和教师了解系统内容。
- 心理资源：展示科普文章，支持文章详情页查看。
- 情绪日记：学生可记录情绪、强度、压力来源和备注。
- 匿名树洞：学生可匿名表达压力、关系和成长困扰。
- 心理测评：支持心理量表记录与结果展示。
- 咨询预约：学生可选择咨询师并提交预约，教师可查看，管理员可管理。
- 咨询师数据：通过爬虫从公开高校心理咨询中心页面同步咨询师姓名、职称和专长。
- 数据可视化：使用 ECharts 展示校园心理健康概览、情绪趋势和压力分布。
- 后台管理：使用 Django Admin + SimpleUI，支持中文化数据管理。
- 定时更新：提供 Windows 计划任务脚本，每日自动同步心理资源和咨询师数据。

## 技术栈

### 后端

- Python 3.11+
- Django 5.2
- Django REST framework
- django-cors-headers
- django-simpleui
- SQLite

### 前端

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
│   │   ├── management/
│   │   │   └── commands/
│   │   │       ├── seed_demo.py
│   │   │       ├── sync_authoritative_resources.py
│   │   │       └── sync_authoritative_counselors.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── db.sqlite3
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── setup_daily_resource_sync.ps1
│   └── setup_daily_counselor_sync.ps1
├── requirements.txt
└── README.md
```

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

后端默认地址：

```text
http://127.0.0.1:8000/
```

后台管理地址：

```text
http://127.0.0.1:8000/admin/
```

## 前端运行

在项目根目录执行：

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173/
```

生产构建：

```powershell
cd frontend
npm run build
```

## 数据同步命令

同步权威心理科普资源：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py sync_authoritative_resources --force
```

同步公开高校心理咨询中心的咨询师数据：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py sync_authoritative_counselors --force
```

说明：咨询师爬虫当前只写入姓名、职称和专长，不保存来源链接、资质说明、可预约时段等额外字段。

## 每日自动更新

项目提供 Windows 计划任务脚本：

```powershell
.\scripts\setup_daily_resource_sync.ps1
.\scripts\setup_daily_counselor_sync.ps1
```

执行后会注册每日自动任务，定时运行对应的 Django 管理命令。

## 常用检查

后端检查：

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py check
```

前端构建检查：

```powershell
cd frontend
npm run build
```

## 数据库说明

开发环境默认使用 SQLite：

```text
backend/db.sqlite3
```

如果使用 Navicat 连接，选择 SQLite 连接类型，然后选择该数据库文件即可。SQLite 本地文件模式没有数据库账号和密码。

## 备注

- 本项目当前用于课程设计、毕业设计或原型演示场景。
- 爬虫数据来自公开网页，仅用于系统功能演示和初始化数据。
- 部署到云端前需要关闭 `DEBUG`、配置正式 `SECRET_KEY`、设置 `ALLOWED_HOSTS`，并根据实际需要替换为 MySQL/PostgreSQL 等数据库。
