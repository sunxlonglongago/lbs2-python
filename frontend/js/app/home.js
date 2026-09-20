// Index page: port of default.asp (normal and list view modes).
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

function canEditArticle(article) {
  const user = LBS.user;
  if (!user) {
    return false;
  }
  const level = (user.rights && user.rights.edit) || 0;
  return level > 1 || (level === 1 && user.id === article.author_id);
}

function canDeleteArticle(article) {
  const user = LBS.user;
  if (!user) {
    return false;
  }
  const level = (user.rights && user.rights.delete) || 0;
  return level > 1 || (level === 1 && user.id === article.author_id);
}

function renderNormal(items, keywords) {
  const html = items.map((article) => {
    const rows = [];
    if (article.selected) {
      rows.push(R.titleIcon('icon_star.gif', LBS.t('selected'), LBS.t('selected')));
    }
    if (article.locked || article.category.locked) {
      rows.push(R.titleIcon('icon_lock.gif', LBS.t('locked'), LBS.t('locked')));
    }
    const title = article.title_html || R.escapeHtml(article.title);
    let titleHtml = '<a href="' + R.articleUrl(article.id) + '">' + title + '</a>';
    if (article.mode > 1) {
      titleHtml += ' <span class="comment-text">[' + article.mode + ']</span> ';
    }
    const label = '[ ' + R.escapeHtml(article.post_time) + ' | ' + LBS.t('author') +
      ': <a href="' + R.userUrl(article.author_id) + '">' +
      R.escapeHtml(article.author) + '</a>' +
      (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(article.ip) : '') +
      ' ]';

    const actions = [];
    if (canEditArticle(article)) {
      actions.push('<a href="article.asp?act=edit&amp;id=' + article.id +
        '" title="' + LBS.t('edit') + '"><img src="' + R.image('icon_edit.gif') +
        '" alt="' + LBS.t('edit') + '" /></a>');
    }
    if (canDeleteArticle(article)) {
      actions.push('<a href="article.asp?act=delete&amp;id=' + article.id +
        '" title="' + LBS.t('delete') + '" id="delete-' + article.id +
        '"><img src="' + R.image('icon_del.gif') + '" alt="' + LBS.t('delete') +
        '" /></a>');
    }
    actions.push(
      '<a href="' + R.categoryUrl(article.category.id) + '">' + LBS.t('category') +
        ': ' + R.escapeHtml(article.category.name) + '</a>'
    );
    actions.push('<a href="article.asp?id=' + article.id + '">' +
      LBS.t('permalink') + '</a>');
    actions.push('<a href="' + R.articleUrl(article.id) + '#commentbox">' +
      LBS.t('comments') + ': ' + article.comment_count + '</a>');
    actions.push('<a href="trackback.asp?act=list&amp;id=' + article.id + '">' +
      LBS.t('trackbacks') + ': ' + article.trackback_count + '</a>');
    actions.push(LBS.t('views') + ': ' + article.view_count);

    const more = article.has_more
      ? '...<br /><br /><a href="' + R.articleUrl(article.id) + '"><b>' +
        LBS.t('read_more') + '</b></a>'
      : '';

    return [
      '<div class="textbox">',
      '  <div class="textbox-title">',
      '    <h4>',
      rows.join('') + titleHtml,
      '    </h4>',
      '    <div class="textbox-label">' + label + '</div>',
      '  </div>',
      '  <div class="textbox-content">',
      article.content_html + more,
      '  </div>',
      '  <div class="textbox-bottom">',
      actions.join(' | '),
      '  </div>',
      '</div>',
    ].join('\n');
  });
  return html.join('\n');
}

