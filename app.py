from flask import Flask, render_template, send_from_directory, url_for, request, redirect, jsonify
from datetime import datetime
import os
import secrets
import hashlib
import json

# 尝试导入cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    cloudinary_available = True
except ImportError:
    cloudinary_available = False
    print("警告: Cloudinary模块未找到。将使用本地文件上传。")

# 尝试导入feedgen
try:
    from feedgen.feed import FeedGenerator
    feedgen_available = True
except ImportError:
    feedgen_available = False
    print("警告: FeedGenerator模块未找到。RSS功能将被禁用。")

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SITE_NAME'] = "灰礁播客"  # 站点名称
app.config['SITE_DESCRIPTION'] = "浮筝带来的灰礁上的声音"  # 站点描述
app.config['SITE_URL'] = os.environ.get('SITE_URL', 'https://podcast-five-pink.vercel.app')  # 线上URL
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'media')

# 如果Cloudinary可用，则配置它
if cloudinary_available:
    cloudinary.config( 
        cloud_name = "@dxm0ajjil", 
        api_key = "286612799875297", 
        api_secret = "EkrlSu4mv50B9Aclc_a4US3ZdX4" 
    )

# 使用内存列表存储播客集
EPISODES = []

# 尝试从JSON文件加载现有播客数据（如果在本地开发）
def load_episodes():
    try:
        if os.path.exists('episodes.json'):
            with open('episodes.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载episodes.json失败: {e}")
    return []

# 尝试保存播客数据到JSON文件（如果在本地开发）
def save_episodes():
    try:
        with open('episodes.json', 'w', encoding='utf-8') as f:
            json.dump(EPISODES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存episodes.json失败: {e}")

# 初始化时加载播客
EPISODES = load_episodes()

# 上下文处理器 - 为所有模板提供站点信息
@app.context_processor
def inject_site_info():
    return dict(
        site_name=app.config['SITE_NAME'],
        site_description=app.config['SITE_DESCRIPTION'],
        site_url=app.config['SITE_URL'],
        current_year=datetime.now().year
    )

# 首页 - 显示所有播客列表
@app.route('/')
def index():
    # 按发布日期排序
    sorted_episodes = sorted(EPISODES, key=lambda x: x.get('pub_date', ''), reverse=True)
    return render_template('index.html', episodes=sorted_episodes)

# 播客单集页面
@app.route('/episode/<int:episode_id>', methods=['GET', 'POST'])
def episode(episode_id):
    # 检查ID是否有效
    if episode_id < 0 or episode_id >= len(EPISODES):
        return "播客不存在", 404
        
    episode = EPISODES[episode_id]
    
    # 如果有密码保护
    if episode.get('password'):
        if request.method == 'POST':
            input_password = request.form.get('password')
            if hashlib.sha256(input_password.encode()).hexdigest() == episode['password']:
                return render_template('episode.html', episode=episode, authenticated=True)
            else:
                return render_template('episode.html', episode=episode, authenticated=False, error="密码错误")
        return render_template('episode.html', episode=episode, authenticated=False)
    
    return render_template('episode.html', episode=episode, authenticated=True)

# 提供音频文件（仅在本地开发中使用）
@app.route('/media/<path:filename>')
def media(filename):
    # 检查文件名是否是URL
    if filename.startswith(('http://', 'https://')):
        return redirect(filename)
    # 本地文件
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# RSS Feed生成
@app.route('/feed.xml')
def feed():
    if not feedgen_available:
        return "RSS功能未启用，缺少必要的依赖项", 500
        
    fg = FeedGenerator()
    fg.title(app.config['SITE_NAME'])
    fg.description(app.config['SITE_DESCRIPTION'])
    fg.link(href=app.config['SITE_URL'])
    fg.language('zh-CN')
    
    # 按发布日期排序
    sorted_episodes = sorted(EPISODES, key=lambda x: x.get('pub_date', ''), reverse=True)
    
    for episode in sorted_episodes:
        # 跳过有密码的集数(在RSS中不包含私密内容)
        if episode.get('password'):
            continue
            
        fe = fg.add_entry()
        fe.title(episode['title'])
        fe.description(episode['description'])
        
        # 解析日期字符串为datetime对象
        pub_date = datetime.fromisoformat(episode['pub_date']) if isinstance(episode['pub_date'], str) else episode['pub_date']
        fe.pubDate(pub_date)
        
        # 创建音频文件的URL
        audio_url = episode['audio_file']
        # 如果URL不是以http开头，添加站点URL前缀
        if not audio_url.startswith(('http://', 'https://')):
            audio_url = f"{app.config['SITE_URL']}/media/{episode['audio_file']}"
            
        fe.enclosure(audio_url, 0, 'audio/mpeg')
    
    return fg.rss_str(pretty=True), 200, {'Content-Type': 'application/xml'}

# 上传播客
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        password = request.form.get('password')
        
        # 检查是否使用Cloudinary上传
        audio_url = request.form.get('audio_url')
        if audio_url and cloudinary_available:
            # Cloudinary模式 - 使用URL
            filename = audio_url
        else:
            # 传统模式 - 本地文件上传（仅在本地开发中使用）
            audio_file = request.files.get('audio_file')
            if not audio_file:
                return "没有选择文件", 400
                
            filename = audio_file.filename
            
            # 在Vercel上不会工作，但在本地开发可用
            try:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(audio_path)
            except Exception as e:
                print(f"保存文件失败: {e}")
                return "保存文件失败，请尝试使用Cloudinary上传", 500
        
        # 创建新的Episode
        new_episode = {
            'id': len(EPISODES),
            'title': title,
            'description': description,
            'audio_file': filename,
            'pub_date': datetime.now().isoformat()
        }
        
        # 如果提供了密码，存储其哈希值
        if password:
            new_episode['password'] = hashlib.sha256(password.encode()).hexdigest()
        
        # 添加到内存列表
        EPISODES.append(new_episode)
        
        # 尝试保存到JSON（仅本地开发）
        save_episodes()
        
        return redirect(url_for('index'))
    
    return render_template('upload.html', use_cloudinary=cloudinary_available)

# 状态检查端点，用于Vercel
@app.route('/status')
def status():
    return jsonify({
        "status": "ok",
        "episodes_count": len(EPISODES),
        "cloudinary_available": cloudinary_available,
        "feedgen_available": feedgen_available
    })

# 提供favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

if __name__ == '__main__':
    app.run(debug=True)