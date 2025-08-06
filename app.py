from flask import Flask, render_template, send_from_directory, url_for, request, redirect, jsonify
from flask import session, flash  # Add these imports
from datetime import datetime
import os
import secrets
import hashlib
import json
import base64
import functools  # Important for the decorator

# 尝试导入requests，在Vercel上首次部署时可能不可用
try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False
    print("警告: requests模块未找到。部分功能可能不可用。")

# 尝试导入cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    cloudinary_available = True
except ImportError:
    cloudinary_available = False
    print("警告: Cloudinary模块未找到。")

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SITE_NAME'] = "灰礁播客"
app.config['SITE_DESCRIPTION'] = "浮筝带来的灰礁上的声音"
app.config['SITE_URL'] = os.environ.get('SITE_URL', 'https://podcast-five-pink.vercel.app')

# 确保目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# 确保CSS目录存在
css_dir = os.path.join(app.static_folder, 'css')
ensure_dir(css_dir)

# Add a constant for admin password
ADMIN_PASSWORD = "greyreef2025"  # 修改为你想要的密码

# 如果Cloudinary可用，则配置它
if cloudinary_available:
    cloudinary.config( 
        cloud_name = "dxm0ajjil",
        api_key = "286612799875297", 
        api_secret = "EkrlSu4mv50B9Aclc_a4US3ZdX4" 
    )

# 默认播客数据
def default_episodes():
    return [{
        'id': 0,
        'title': '欢迎收听灰礁播客',
        'description': '这是一个演示播客，用于验证样式是否正确加载。你可以在上传新播客后删除它。',
        'audio_file': 'https://docs.google.com/uc?export=download&id=1v6JDgNLlQB9cHIuWiUhpJrKp-s73V56j',
        'pub_date': '2025-05-20',
        'is_demo': True  # 标记为演示播客
    }]

# 从Cloudinary下载JSON数据
def download_episodes_from_cloudinary():
    # 首次部署时，requests可能不可用，使用默认数据
    if not requests_available:
        return default_episodes()
        
    try:
        # 获取JSON文件URL
        url = cloudinary.utils.cloudinary_url("episodes_data", resource_type="raw")[0]
        # 下载JSON数据
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            # 如果文件不存在，返回默认数据
            return default_episodes()
    except Exception as e:
        print(f"从Cloudinary下载播客数据出错: {e}")
        return default_episodes()

# 上传JSON数据到Cloudinary
def upload_episodes_to_cloudinary(episodes):
    try:
        # 将数据转换为JSON字符串
        episodes_json = json.dumps(episodes, ensure_ascii=False)
        # 使用Cloudinary的raw上传功能
        result = cloudinary.uploader.upload(
            "data:application/json;base64," + base64.b64encode(episodes_json.encode('utf-8')).decode('utf-8'),
            resource_type="raw",
            public_id="episodes_data",
            overwrite=True
        )
        return result.get('secure_url')
    except Exception as e:
        print(f"上传播客数据到Cloudinary出错: {e}")
        return None

# 初始化播客数据
if cloudinary_available and requests_available:
    EPISODES = download_episodes_from_cloudinary()
else:
    # 如果Cloudinary不可用或requests不可用，使用默认数据
    EPISODES = default_episodes()

# 定义login_required装饰器 - 必须在使用前定义
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('admin_login'))
        return view(**kwargs)
    return wrapped_view

# 上下文处理器 - 为所有模板提供站点信息
@app.context_processor
def inject_site_info():
    return dict(
        site_name=app.config['SITE_NAME'],
        site_description=app.config['SITE_DESCRIPTION'],
        site_url=app.config['SITE_URL'],
        current_year=datetime.now().year
    )

# 首页
@app.route('/')
def index():
    return render_template('index.html', episodes=EPISODES)

# 管理员登录
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('upload'))
        else:
            error = "密码不正确"
    
    return render_template('admin_login.html', error=error)

@app.route('/episode/<int:episode_id>')
def episode(episode_id):
    # 查找ID匹配的播客
    matching_episode = None
    prev_url = None
    next_url = None
    
    # 找到当前播客
    for i, ep in enumerate(EPISODES):
        if ep['id'] == episode_id:
            matching_episode = ep
            
            # 计算上一集的URL
            if i > 0:
                prev_url = url_for('episode', episode_id=EPISODES[i-1]['id'])
            
            # 计算下一集的URL
            if i < len(EPISODES) - 1:
                next_url = url_for('episode', episode_id=EPISODES[i+1]['id'])
            
            break
            
    if matching_episode:
        return render_template('episode.html', 
                              episode=matching_episode, 
                              authenticated=True,
                              prev_url=prev_url,
                              next_url=next_url)
    return render_template('error.html', error="播客不存在", error_code="404"), 404

