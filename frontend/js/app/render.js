// Small helpers shared by the page scripts.
const LBSRender = (() => {
  function byId(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    const node = byId(id);
    if (node) {
      node.textContent = value == null ? '' : String(value);
    }
    return node;
  }

  function setHtml(id, value) {
    const node = byId(id);
    if (node) {
      node.innerHTML = value == null ? '' : String(value);
    }
    return node;
  }

  function show(id, visible) {
    const node = byId(id);
    if (node) {
      node.style.display = visible ? 'block' : 'none';
    }
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/>/g, '&gt;')
      .replace(/</g, '&lt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function intParam(name, fallback) {
    const raw = params().get(name);
    const value = parseInt(raw == null ? '' : raw, 10);
    return Number.isNaN(value) ? fallback : value;
  }

  function imageFolder() {
    return (LBS.info && LBS.info.image_folder) || 'styles/default/images';
  }

  function articleUrl(id) {
    return 'article.asp?id=' + encodeURIComponent(id);
  }

  function categoryUrl(id) {
    return 'default.asp?cat=' + encodeURIComponent(id);
  }

  function userUrl(id) {
    return 'user.asp?id=' + encodeURIComponent(id);
  }

  function image(path) {
    return imageFolder() + '/' + path;
  }

  // Port of redirectMessage() in global.asp.
  function messageBox(title, content, options) {
    const settings = options || {};
    const style = settings.style || 'messagebox';
    const target = settings.target || 'default.asp';
    const linkText = settings.linkText || LBS.t('goback');
    const refresh = settings.auto
      ? '<meta http-equiv="refresh" content="3;url=' + target + '" />'
      : '';
    return [
      '<div id="mainWrapper">',
      '<center>',
      '<div class="' + style + '">',
      '  <div class="' + style + '-title">' + title + '</div>',
      '  <div class="' + style + '-content">' + content + '</div>',
      '  <div class="' + style + '-bottom"><a href="' + target + '">' + linkText +
        '</a></div>',
      '  ' + refresh,
      '</div>',
      '</center>',
      '</div>',
    ].join('\n');
  }

  // The ASP error dialogs show a bullet list of language strings.
  function errorList(errors) {
    return '<ul>' + errors
      .map((code) => '<li>' + LBS.t(code) + '</li>')
      .join('') + '</ul>';
  }

  // Sizes an em based icon next to a title, mirroring the ASP markup.
  function titleIcon(file, alt, title) {
    return (
      '<img src="' + image(file) + '" alt="' + escapeHtml(alt || '') +
      '" title="' + escapeHtml(title || alt || '') + '" />'
    );
  }

  return {
    byId,
    setText,
    setHtml,
    show,
    escapeHtml,
    params,
    intParam,
    imageFolder,
    articleUrl,
    categoryUrl,
    userUrl,
    image,
    titleIcon,
    messageBox,
    errorList,
  };
})();

window.LBSRender = LBSRender;
