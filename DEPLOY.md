# 狂野飙车9游戏账号交易平台

一个基于Flask的游戏账号交易平台，包含议价、充值、交易等功能。

## 部署到Railway（公网永久访问）

### 步骤1：上传到GitHub

1. 登录GitHub，点击右上角 **+** → **New repository**
2. 仓库名称填 `asphalt9-trading`，选择 **Public**
3. 点击 **Create repository**

4. 打开项目文件夹，右键选择 **用Git Bash here**（或打开终端）

5. 执行以下命令：
```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/你的用户名/asphalt9-trading.git
git push -u origin main
```

### 步骤2：部署到Railway

1. 访问 https://railway.app 并登录（可用GitHub账号）
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 选择你刚创建的 `asphalt9-trading` 仓库
4. Railway会自动检测并部署

### 步骤3：添加数据库

1. 部署完成后，点击你的项目
2. 点击 **Add a Database** → **PostgreSQL**
3. Railway会自动设置 `DATABASE_URL` 环境变量

### 步骤4：配置环境变量

1. 在项目设置中，找到 **Variables**
2. 添加环境变量：
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = `asphalt9_trading_secret_key_2024`

### 获取公网地址

部署成功后，Railway会提供类似 `https://asphalt9-trading.up.railway.app` 的公网地址，点击即可访问！

---

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

访问 http://127.0.0.1:5000

## 测试账号

- 管理员：admin / admin123
- 用户：racing_king / user123