function renderList(items) {
  const rows = items.map((article) => {
    const title = article.title_html || R.escapeHtml(article.title);
    const marks = [];
    if (article.selected) {
      marks.push(R.titleIcon('icon_star.gif', LBS.t('selected'), LBS.t('selected')));
    }
    if (article.locked || article.category.locked) {
      marks.push(R.titleIcon('icon_lock.gif', LBS.t('locked'), LBS.t('locked')));
    }
    const actions = [];
    if (canEditArticle(article)) {
      actions.push('<a href="article.asp?act=edit&amp;id=' + article.id +
        '" title="' + LBS.t('edit') + '"><img src="' + R.image('icon_edit.gif') +
        '" alt="' + LBS.t('edit') + '" /></a>');
    }
    if (canDeleteArticle(article)) {
      actions.push('<a href="article.asp?act=delete&amp;id=' + article.id +
        '" title="' + LBS.t('delete') + '"><img src="' + R.image('icon_del.gif') +
        '" alt="' + LBS.t('delete') + '" /></a>');
    }
    return [
      '  <tr>',
      '  <td class="listbox-entry">',
      '    <a href="' + R.categoryUrl(article.category.id) + '">[' +
        R.escapeHtml(article.category.name) + ']</a>',
      '    <a href="' + R.articleUrl(article.id) + '"> ' + title + '</a>' +
        marks.join(''),
      '  </td>',
      '  <td class="listbox-entry" style="word-break: normal;">',
      (actions.length ? '    ' + actions.join(' | ') + ' |' : ''),
      '    <a href="' + R.userUrl(article.author_id) + '" title="' + LBS.t('author') +
        '">' + R.escapeHtml(article.author) + '</a>',
      '  </td>',
      '  <td class="listbox-entry" width="70">' +
        R.escapeHtml(article.post_time.slice(0, 10)) + '</td>',
      '  <td class="listbox-entry" width="100"><a href="' + R.articleUrl(article.id) +
        '#commentbox" title="' + LBS.t('comments') + '">' + article.comment_count +
        '</a> | ' + article.trackback_count + ' | ' + article.view_count + '</td>',
      '  </tr>',
    ].join('\n');
  });
  return [
    '<div class="listbox">',
    '<div class="listbox-table">',
    '<table cellpadding="2" cellspacing="2" width="100%">',
    rows.join('\n'),
    '</table>',
    '</div>',
    '</div>',
  ].join('\n');
}

function filterSummary(filters) {
  const parts = [];
  if (filters.category) {
    parts.push(LBS.t('category') + ': ' + filters.category);
  }
  if (filters.date) {
    parts.push(R.escapeHtml(filters.date));
  }
  if (filters.keywords && filters.keywords.length) {
    parts.push(LBS.t('search') + ': ' + R.escapeHtml(filters.keywords.join(' ')));
  }
  return parts.length ? parts.join(' | ') + ' | ' : '';
}

async function render() {
  const search = R.params().toString();
  const data = await LBS.get('/api/articles' + (search ? '?' + search : ''));

  R.setText('viewModeLabel', LBS.t('view_mode'));
  R.setText('modeNormal', LBS.t('normal'));
  R.setText('modeList', LBS.t('list'));

  const sidebar = LBS.data.site;
  void sidebar;

  // The announcement only shows on the first page, like default.asp.
  const announcement = LBS.data.announcement || {};
  if (announcement.show && data.page === 1) {
    R.setText('announceTime', announcement.date);
    R.setHtml('announceBody', announcement.html);
    R.show('announceBox', true);
  }

  const listNode = R.byId('articleList');
  if (!data.total) {
    listNode.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      LBS.t('no_article') + '</div></div>';
  } else if (data.mode === 1) {
    listNode.innerHTML = renderList(data.items);
  } else {
    listNode.innerHTML = renderNormal(data.items, data.filters.highlight);
  }

  const summary = filterSummary(data.filters);
  R.setHtml('topPages', summary + data.page_links);
  R.setHtml('bottomPages', data.page_links);
}

async function main() {
  await window.LBSLayout.mount({
    onReady() {
      return render();
    },
  });
}

main().catch((error) => {
  const node = R.byId('articleList');
  if (node) {
    node.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      R.escapeHtml(error.message) + '</div></div>';
  }
});
