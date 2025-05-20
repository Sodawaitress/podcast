// 终极星空效果 JavaScript

// 当页面加载完成时创建星空效果
document.addEventListener('DOMContentLoaded', function() {
    // 确保容器元素存在
    ensureContainers();
    
    // 创建原地闪烁的星星
    createTwinklingStars();
    
    // 创建流星系统
    createShootingStarSystem();
});

// 确保所有需要的容器都存在
function ensureContainers() {
    // 检查并创建原地闪烁星星容器
    if (!document.getElementById('staticStars')) {
        const staticStarsContainer = document.createElement('div');
        staticStarsContainer.id = 'staticStars';
        staticStarsContainer.className = 'static-stars';
        document.body.prepend(staticStarsContainer);
    }
    
    // 检查并创建流星容器
    if (!document.getElementById('shootingStars')) {
        const shootingStarsContainer = document.createElement('div');
        shootingStarsContainer.id = 'shootingStars';
        shootingStarsContainer.className = 'shooting-stars-container';
        document.body.prepend(shootingStarsContainer);
    }
}

// 创建原地闪烁的星星
function createTwinklingStars() {
    const staticStarsContainer = document.getElementById('staticStars');
    
    // 清空容器以防重复
    staticStarsContainer.innerHTML = '';
    
    // 创建大量不同大小的闪烁星星
    for (let i = 0; i < 150; i++) {
        const star = document.createElement('div');
        star.className = 'twinkling-star';
        
        // 随机大小 (0.5px - 3px)
        const size = Math.random() * 2.5 + 0.5;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        
        // 随机位置
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        
        // 随机闪烁延迟
        star.style.animationDelay = `${Math.random() * 5}s`;
        
        // 随机闪烁持续时间
        star.style.animationDuration = `${Math.random() * 3 + 2}s`;
        
        staticStarsContainer.appendChild(star);
    }
}

// 创建流星系统
function createShootingStarSystem() {
    const shootingStarsContainer = document.getElementById('shootingStars');
    
    // 初始创建几个流星
    for (let i = 0; i < 3; i++) {
        setTimeout(() => {
            createShootingStar(shootingStarsContainer);
        }, Math.random() * 3000);
    }
    
    // 周期性创建新的流星
    setInterval(() => {
        if (Math.random() > 0.5) { // 50%的几率创建新流星
            createShootingStar(shootingStarsContainer);
        }
    }, 2000);
}

// 创建单个流星
function createShootingStar(container) {
    const shootingStar = document.createElement('div');
    shootingStar.className = 'shooting-star';
    
    // 随机长度 (50-150px)
    const length = Math.random() * 100 + 50;
    shootingStar.style.width = `${length}px`;
    
    // 随机位置（总是从屏幕右侧边缘开始）
    const startPositionY = Math.random() * 70; // 限制在上部70%的区域
    shootingStar.style.right = '0';
    shootingStar.style.top = `${startPositionY}%`;
    
    // 随机角度 (15-45度)
    const angle = Math.random() * 30 + 15;
    shootingStar.style.transform = `rotate(${angle}deg)`;
    
    // 随机速度 (1.5-4秒)
    const duration = Math.random() * 2.5 + 1.5;
    shootingStar.style.animationDuration = `${duration}s`;
    
    // 添加流星到容器
    container.appendChild(shootingStar);
    
    // 动画结束后移除流星元素
    setTimeout(() => {
        shootingStar.remove();
    }, duration * 1000);
}