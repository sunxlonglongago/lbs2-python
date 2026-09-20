// Trackback list page: port of trackback.asp.
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

function entryHtml(entry) {
  const rows = [];
  rows.push('<div class="trackbackbox">');
  rows.push('  <div class="trackbackbox-title">');
  rows.push('    <img src="' + R.image('icon_trackback.gif') + '" alt="' +
    LBS.t('trackback') + '" />');
  rows.push('    <b><a href="' + R.escapeHtml(entry.url) + '" title="' +
    R.escapeHtml(entry.title) + '" target="_blank">' + entry.title_html + '</a></b>');
  rows.push('    <div class="trackbackbox-label">');
  rows.push('      [  ' + R.escapeHtml(entry.blog) + ' | ' +
    R.escapeHtml(entry.time) +
    (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(entry.ip) : '') + ' ]');
  if (LBS.user && canDelete(entry)) {
    rows.push('      &nbsp;<a href="trackback.asp?act=delete&amp;id=' + entry.id +
      '"><img src="' + R.image('icon_del.gif') + '" alt="' + LBS.t('delete') +
      '"></a>');
  }
  rows.push('    </div>');
  rows.push('  </div>');
  rows.push('  <div class="trackbackbox-content">' + entry.excerpt_html +
    '<br /><br />');
  rows.push('    <a href="article.asp?id=' + entry.article_id + '">&raquo; ' +
    R.escapeHtml(entry.article_title) + '</a>');
  rows.push('  </div>');
  rows.push('</div>');
  return rows.join('\n');
}

function canDelete(entry) {
  const level = (LBS.user.rights && LBS.user.rights.delete) || 0;
  return LBS.user.group_id === 1 || level > 1 ||
    (level === 1 && LBS.user.id === entry.article_author_id);
}

function showMessage(style, content) {
  R.setHtml('trackbackList', R.messageBox(
    style === 'error' ? LBS.t('error') : LBS.t('done'),
    content,
    {
      style: style === 'error' ? 'errorbox' : 'messagebox',
      target: 'default.asp',
      linkText: LBS.t('redirect'),
      auto: style !== 'error',
    }
  ));
}

async function main() {
  await window.LBSLayout.mount({});
  const params = R.params();
  const act = (params.get('act') || 'list').toLowerCase();
  const id = R.intParam('id', 0);

  if (act === 'delete' && id) {
    if (!window.confirm(LBS.t('confirm_delete_trackback') + '?')) {
      window.location.href = 'trackback.asp?act=list';
      return;
    }
    try {
      const response = await fetch(LBS.api('/api/trackbacks/' + id), {
        method: 'DELETE',
        credentials: 'same-origin',
      });
      if (!response.ok) {
        throw new Error('delete_failed');
      }
      showMessage('done', LBS.t('trackback_delete_done'));
    } catch (error) {
      showMessage('error', LBS.t('no_rights'));
    }
    return;
  }

  const search = params.toString();
  const data = await LBS.get('/api/trackbacks' + (search ? '?' + search : ''));
  const list = R.byId('trackbackList');
  if (!data.total) {
    list.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      LBS.t('no_entry') + '</div></div>';
  } else {
    list.innerHTML = data.items.map(entryHtml).join('\n');
  }
  const summary = LBS.t('trackbacks') + ' | ' +
    (data.filters.keywords.length
      ? LBS.t('search') + ': ' + R.escapeHtml(data.filters.keywords.join(' ')) + ' | '
      : '') + data.page_links;
  R.setHtml('trackbackPages', summary);
  R.setHtml('trackbackBottomPages', LBS.t('trackbacks') + ' | ' + data.page_links);
}

main();
