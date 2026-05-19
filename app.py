"""
狂野飙车9游戏账号交易平台
主应用文件
"""
import sqlite3
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from database import get_db, init_db, add_negotiations_table, add_images_column, add_insurance_column

app = Flask(__name__)
app.secret_key = 'asphalt9_trading_secret_key_2024'

DATABASE = 'trading_platform.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGES = 9

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== 辅助函数 ====================

def login_required(f):
    """登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        return user
    return None

# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取最新上架的账号
    cursor.execute('''
        SELECT a.*, u.username as seller_name 
        FROM accounts a 
        JOIN users u ON a.seller_id = u.id 
        WHERE a.status = 'available' 
        ORDER BY a.created_at DESC 
        LIMIT 6
    ''')
    latest_accounts = cursor.fetchall()
    
    # 获取热门账号（高等级）
    cursor.execute('''
        SELECT a.*, u.username as seller_name 
        FROM accounts a 
        JOIN users u ON a.seller_id = u.id 
        WHERE a.status = 'available' 
        ORDER BY a.level DESC 
        LIMIT 6
    ''')
    hot_accounts = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', 
                           latest_accounts=latest_accounts, 
                           hot_accounts=hot_accounts,
                           user=get_current_user())

@app.route('/accounts')
def accounts():
    """账号列表页"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有可交易账号
    cursor.execute('''
        SELECT a.*, u.username as seller_name 
        FROM accounts a 
        JOIN users u ON a.seller_id = u.id 
        WHERE a.status = 'available' 
        ORDER BY a.created_at DESC
    ''')
    accounts = cursor.fetchall()
    conn.close()
    
    return render_template('accounts.html', accounts=accounts, user=get_current_user())

@app.route('/account/<int:account_id>')
def account_detail(account_id):
    """账号详情页"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, u.username as seller_name, u.email as seller_email
        FROM accounts a 
        JOIN users u ON a.seller_id = u.id 
        WHERE a.id = ?
    ''', (account_id,))
    account = cursor.fetchone()
    conn.close()
    
    if not account:
        flash('账号不存在！', 'danger')
        return redirect(url_for('accounts'))
    
    current_user = get_current_user()
    is_owner = current_user and current_user['id'] == account['seller_id']
    is_sold = account['status'] == 'sold'
    
    return render_template('account_detail.html', 
                           account=account, 
                           user=current_user,
                           is_owner=is_owner,
                           is_sold=is_sold)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_account():
    """发布账号页"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        level = request.form.get('level')
        cars_count = request.form.get('cars_count')
        price = request.form.get('price')
        image_desc = request.form.get('image_desc')
        
        if not all([title, level, cars_count, price]):
            flash('请填写所有必填项！', 'danger')
            return redirect(url_for('sell_account'))
        
        # 处理图片上传
        uploaded_images = []
        files = request.files.getlist('images')
        for i, file in enumerate(files[:MAX_IMAGES]):
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 添加时间戳避免重名
                import time
                new_filename = f"{int(time.time())}_{i}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, new_filename))
                uploaded_images.append(new_filename)
        
        images_str = ','.join(uploaded_images)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (seller_id, title, description, level, cars_count, price, image_desc, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], title, description, level, cars_count, price, image_desc, images_str))
        conn.commit()
        conn.close()
        
        flash('账号发布成功！', 'success')
        return redirect(url_for('my_accounts'))
    
    return render_template('sell.html', user=get_current_user(), max_images=MAX_IMAGES)

