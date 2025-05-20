from flask import Flask, render_template, send_from_directory, url_for, request, redirect, jsonify
from datetime import datetime
import os
import secrets
import hashlib
import json
import base64

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

# 如果Cloudinary可用，则配置它
if cloudinary_available:
    cloudinary.config( 
        cloud_name = "dxm0ajjil",
        api_key = "286612799875297", 
        api_secret = "EkrlSu4mv50B9Aclc_a4US3ZdX4" 
    )

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

# 默认播客数据
def default_episodes():
    return [{
        'id': 0,
        'title': '欢迎收听灰礁播客',
        'description': '这是一个演示播客，用于验证样式是否正确加载。上传新的播客后此条目会保留。',
        'audio_file': 'https://docs.google.com/uc?export=download&id=1v6JDgNLlQB9cHIuWiUhpJrKp-s73V56j',
        'pub_date': '2025-05-20'
    }]

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

# 单集页面
@app.route('/episode/<int:episode_id>')
def episode(episode_id):
    if episode_id < len(EPISODES):
        return render_template('episode.html', episode=EPISODES[episode_id], authenticated=True)
    return "播客不存在", 404

# 上传页面
@app.route('/upload', methods=['GET', 'POST'])
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
                'pub_date': datetime.now().isoformat()
            }
            
            # 添加到内存列表
            EPISODES.append(new_episode)
            
            # 保存到Cloudinary
            if cloudinary_available:
                upload_episodes_to_cloudinary(EPISODES)
                
            return redirect(url_for('index'))
    
    # 传递正确的upload_preset到模板
    return render_template('upload.html', use_cloudinary=cloudinary_available, 
                          cloud_name="dxm0ajjil", 
                          upload_preset="podcast_upload")

# RSS Feed
@app.route('/feed.xml')
def feed():
    return "RSS Feed", 200

# 提供CSS文件 - 直接路由
@app.route('/static/css/new-style.css')
def css():
    return send_from_directory(os.path.join(app.static_folder, 'css'), 'new-style.css')

# 提供favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/x-icon')

# 状态检查端点
@app.route('/status')
def status():
    return jsonify({
        "status": "ok",
        "cloudinary_available": cloudinary_available,
        "requests_available": requests_available,
        "episodes_count": len(EPISODES),
        "static_url": url_for('static', filename='css/new-style.css'),
        "css_exists": os.path.exists(os.path.join(app.static_folder, 'css', 'new-style.css'))
    })

if __name__ == '__main__':
    app.run(debug=True)