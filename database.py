"""
狂野飙车9游戏账号交易平台
数据库初始化模块
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'trading_platform.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    # 检查数据库是否已存在，如果已存在则不重新初始化
    if os.path.exists(DATABASE):
        print('数据库已存在，跳过初始化')
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            balance REAL DEFAULT 1000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建游戏账号表
    cursor.execute('''
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            level INTEGER,
            cars_count INTEGER,
            price REAL NOT NULL,
            image_desc TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    # 创建交易记录表
    cursor.execute('''
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    # 创建议价表
    cursor.execute('''
        CREATE TABLE negotiations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            offered_price REAL NOT NULL,
            counter_price REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id)
        )
    ''')
    
    # 创建管理员账户
    admin_password = generate_password_hash('admin123')
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (?, ?, ?, ?)',
        ('admin', admin_password, 'admin@example.com', 10000.0)
    )
    
    # 创建示例卖家
    user1_password = generate_password_hash('user123')
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (?, ?, ?, ?)',
        ('racing_king', user1_password, 'racing@example.com', 5000.0)
    )
    
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (?, ?, ?, ?)',
        ('speed_demon', generate_password_hash('pass123'), 'speed@example.com', 3000.0)
    )
    
    conn.commit()
    conn.close()
    
    print('数据库初始化完成！')
    print('管理员账号: admin / admin123')
    print('示例账号: racing_king / user123, speed_demon / pass123')

def add_negotiations_table():
    """为现有数据库添加议价表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='negotiations'")
    if cursor.fetchone():
        conn.close()
        return
    
    cursor.execute('''
        CREATE TABLE negotiations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            offered_price REAL NOT NULL,
            counter_price REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_images_column():
    """为账号表添加图片字段"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(accounts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'images' not in columns:
        cursor.execute("ALTER TABLE accounts ADD COLUMN images TEXT DEFAULT ''")
        conn.commit()
    
    conn.close()

def add_insurance_column():
    """为交易表添加保险字段"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'insurance' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN insurance REAL DEFAULT 0")
        conn.commit()
    
    conn.close()

if __name__ == '__main__':
    init_db()
