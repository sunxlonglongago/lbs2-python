// Comment list / edit page: port of comment.asp.
import './api.js';
import './render.js';
import './layout.js';
import './commentform.js';

const R = window.LBSRender;

function entryHtml(entry) {
  const rows = [];
  const icon = entry.author_id === entry.article_author_id
    ? 'icon_quote_author.gif'
    : 'icon_quote.gif';
  rows.push('<div class="commentbox">');
  rows.push('  <div class="commentbox-title">');
  rows.push('    <img src="' + R.image(icon) + '" alt="' + LBS.t('quote') + '" />');
  rows.push('    <b><a href="user.asp?act=view&amp;id=' + entry.author_id + '">' +
    R.escapeHtml(entry.author) + (entry.author_id === 0 ? '*' : '') + '</a></b>:');
  rows.push('    <a href="article.asp?id=' + entry.article_id + '">' +
    R.escapeHtml(entry.article_title) + '</a>');
  rows.push('    <div class="commentbox-label">');
  rows.push('      [ ' + R.escapeHtml(entry.post_time) +
    (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(entry.ip) : '') + ' ]');
  if (entry.can_edit) {
    rows.push('      &nbsp;<a href="comment.asp?act=edit&amp;id=' + entry.id +
      '" title="' + LBS.t('edit') + '"><img src="' + R.image('icon_edit.gif') +
      '" alt="' + LBS.t('edit') + '"></a>');
  }
  if (entry.can_delete) {
    rows.push('      &nbsp;<a href="comment.asp?act=delete&amp;id=' + entry.id +
      '" title="' + LBS.t('delete') + '"><img src="' + R.image('icon_del.gif') +
      '" alt="' + LBS.t('delete') + '"></a>');
  }
  rows.push('    </div>');
  rows.push('  </div>');
  rows.push('  <div id="comm_' + entry.id + '" class="commentbox-content">');
  if (entry.visible) {
    rows.push('    ' + entry.content_html);
    if (entry.edit_mark) {
      const parts = String(entry.edit_mark).split('$|$');
      rows.push('    <div class="editmark">[' + LBS.t('edited_by') + parts[0] +
        LBS.t('at') + parts[1] + ']</div>');
    }
  } else {
    rows.push('    <div class="hidden-note">' + LBS.t('hidden_comment') + '</div>');
  }
  rows.push('  </div>');
  rows.push('</div>');
  return rows.join('\n');
}

function showMessage(style, content, target) {
  R.setHtml('commentList', R.messageBox(
    style === 'error' ? LBS.t('error') : LBS.t('done'),
    content,
    {
      style: style === 'error' ? 'errorbox' : 'messagebox',
      target: target || 'comment.asp',
      linkText: LBS.t('redirect'),
      auto: style !== 'error',
    }
  ));
  R.show('commentListWrapper', false);
}

async function renderList(params) {
  const search = params.toString();
  const data = await LBS.get('/api/comments' + (search ? '?' + search : ''));
  const list = R.byId('commentList');
  if (!data.total) {
    list.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      LBS.t('no_entry') + '</div></div>';
  } else {
    list.innerHTML = data.items.map(entryHtml).join('\n');
  }
  const summary = LBS.t('comments') + ' | ' +
    (data.filters.keywords.length
      ? LBS.t('search') + ': ' + R.escapeHtml(data.filters.keywords.join(' ')) + ' | '
      : '') + data.page_links;
  R.setHtml('commentPages', summary);
  R.setHtml('commentBottomPages', LBS.t('comments') + ' | ' + data.page_links);
}

async function renderEditForm(commentId) {
  if (!LBS.user) {
    showMessage('error', LBS.t('no_rights'));
    return;
  }
  try {
    const data = await LBS.get('/api/comments/' + commentId);
    const comment = data.comment;
    R.setHtml('commentFormMount', window.LBSCommentForm.html({
      action: 'comment.asp?act=update&id=' + commentId,
      title: LBS.t('edit_comment_on'),
      content: comment.content,
      hidden: comment.hidden,
      ubbFlags: comment.ubb_flags,
      submitLabel: LBS.t('save_change'),
    }));
    R.show('commentListWrapper', false);
    window.LBSCommentForm.wire(async (payload) => {
      try {
        await LBS.patch('/api/comments/' + commentId, payload);
        showMessage('done', LBS.t('comment_save_done'), 'comment.asp');
      } catch (error) {
        const messages = (error.data && error.data.errors) || [error.message];
        showMessage('error', R.errorList(messages));
      }
    });
  } catch (error) {
    showMessage('error', LBS.t('no_rights'));
  }
}

async function deleteComment(commentId) {
  if (!window.confirm(LBS.t('confirm_delete_comment') + '?')) {
    window.location.href = 'comment.asp';
    return;
  }
  try {
    const response = await fetch(LBS.api('/api/comments/' + commentId), {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (!response.ok) {
      throw new Error('delete_failed');
    }
    showMessage('done', LBS.t('comment_delete_done'), 'comment.asp');
  } catch (error) {
    showMessage('error', LBS.t('no_rights'));
  }
}

async function main() {
  await window.LBSLayout.mount({});
  const params = R.params();
  const act = (params.get('act') || '').toLowerCase();
  const id = R.intParam('id', 0);

  if (act === 'edit' && id) {
    await renderEditForm(id);
    return;
  }
  if (act === 'delete' && id) {
    await deleteComment(id);
    return;
  }
  await renderList(params);
}

main().catch((error) => {
  showMessage('error', R.escapeHtml(error.message));
});
