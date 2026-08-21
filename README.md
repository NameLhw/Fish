# 校园版咸鱼 - 校园二手交易平台

> 高校学生二手物品交易平台，移动端优先 (H5)，支持商品发布、求购、私聊、线下当面交易

## 技术栈

- **后端**: Python + Flask + Flask-SQLAlchemy
- **数据库**: SQLite (文件型，无需额外服务)
- **前端**: HTML5 + CSS3 + JavaScript (Jinja2 模板渲染)
- **图片处理**: Pillow

## 快速启动

### 1. 创建虚拟环境并安装依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_db.py
```

### 3. 启动应用

```bash
python app.py
```

或者直接运行启动脚本：

```bash
run.bat
```

### 4. 访问应用

浏览器打开: http://127.0.0.1:5000

## 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 学生 | 张三 | 123456 |
| 学生 | 李四 | 123456 |
| 学生 | 王五 | 123456 |

## 核心功能

### 1. 商品发布管理
- 发布二手商品（标题、价格、原价、分类、新旧程度、校区、交易方式、图文描述）
- 编辑、删除、上下架商品
- 多图片上传

### 2. 求购管理
- 发布求购信息（物品名称、预算范围、期望成色、校区）
- 查看求购列表、搜索、联系求购者
- 删除自己的求购信息

### 3. 用户与认证
- 学生注册（用户名 + 学号 + 学院）
- 登录 / 退出
- 个人资料管理（头像、手机号）
- 管理员审核用户

### 4. 搜索筛选
- 关键词搜索
- 按分类、校区、新旧程度筛选
- 按价格排序（从低到高 / 从高到低）
- 分页展示

### 5. 互动与交易
- 商品留言评论
- 买卖双方私聊
- 创建订单、约定交易地点和时间
- 订单状态跟踪（待沟通 → 待交易 → 已完成 / 已取消）

### 6. 平台管理
- 管理后台仪表盘（数据统计）
- 商品审核管理（通过 / 驳回 / 强制下架）
- 用户管理（通过 / 拒绝）
- 分类管理（增删）
- 举报处理

## 项目结构

```
campus-flea-market/
├── app.py                 # 主应用 (Flask 路由)
├── config.py              # 配置文件
├── models.py              # 数据库模型
├── init_db.py             # 数据库初始化脚本
├── requirements.txt       # Python 依赖
├── run.bat                # Windows 启动脚本
├── campus_flea.db         # SQLite 数据库 (自动生成)
├── static/
│   ├── css/
│   │   ├── style.css      # 全局样式
│   │   └── default_avatar.svg  # 默认头像
│   ├── js/
│   │   └── app.js         # 前端交互
│   └── uploads/           # 图片上传目录
└── templates/
    ├── base.html          # 基础模板 (导航 + 页脚)
    ├── index.html         # 首页 (商品列表 + 筛选)
    ├── product_detail.html # 商品详情
    ├── publish.html       # 发布/编辑商品
    ├── my_products.html   # 我的商品
    ├── purchase_list.html # 求购列表
    ├── purchase_publish.html # 发布求购
    ├── login.html         # 登录
    ├── register.html      # 注册
    ├── profile.html       # 个人中心
    ├── edit_profile.html  # 编辑资料
    ├── messages.html      # 消息列表
    ├── chat.html          # 私聊页面
    ├── orders.html        # 订单管理
    ├── error.html         # 错误页
    └── admin/
        ├── dashboard.html # 管理后台
        ├── products.html  # 商品管理
        ├── users.html     # 用户管理
        ├── categories.html # 分类管理
        └── reports.html  # 举报处理
```

## 数据库模型

| 模型 | 说明 |
|------|------|
| User | 用户 (学生/管理员) |
| Product | 二手商品 |
| Category | 商品分类 |
| PurchaseRequest | 求购信息 |
| Message | 私信消息 |
| Order | 交易订单 |
| Comment | 商品留言 |
| Report | 违规举报 |

## 可扩展方向

- AI 智能审核商品信息
- 公益捐赠模块
- 二手教材专区
- 校园闲置置换
- 微信小程序版本
- 实时消息推送 (WebSocket)