@app.route('/my-accounts')
@login_required
def my_accounts():
    """我的账号页"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 我发布的账号
    cursor.execute('''
        SELECT * FROM accounts WHERE seller_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],))
    my_accounts = cursor.fetchall()
    
    # 我购买的账号
    cursor.execute('''
        SELECT a.*, t.created_at as bought_at
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.buyer_id = ?
    ''', (session['user_id'],))
    bought_accounts = cursor.fetchall()
    
    conn.close()
    return render_template('my_accounts.html', 
                           my_accounts=my_accounts, 
                           bought_accounts=bought_accounts,
                           user=get_current_user())

@app.route('/buy/<int:account_id>', methods=['POST'])
@login_required
def buy_account(account_id):
    """购买账号"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取账号信息
    cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
    account = cursor.fetchone()
    
    if not account:
        conn.close()
        flash('账号不存在！', 'danger')
        return redirect(url_for('accounts'))
    
    if account['status'] == 'sold':
        conn.close()
        flash('该账号已售出！', 'warning')
        return redirect(url_for('accounts'))
    
    if account['seller_id'] == session['user_id']:
        conn.close()
        flash('不能购买自己的账号！', 'warning')
        return redirect(url_for('account_detail', account_id=account_id))
    
    # 获取买家信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    buyer = cursor.fetchone()
    
    # 检查是否购买保险
    buy_insurance = request.form.get('buy_insurance') == '1'
    insurance_amount = round(account['price'] * 0.1, 2) if buy_insurance else 0
    total_price = account['price'] + insurance_amount
    
    if buyer['balance'] < total_price:
        conn.close()
        if buy_insurance:
            flash(f'余额不足！购买此账号（含保险）需要 {total_price} 金币。', 'danger')
        else:
            flash('余额不足！请充值。', 'danger')
        return redirect(url_for('account_detail', account_id=account_id))
    
    # 执行交易
    try:
        # 扣除买家余额
        new_balance = buyer['balance'] - total_price
        cursor.execute('UPDATE users SET balance = ? WHERE id = ?', 
                       (new_balance, session['user_id']))
        
        # 给卖家增加余额（不含保险费）
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                       (account['price'], account['seller_id']))
        
        # 更新账号状态
        cursor.execute('UPDATE accounts SET status = ? WHERE id = ?',
                       ('sold', account_id))
        
        # 创建交易记录（包含保险信息）
        cursor.execute('INSERT INTO transactions (buyer_id, account_id, price, insurance) VALUES (?, ?, ?, ?)',
                       (session['user_id'], account_id, account['price'], insurance_amount))
        
        conn.commit()
        
        if buy_insurance:
            flash(f'购买成功！您已购买 "{account["title"]}"，并获得{insurance_amount}金币的找回保险！', 'success')
        else:
            flash(f'购买成功！您已购买 "{account["title"]}"！', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'交易失败：{str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('my_accounts'))

@app.route('/recharge', methods=['GET', 'POST'])
@login_required
def recharge():
    """充值页面"""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        
        if amount <= 0:
            flash('请输入正确的金额！', 'danger')
            return redirect(url_for('recharge'))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                       (amount, session['user_id']))
        conn.commit()
        conn.close()
        
        flash(f'充值成功！+{amount} 金币', 'success')
        return redirect(url_for('my_accounts'))
    
    return render_template('recharge.html', user=get_current_user())

