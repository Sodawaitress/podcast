/**
 * 魔法光标效果 - 粉紫色主题
 * 这个脚本创建一个跟随鼠标的粉紫色光标效果和魔法星星
 */
document.addEventListener('DOMContentLoaded', function() {
  // 创建魔法光标元素
  const cursor = document.createElement('div');
  cursor.classList.add('magic-cursor');
  document.body.appendChild(cursor);
  
  // 跟随鼠标移动
  document.addEventListener('mousemove', function(e) {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });
  
  // 鼠标悬停在链接和按钮上时放大光标
  const interactiveElements = document.querySelectorAll('a, button, .button, input[type="submit"]');
  interactiveElements.forEach(element => {
    element.addEventListener('mouseenter', () => {
      cursor.classList.add('grow');
      
      // 创建魔法星星
      createMagicStars(e.clientX, e.clientY);
    });
    
    element.addEventListener('mouseleave', () => {
      cursor.classList.remove('grow');
    });
  });
  
  // 点击时创建额外的魔法星星
  document.addEventListener('click', function(e) {
    createMagicStars(e.clientX, e.clientY);
  });
  
  // 创建魔法星星函数
  function createMagicStars(x, y) {
    const stars = document.createElement('div');
    stars.classList.add('magic-stars');
    stars.style.left = x + 'px';
    stars.style.top = y + 'px';
    document.body.appendChild(stars);
    
    // 1.5秒后移除星星元素（动画结束后）
    setTimeout(() => {
      stars.remove();
    }, 1500);
  }
});