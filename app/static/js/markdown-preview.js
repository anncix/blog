/* 后台文章编辑器：Markdown 实时预览（本地最小实现，无需第三方库） */
(function () {
  const editor = document.getElementById('editor');
  const preview = document.getElementById('preview');
  const editBtn = document.getElementById('editModeBtn');
  const prevBtn = document.getElementById('previewModeBtn');
  if (!editor || !preview) return;

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function inline(s) {
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
    s = s.replace(/`(.+?)`/g, '<code>$1</code>');
    s = s.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');
    return s;
  }
  function render(src) {
    const lines = src.split('\n');
    let html = '';
    let inCode = false;
    let codeBuf = [];
    const flush = () => {
      if (inCode) {
        html += '<pre><code>' + esc(codeBuf.join('\n')) + '</code></pre>';
        codeBuf = [];
        inCode = false;
      }
    };
    lines.forEach(line => {
      if (/^```/.test(line)) {
        flush();
        inCode = !inCode;
        return;
      }
      if (inCode) { codeBuf.push(line); return; }
      if (/^#### /.test(line)) html += '<h4>' + inline(line.slice(5)) + '</h4>';
      else if (/^### /.test(line)) html += '<h3>' + inline(line.slice(4)) + '</h3>';
      else if (/^## /.test(line)) html += '<h2>' + inline(line.slice(3)) + '</h2>';
      else if (/^# /.test(line)) html += '<h1>' + inline(line.slice(2)) + '</h1>';
      else if (/^> /.test(line)) html += '<blockquote>' + inline(line.slice(2)) + '</blockquote>';
      else if (/^[-*] /.test(line)) html += '<li>' + inline(line.slice(2)) + '</li>';
      else if (line.trim() === '') html += '<br>';
      else html += '<p>' + inline(line) + '</p>';
    });
    flush();
    return html;
  }

  function showPreview() {
    preview.innerHTML = render(editor.value);
    preview.classList.remove('d-none');
    editor.classList.add('d-none');
    editBtn.classList.add('active');
    prevBtn.classList.remove('active');
  }
  function showEdit() {
    preview.classList.add('d-none');
    editor.classList.remove('d-none');
    editBtn.classList.remove('active');
    prevBtn.classList.add('active');
  }

  prevBtn.addEventListener('click', showPreview);
  editBtn.addEventListener('click', showEdit);
  editor.addEventListener('input', function () {
    if (!preview.classList.contains('d-none')) showPreview();
  });
})();