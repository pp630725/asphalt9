"""
狂野飙车9游戏账号交易平台
数据库初始化模块
支持 SQLite（本地）和 PostgreSQL（云部署）
"""
import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

# 数据库配置 - 支持多种环境变量名
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRESQL_URL') or os.environ.get('DATABASE_URI') or ''
DATABASE = 'trading_platform.db' if not DATABASE_URL else DATABASE_URL

def is_postgresql():
    """检查是否为PostgreSQL数据库"""
    if not DATABASE_URL:
        return False
    # 检查各种可能的PostgreSQL URL前缀
    url_lower = DATABASE_URL.lower()
    pg_prefixes = ('postgres://', 'postgresql://', 'postgres:', 'postgresql:')
    return any(url_lower.startswith(prefix) for prefix in pg_prefixes)

def get_db():
    """获取数据库连接"""
    if is_postgresql():
        # PostgreSQL连接（云部署）
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            print(f"PostgreSQL连接失败: {e}")
            print(f"DATABASE_URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"DATABASE_URL: {DATABASE_URL}")
    # SQLite连接（本地开发）
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    print(f"[init_db] 检测到数据库模式: {'PostgreSQL' if is_postgresql() else 'SQLite'}")
    if is_postgresql():
        init_postgres_db()
    else:
        init_sqlite_db()

def init_sqlite_db():
    """初始化SQLite数据库"""
    if os.path.exists(DATABASE):
        print('数据库已存在，跳过初始化')
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建表
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
            images TEXT DEFAULT '',
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            price REAL NOT NULL,
            insurance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
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
    
    # 创建示例数据
    create_sample_data(conn, cursor)
    
    conn.commit()
    conn.close()
    print('数据库初始化完成！')

def init_postgres_db():
    """初始化PostgreSQL数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建表（使用PostgreSQL语法）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            balance REAL DEFAULT 1000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            seller_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            level INTEGER,
            cars_count INTEGER,
            price REAL NOT NULL,
            image_desc TEXT,
            images TEXT DEFAULT '',
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            buyer_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            price REAL NOT NULL,
            insurance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS negotiations (
            id SERIAL PRIMARY KEY,
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
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        print('数据库已存在，跳过初始化')
        return
    
    # 创建示例数据
    create_sample_data(conn, cursor)
    
    conn.commit()
    conn.close()
    print('PostgreSQL数据库初始化完成！')

def create_sample_data(conn, cursor):
    """创建示例数据"""
    # 创建管理员
    admin_password = generate_password_hash('admin123')
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (%s, %s, %s, %s)',
        ('admin', admin_password, 'admin@example.com', 10000.0)
    )
    
    # 创建卖家
    user1_password = generate_password_hash('user123')
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (%s, %s, %s, %s)',
        ('racing_king', user1_password, 'racing@example.com', 5000.0)
    )
    
    cursor.execute(
        'INSERT INTO users (username, password, email, balance) VALUES (%s, %s, %s, %s)',
        ('speed_demon', generate_password_hash('pass123'), 'speed@example.com', 3000.0)
    )
    
    # 创建示例账号
    sample_accounts = [
        ('极速传说888', 'VIP15级顶级账号，全S级车辆库包含法拉利LaFerrari、帕加尼Huayra、布加迪Chiron等绝版豪车。账号历史胜率85%，累计声望值999999，解锁全部赛道和成就。', 50, 45, 8888.0),
        ('秋名山车神001', '竞技专精账号，排名第1赛季冠军，多次获得钻石联赛冠军。拥有10辆S级限定车辆，氮气加速技巧纯熟。', 45, 38, 6688.0),
        ('幻影车神9527', '稀有赛季冠军账号，本赛季积分8888，拥有多辆绝版限定车辆。账号无违规记录，交易安全。', 42, 35, 5888.0),
        ('漂移之王007', '高端账号，高胜率75%，擅长各种赛道。拥有兰博基尼Aventador SVJ、保时捷911 GT3等顶级跑车。', 40, 32, 4888.0),
        ('极速狂飙123', 'VIP12账号，解锁全部赛道，车库包含多辆A级和S级车辆。性价比极高的入门级高端账号。', 35, 28, 2888.0),
        ('午夜赛车手', '代练退单账号，账号价值被低估。包含法拉利488 GTB、迈凯伦570S等高性能车辆，适合进阶玩家。', 32, 25, 2288.0),
        ('风暴骑士666', '限时特惠账号，包含多辆限定版车辆。账号等级30级，上升空间大，适合新手玩家入门。', 30, 22, 1688.0),
        ('闪电漂移者', '平民玩家账号，高性价比。拥有多辆实用A级车辆，氮气加速技巧熟练，适合日常娱乐。', 25, 18, 988.0),
        ('夜之咆哮', '新手起步账号，包含基础S级车辆一辆。账号等级20级，轻松上手，体验游戏核心玩法。', 20, 12, 588.0),
        ('暗夜猎手', '体验账号，包含3辆A级车辆。账号等级15级，适合首次体验狂野飙车9国服的玩家。', 15, 8, 388.0),
    ]
    
    # 根据数据库类型选择占位符
    placeholder = '%s' if is_postgresql() else '?'
    
    for title, desc, level, cars, price in sample_accounts:
        cursor.execute(
            f'INSERT INTO accounts (seller_id, title, description, level, cars_count, price, images, status) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})',
            (2, title, desc, level, cars, price, '', 'available')
        )
    
    print('示例数据创建完成！')
    print('管理员账号: admin / admin123')
    print('示例账号: racing_king / user123')

def add_negotiations_table():
    """为现有数据库添加议价表"""
    conn = get_db()
    cursor = conn.cursor()
    
    if is_postgresql():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS negotiations (
                id SERIAL PRIMARY KEY,
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
    else:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='negotiations'")
        if not cursor.fetchone():
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
    
    if is_postgresql():
        try:
            cursor.execute('ALTER TABLE accounts ADD COLUMN images TEXT DEFAULT \'\'')
            conn.commit()
        except psycopg2.errors.DuplicateColumn:
            pass
    else:
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
    
    if is_postgresql():
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN insurance REAL DEFAULT 0')
            conn.commit()
        except psycopg2.errors.DuplicateColumn:
            pass
    else:
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'insurance' not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN insurance REAL DEFAULT 0")
            conn.commit()
    
    conn.close()

if __name__ == '__main__':
    init_db()
