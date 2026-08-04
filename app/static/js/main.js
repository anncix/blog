/* 主交互：主题切换、移动端菜单、返回顶部、评论表单、图片懒加载 */
(function () {
  const root = document.documentElement;

  // ---------- 主题 ----------
  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    // 同步 Bootstrap 主题
    root.setAttribute('data-bs-theme', theme === 'dark' ? 'dark' : 'light');
    try { localStorage.setItem('blog-theme', theme); } catch (e) {}
  }
  function resolveTheme() {
    const saved = (function () { try { return localStorage.getItem('blog-theme'); } catch (e) { return null; } })();
    if (saved) return saved;
    const mode = (root.getAttribute('data-theme-mode') || 'system');
    if (mode === 'dark') return 'dark';
    if (mode === 'light') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  root.setAttribute('data-theme-mode', root.getAttribute('data-theme-mode') || 'system');
  applyTheme(resolveTheme());

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const cur = root.getAttribute('data-theme');
      applyTheme(cur === 'dark' ? 'light' : 'dark');
    });
  }

  // ---------- 移动端菜单 ----------
  const navToggle = document.getElementById('navToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  if (navToggle && mobileMenu) {
    navToggle.addEventListener('click', () => mobileMenu.classList.toggle('open'));
  }

  // ---------- 返回顶部 ----------
  const backTop = document.getElementById('backTop');
  if (backTop) {
    window.addEventListener('scroll', function () {
      backTop.classList.toggle('show', window.scrollY > 300);
    });
    backTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ---------- 评论：回复按钮 ----------
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.reply-btn');
    if (btn) {
      const parentId = document.getElementById('parentId');
      const cancel = document.getElementById('cancelReply');
      const author = btn.dataset.author;
      if (parentId) parentId.value = btn.dataset.commentId;
      if (cancel) cancel.classList.remove('d-none');
      const ta = document.querySelector('#commentForm textarea');
      if (ta) {
        ta.focus();
        if (author) ta.placeholder = '回复 @' + author + '：';
      }
    }
  });
  const cancelReply = document.getElementById('cancelReply');
  if (cancelReply) {
    cancelReply.addEventListener('click', function () {
      document.getElementById('parentId').value = '';
      this.classList.add('d-none');
      const ta = document.querySelector('#commentForm textarea');
      if (ta) ta.placeholder = '写下你的评论…';
    });
  }

  // ---------- 图片懒加载 ----------
  function initLazy() {
    const imgs = document.querySelectorAll('img[data-src]');
    imgs.forEach(img => {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    });
  }
  window.__initLazy = initLazy;
  initLazy();
})();