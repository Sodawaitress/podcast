from flask import Flask, render_template, send_from_directory, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from feedgen.feed import FeedGenerator
import os
import secrets
import hashlib

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///podcast.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'media')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SITE_NAME'] = "灰礁播客"  # 站点名称
app.config['SITE_DESCRIPTION'] = "浮筝带来的灰礁上的声音"  # 站点描述
app.config['SITE_URL'] = 'http://127.0.0.1:5000'  # 本地开发时的URL

db = SQLAlchemy(app)

# 定义Episode模型
class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    audio_file = db.Column(db.String(100), nullable=False)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer, default=0)  # 以秒为单位
    password = db.Column(db.String(64), nullable=True)  # 可选密码保护
    
    def __repr__(self):
        return f'Episode({self.title})'

# 创建数据库表
with app.app_context():
    db.create_all()

# 上下文处理器 - 为所有模板提供站点信息
@app.context_processor
def inject_site_info():
    return dict(
        site_name=app.config['SITE_NAME'],
        site_description=app.config['SITE_DESCRIPTION'],
        site_url=app.config['SITE_URL']
    )

# 首页 - 显示所有播客列表
@app.route('/')
def index():
    episodes = Episode.query.order_by(Episode.pub_date.desc()).all()
    return render_template('index.html', episodes=episodes)

# 播客单集页面
@app.route('/episode/<int:episode_id>', methods=['GET', 'POST'])
def episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    
    # 如果有密码保护
    if episode.password:
        if request.method == 'POST':
            input_password = request.form.get('password')
            if hashlib.sha256(input_password.encode()).hexdigest() == episode.password:
                return render_template('episode.html', episode=episode, authenticated=True)
            else:
                return render_template('episode.html', episode=episode, authenticated=False, error="密码错误")
        return render_template('episode.html', episode=episode, authenticated=False)
    
    return render_template('episode.html', episode=episode, authenticated=True)

# 提供音频文件
@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# RSS Feed生成
@app.route('/feed.xml')
def feed():
    fg = FeedGenerator()
    fg.title(app.config['SITE_NAME'])
    fg.description(app.config['SITE_DESCRIPTION'])
    fg.link(href=app.config['SITE_URL'])
    fg.language('zh-CN')
    
    episodes = Episode.query.order_by(Episode.pub_date.desc()).all()
    
    for episode in episodes:
        # 跳过有密码的集数(在RSS中不包含私密内容)
        if episode.password:
            continue
            
        fe = fg.add_entry()
        fe.title(episode.title)
        fe.description(episode.description)
        fe.pubDate(episode.pub_date)
        
        # 创建音频文件的URL
        audio_url = f"{app.config['SITE_URL']}/media/{episode.audio_file}"
        fe.enclosure(audio_url, 0, 'audio/mpeg')
    
    return fg.rss_str(pretty=True), 200, {'Content-Type': 'application/xml'}

# 简单的上传界面 (真实使用时应添加身份验证)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        audio_file = request.files.get('audio_file')
        password = request.form.get('password')
        
        if audio_file:
            filename = audio_file.filename
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(audio_path)
            
            # 创建新的Episode
            new_episode = Episode(
                title=title,
                description=description,
                audio_file=filename
            )
            
            # 如果提供了密码，存储其哈希值
            if password:
                new_episode.password = hashlib.sha256(password.encode()).hexdigest()
            
            db.session.add(new_episode)
            db.session.commit()
            
            return redirect(url_for('index'))
    
    return render_template('upload.html')

from datetime import datetime

# 将这段代码添加到您的app.py文件中，放在其他上下文处理器旁边
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=True)