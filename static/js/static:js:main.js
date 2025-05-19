// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取模态框元素
    const modal = document.getElementById('alternate-links-modal');
    const modalLink = document.getElementById('alternate-links');
    const closeBtn = document.querySelector('.close');
    
    // 如果找到了这些元素
    if (modal && modalLink && closeBtn) {
        // 点击链接时显示模态框
        modalLink.addEventListener('click', function() {
            modal.style.display = 'block';
        });
        
        // 点击关闭按钮隐藏模态框
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
        
        // 点击模态框外部区域关闭
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // 复制链接到剪贴板的功能
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            alert('链接已复制到剪贴板');
        }).catch(function(err) {
            console.error('无法复制链接: ', err);
        });
    };
    
    // 音频播放相关功能
    const audioPlayers = document.querySelectorAll('audio');
    audioPlayers.forEach(function(player) {
        // 添加保存进度功能
        const episodeId = window.location.pathname.split('/').pop();
        
        // 从本地存储加载进度
        const savedTime = localStorage.getItem('podcast_progress_' + episodeId);
        if (savedTime) {
            player.currentTime = parseFloat(savedTime);
        }
        
        // 每5秒保存一次进度
        setInterval(function() {
            if (!player.paused) {
                localStorage.setItem('podcast_progress_' + episodeId, player.currentTime);
            }
        }, 5000);
        
        // 播放结束时清除进度
        player.addEventListener('ended', function() {
            localStorage.removeItem('podcast_progress_' + episodeId);
        });
    });
    
    // 添加简单的离线支持
    if ('serviceWorker' in navigator) {
        // 注册Service Worker
        navigator.serviceWorker.register('/sw.js').catch(function(error) {
            console.log('Service Worker registration failed:', error);
        });
    }
});

// 添加自动暗黑模式切换
(function() {
    // 检查用户偏好
    const darkModePreference = window.matchMedia('(prefers-color-scheme: dark)');
    
    function setDarkMode(isDark) {
        if (isDark) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
    
    // 初始设置
    setDarkMode(darkModePreference.matches);
    
    // 监听变化
    darkModePreference.addEventListener('change', function(e) {
        setDarkMode(e.matches);
    });
})();
