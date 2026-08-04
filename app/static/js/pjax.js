/* Pjax 无刷新加载：拦截内部链接，获取页面并替换内容区 */
(function () {
  const content = document.getElementById('content');
  if (!content) return;

  function applyThemeFromPage(html) {
    // 从响应中解析 data-theme / data-accent 并应用
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const root = doc.documentElement;
    const attrs = ['data-theme', 'data-accent'];
    attrs.forEach(a => {
      const v = root.getAttribute(a);
      if (v) {
        if (a === 'data-theme') setTheme(v);
        else document.documentElement.setAttribute(a, v);
      }
    });
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('blog-theme', theme); } catch (e) {}
  }

  function load(url, title) {
    content.classList.add('pjax-loading');
    fetch(url, { headers: { 'X-PJAX': 'true' } })
      .then(res => res.text())
      .then(html => {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const newContent = doc.getElementById('content');
        if (newContent) {
          content.innerHTML = newContent.innerHTML;
          window.scrollTo(0, 0);
          if (title) document.title = title;
          else if (doc.title) document.title = doc.title;
          applyThemeFromPage(html);
          // 重新替换返回顶部按钮引用（主入口为全局监听，无需重建）
          if (window.__initLazy) window.__initLazy();
        } else {
          location.href = url;
        }
      })
      .catch(() => location.href = url)
      .finally(() => content.classList.remove('pjax-loading'));
  }

  document.addEventListener('click', function (e) {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('//')) return;
    if (a.hasAttribute('target')) return;
    if (a.origin && a.origin !== location.origin) return;
    e.preventDefault();
    if (history.state && history.state.url === href) {
      load(href, a.title);
    } else {
      history.pushState({ url: href }, '', href);
      load(href, a.title);
    }
  });

  window.addEventListener('popstate', function () {
    const url = location.pathname + location.search;
    load(url, document.title);
  });

  // 暴露主题设置供 main.js 使用
  window.__setTheme = setTheme;
})();