# 删除播客
@app.route('/delete/<int:episode_id>', methods=['POST'])
@login_required
def delete_episode(episode_id):
    global EPISODES
    
    # 查找要删除的播客索引
    episode_index = -1
    for i, ep in enumerate(EPISODES):
        if ep['id'] == episode_id:
            episode_index = i
            break
    
    if episode_index >= 0:
        # 删除播客
        removed = EPISODES.pop(episode_index)
        
        # 重新编号剩余播客
        for i, ep in enumerate(EPISODES):
            ep['id'] = i
        
        # 保存到Cloudinary
        if cloudinary_available:
            upload_episodes_to_cloudinary(EPISODES)
            
        return redirect(url_for('upload'))  # 改为返回上传页面而不是首页
    
    return render_template('error.html', error="播客不存在", error_code="404"), 404

# 上传页面
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        audio_url = request.form.get('audio_url')
        
        if audio_url:
            # 创建新的Episode
            new_episode = {
                'id': len(EPISODES),
                'title': title,
                'description': description,
                'audio_file': audio_url,
                'pub_date': datetime.now().strftime('%Y-%m-%d'),
                'is_demo': False  # 标记为非演示播客
            }
            
            # 添加到内存列表
            EPISODES.append(new_episode)
            
            # 保存到Cloudinary
            if cloudinary_available:
                upload_episodes_to_cloudinary(EPISODES)
                
            return redirect(url_for('index'))
    
    # 传递正确的upload_preset到模板
    return render_template('upload.html', 
                          episodes=EPISODES,  # 添加播客列表用于管理
                          use_cloudinary=cloudinary_available, 
                          cloud_name="dxm0ajjil", 
                          upload_preset="podcast_upload")

# RSS Feed
@app.route('/feed.xml')
def feed():
    return "RSS Feed", 200

@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except Exception as e:
        # 如果找不到favicon，返回一个空响应
        return '', 204

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="404 - 页面未找到", error_code="404"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error="500 - 服务器内部错误", error_code="500"), 500

# 状态检查端点
@app.route('/status')
def status():
    # 检查CSS文件是否存在
    css_path = os.path.join(app.static_folder, 'css', 'new-style.css')
    css_exists = os.path.exists(css_path)
    
    # 如果CSS文件不存在，尝试创建它
    if not css_exists:
        try:
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write('/* 这是一个占位CSS文件 */\n')
                f.write('body { background-color: #0b0b1e; color: white; }')
            css_exists = os.path.exists(css_path)
        except Exception as e:
            print(f"无法创建CSS文件: {e}")
    
    return jsonify({
        "status": "ok",
        "cloudinary_available": cloudinary_available,
        "requests_available": requests_available,
        "episodes_count": len(EPISODES),
        "static_url": url_for('static', filename='css/new-style.css'),
        "css_exists": css_exists,
        "css_path": css_path
    })
# 日历相关路由 - 添加到你现有的app.py文件中

# 日历页面路由
@app.route('/calendar')
def calendar_page():
    return send_from_directory('.', 'calendar.html')

# 日历数据API - 获取日历数据
@app.route('/api/calendar/load', methods=['GET'])
def load_calendar_data():
    if not cloudinary_available:
        return jsonify({"error": "Cloudinary not available"}), 500
    
    try:
        # 尝试从Cloudinary获取日历数据
        url = cloudinary.utils.cloudinary_url("calendar_data", resource_type="raw")[0]
        if requests_available:
            response = requests.get(url)
            if response.status_code == 200:
                return jsonify(response.json())
        
        # 如果没有数据，返回默认数据
        default_calendar_data = {
            "events": [
                {
                    "id": 1,
                    "title": "播客录制",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "time": "09:00",
                    "endTime": "10:30",
                    "location": "录音室",
                    "notes": "第10期节目录制"
                }
            ],
            "timeSettings": {
                "startHour": 6,
                "endHour": 22
            }
        }
        return jsonify(default_calendar_data)
        
    except Exception as e:
        print(f"加载日历数据出错: {e}")
        return jsonify({"error": "Failed to load calendar data"}), 500

# 日历数据API - 保存日历数据
@app.route('/api/calendar/save', methods=['POST'])
def save_calendar_data():
    if not cloudinary_available:
        return jsonify({"error": "Cloudinary not available"}), 500
    
    try:
        calendar_data = request.get_json()
        
        # 添加时间戳
        calendar_data['lastUpdated'] = datetime.now().isoformat()
        
        # 转换为JSON字符串并上传到Cloudinary
        calendar_json = json.dumps(calendar_data, ensure_ascii=False)
        result = cloudinary.uploader.upload(
            "data:application/json;base64," + base64.b64encode(calendar_json.encode('utf-8')).decode('utf-8'),
            resource_type="raw",
            public_id="calendar_data",
            overwrite=True
        )
        
        return jsonify({
            "success": True,
            "url": result.get('secure_url'),
            "saved_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"保存日历数据出错: {e}")
        return jsonify({"error": "Failed to save calendar data"}), 500

# 日历管理页面（需要登录）
@app.route('/calendar/admin')
@login_required
def calendar_admin():
    return render_template('calendar_admin.html')

# 在你现有的 upload 路由后面，添加一个指向日历的链接
# 你可以在 upload.html 模板中添加：
# <a href="/calendar" class="btn">📅 管理日程</a>

if __name__ == '__main__':
    app.run(debug=True)