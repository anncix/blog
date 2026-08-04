/* 后台：高亮当前导航 */
(function () {
  const path = location.pathname;
  const links = document.querySelectorAll('.admin-nav-link');
  links.forEach(a => {
    const href = a.getAttribute('href');
    if (href === '/admin' && path === '/admin') a.classList.add('active');
    else if (href && href !== '/admin' && path.startsWith(href)) a.classList.add('active');
  });
})();