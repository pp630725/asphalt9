# 狂野飙车9游戏账号交易平台

一个虚拟的游戏账号交易网站，用于演示和娱乐目的。

## 功能特性

- 用户注册和登录
- 发布游戏账号
- 浏览和搜索账号
- 虚拟购买流程
- 用户中心管理
- 金币充值系统

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

### 3. 访问网站

打开浏览器访问: http://127.0.0.1:5000

## 测试账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |
| racing_king | user123 |
| speed_demon | pass123 |

## 项目结构

```
.
├── app.py              # 主应用文件
├── database.py         # 数据库模块
├── trading_platform.db # SQLite 数据库文件（运行后自动创建）
├── requirements.txt    # Python 依赖
├── README.md           # 说明文档
└── templates/         # HTML 模板
    ├── base.html       # 基础模板
    ├── index.html      # 首页
    ├── accounts.html   # 账号列表
    ├── account_detail.html  # 账号详情
    ├── login.html      # 登录页
    ├── register.html   # 注册页
    ├── sell.html       # 发布账号页
    ├── my_accounts.html # 我的账号页
    └── recharge.html   # 充值页
```

## 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite
- **前端**: HTML5 + CSS3 + JavaScript

## 注意事项

- 这是一个虚拟交易系统，不涉及真实货币
- 密码使用安全哈希存储
- 所有数据存储在本地 SQLite 数据库