# ==================== 用户认证 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'欢迎回来，{user["username"]}！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('login.html', user=get_current_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            flash('请填写用户名和密码！', 'danger')
            return redirect(url_for('register'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            flash('用户名已存在！', 'danger')
            return redirect(url_for('register'))
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            (username, password_hash, email)
        )
        conn.commit()
        conn.close()
        
        flash('注册成功！请登录。', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', user=get_current_user())

@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

# ==================== 议价功能 ====================

@app.route('/negotiate/<int:account_id>', methods=['POST'])
@login_required
def negotiate(account_id):
    """提交议价"""
    offered_price = float(request.form.get('offered_price', 0))
    
    if offered_price <= 0:
        flash('请输入有效的议价金额！', 'danger')
        return redirect(url_for('account_detail', account_id=account_id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查账号是否存在且可售
    cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
    account = cursor.fetchone()
    
    if not account:
        conn.close()
        flash('账号不存在！', 'danger')
        return redirect(url_for('accounts'))
    
    if account['status'] == 'sold':
        conn.close()
        flash('该账号已售出！', 'warning')
        return redirect(url_for('accounts'))
    
    if account['seller_id'] == session['user_id']:
        conn.close()
        flash('不能对自己发布的账号议价！', 'warning')
        return redirect(url_for('account_detail', account_id=account_id))
    
    # 检查是否有待处理的议价
    cursor.execute('''
        SELECT * FROM negotiations 
        WHERE account_id = ? AND buyer_id = ? AND status = 'pending'
    ''', (account_id, session['user_id']))
    if cursor.fetchone():
        conn.close()
        flash('您已提交过议价，请等待卖家回复！', 'warning')
        return redirect(url_for('account_detail', account_id=account_id))
    
    # 创建议价记录
    cursor.execute('''
        INSERT INTO negotiations (account_id, buyer_id, offered_price, status)
        VALUES (?, ?, ?, 'pending')
    ''', (account_id, session['user_id'], offered_price))
    conn.commit()
    conn.close()
    
    flash(f'议价成功！您出价 {offered_price} 金币，等待卖家回复。', 'success')
    return redirect(url_for('my_negotiations'))

@app.route('/negotiations')
@login_required
def my_negotiations():
    """我的议价页面"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 我发出的议价
    cursor.execute('''
        SELECT n.*, a.title as account_title, a.price as original_price, 
               u.username as seller_name
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        JOIN users u ON a.seller_id = u.id
        WHERE n.buyer_id = ?
        ORDER BY n.created_at DESC
    ''', (session['user_id'],))
    my_sent_negotiations = cursor.fetchall()
    
    # 我收到的议价
    cursor.execute('''
        SELECT n.*, a.title as account_title, a.price as original_price,
               u.username as buyer_name
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        JOIN users u ON n.buyer_id = u.id
        WHERE a.seller_id = ? AND n.status IN ('pending', 'countered')
        ORDER BY n.created_at DESC
    ''', (session['user_id'],))
    my_received_negotiations = cursor.fetchall()
    
    conn.close()
    return render_template('negotiations.html',
                           my_sent_negotiations=my_sent_negotiations,
                           my_received_negotiations=my_received_negotiations,
                           user=get_current_user())

@app.route('/negotiate/<int:negotiation_id>/accept', methods=['POST'])
@login_required
def accept_negotiation(negotiation_id):
    """接受议价"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取议价信息
    cursor.execute('''
        SELECT n.*, a.seller_id, a.price as original_price, a.title
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        WHERE n.id = ?
    ''', (negotiation_id,))
    negotiation = cursor.fetchone()
    
    if not negotiation:
        conn.close()
        flash('议价不存在！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['seller_id'] != session['user_id']:
        conn.close()
        flash('无权操作！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['status'] not in ('pending', 'countered'):
        conn.close()
        flash('该议价已处理！', 'warning')
        return redirect(url_for('my_negotiations'))
    
    # 确定成交价格
    if negotiation['status'] == 'countered' and negotiation['counter_price']:
        final_price = negotiation['counter_price']
    else:
        final_price = negotiation['offered_price']
    
    # 获取买家信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (negotiation['buyer_id'],))
    buyer = cursor.fetchone()
    
    if buyer['balance'] < final_price:
        conn.close()
        flash('买家余额不足，无法完成交易！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    # 执行交易
    try:
        # 扣除买家余额
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?',
                       (final_price, negotiation['buyer_id']))
        
        # 给卖家增加余额
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                       (final_price, negotiation['seller_id']))
        
        # 更新账号状态
        cursor.execute('UPDATE accounts SET status = ? WHERE id = ?',
                       ('sold', negotiation['account_id']))
        
        # 更新议价状态
        cursor.execute('UPDATE negotiations SET status = ? WHERE id = ?',
                       ('accepted', negotiation_id))
        
        # 拒绝该账号的其他议价
        cursor.execute('''
            UPDATE negotiations SET status = 'rejected'
            WHERE account_id = ? AND id != ? AND status = 'pending'
        ''', (negotiation['account_id'], negotiation_id))
        
        # 创建交易记录
        cursor.execute('INSERT INTO transactions (buyer_id, account_id, price) VALUES (?, ?, ?)',
                       (negotiation['buyer_id'], negotiation['account_id'], final_price))
        
        conn.commit()
        flash(f'交易成功！以 {final_price} 金币成交账号 "{negotiation["title"]}"！', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'交易失败：{str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('my_accounts'))

@app.route('/negotiate/<int:negotiation_id>/reject', methods=['POST'])
@login_required
def reject_negotiation(negotiation_id):
    """拒绝议价"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.*, a.seller_id
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        WHERE n.id = ?
    ''', (negotiation_id,))
    negotiation = cursor.fetchone()
    
    if not negotiation:
        conn.close()
        flash('议价不存在！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['seller_id'] != session['user_id']:
        conn.close()
        flash('无权操作！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    cursor.execute('UPDATE negotiations SET status = ? WHERE id = ?',
                   ('rejected', negotiation_id))
    conn.commit()
    conn.close()
    
    flash('已拒绝该议价', 'info')
    return redirect(url_for('my_negotiations'))

@app.route('/negotiate/<int:negotiation_id>/counter', methods=['POST'])
@login_required
def counter_negotiation(negotiation_id):
    """还价"""
    counter_price = float(request.form.get('counter_price', 0))
    
    if counter_price <= 0:
        flash('请输入有效的还价金额！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.*, a.seller_id, a.price as original_price
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        WHERE n.id = ?
    ''', (negotiation_id,))
    negotiation = cursor.fetchone()
    
    if not negotiation:
        conn.close()
        flash('议价不存在！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['seller_id'] != session['user_id']:
        conn.close()
        flash('无权操作！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['status'] not in ('pending', 'countered'):
        conn.close()
        flash('该议价已处理！', 'warning')
        return redirect(url_for('my_negotiations'))
    
    cursor.execute('''
        UPDATE negotiations SET counter_price = ?, status = 'countered', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (counter_price, negotiation_id))
    conn.commit()
    conn.close()
    
    flash(f'已还价 {counter_price} 金币，等待买家确认。', 'success')
    return redirect(url_for('my_negotiations'))

@app.route('/negotiate/<int:negotiation_id>/cancel', methods=['POST'])
@login_required
def cancel_negotiation(negotiation_id):
    """取消议价（买家操作）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM negotiations WHERE id = ?', (negotiation_id,))
    negotiation = cursor.fetchone()
    
    if not negotiation:
        conn.close()
        flash('议价不存在！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['buyer_id'] != session['user_id']:
        conn.close()
        flash('无权操作！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['status'] not in ('pending', 'countered'):
        conn.close()
        flash('该议价已处理！', 'warning')
        return redirect(url_for('my_negotiations'))
    
    cursor.execute('UPDATE negotiations SET status = ? WHERE id = ?',
                   ('cancelled', negotiation_id))
    conn.commit()
    conn.close()
    
    flash('已取消议价', 'info')
    return redirect(url_for('my_negotiations'))

@app.route('/negotiate/<int:negotiation_id>/buy', methods=['POST'])
@login_required
def buy_from_negotiation(negotiation_id):
    """接受还价并购买"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.*, a.seller_id, a.title, a.price as original_price
        FROM negotiations n
        JOIN accounts a ON n.account_id = a.id
        WHERE n.id = ?
    ''', (negotiation_id,))
    negotiation = cursor.fetchone()
    
    if not negotiation:
        conn.close()
        flash('议价不存在！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['buyer_id'] != session['user_id']:
        conn.close()
        flash('无权操作！', 'danger')
        return redirect(url_for('my_negotiations'))
    
    if negotiation['status'] != 'countered':
        conn.close()
        flash('卖家尚未还价！', 'warning')
        return redirect(url_for('my_negotiations'))
    
    final_price = negotiation['counter_price']
    
    # 检查保险选项
    buy_insurance = request.form.get('buy_insurance') == '1'
    insurance_amount = round(final_price * 0.1, 2) if buy_insurance else 0
    total_price = final_price + insurance_amount
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    buyer = cursor.fetchone()
    
    if buyer['balance'] < total_price:
        conn.close()
        if buy_insurance:
            flash(f'余额不足！购买此账号（含保险）需要 {total_price} 金币。', 'danger')
        else:
            flash('余额不足！请充值。', 'danger')
        return redirect(url_for('my_negotiations'))
    
    # 执行交易
    try:
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?',
                       (total_price, session['user_id']))
        
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                       (final_price, negotiation['seller_id']))
        
        cursor.execute('UPDATE accounts SET status = ? WHERE id = ?',
                       ('sold', negotiation['account_id']))
        
        cursor.execute('UPDATE negotiations SET status = ? WHERE id = ?',
                       ('accepted', negotiation_id))
        
        # 拒绝其他议价
        cursor.execute('''
            UPDATE negotiations SET status = 'rejected'
            WHERE account_id = ? AND id != ?
        ''', (negotiation['account_id'], negotiation_id))
        
        cursor.execute('INSERT INTO transactions (buyer_id, account_id, price, insurance) VALUES (?, ?, ?, ?)',
                       (session['user_id'], negotiation['account_id'], final_price, insurance_amount))
        
        conn.commit()
        
        if buy_insurance:
            flash(f'购买成功！您已购买 "{negotiation["title"]}"，并获得{insurance_amount}金币的找回保险！', 'success')
        else:
            flash(f'购买成功！您已购买 "{negotiation["title"]}"！', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'交易失败：{str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('my_accounts'))

# ==================== 初始化 ====================

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    # 添加议价表
    add_negotiations_table()
    # 添加图片字段
    add_images_column()
    # 添加保险字段
    add_insurance_column()
    # 启动应用（host='0.0.0.0' 允许局域网访问）
    app.run(debug=True, port=5000, host='0.0.0.0')
