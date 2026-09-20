// Guestbook page: port of gbook.asp (outputGuestBook and outputEditEntry).
import './api.js';
import './render.js';
import './layout.js';
import './commentform.js';

const R = window.LBSRender;

function entryHtml(entry) {
  const rows = [];
  rows.push('<div class="gbbox">');
  rows.push('  <div class="gbbox-content">');
  rows.push('    <div class="gbbox-title">');
  rows.push('      <a href="' + R.userUrl(entry.user_id) + '">' +
    R.escapeHtml(entry.username) + (entry.user_id === 0 ? '*' : '') + '</a>');
  rows.push('      <div class="gbbox-label">');
  rows.push('      [ ' + R.escapeHtml(entry.post_time) +
    (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(entry.ip) : '') + ' ]');
  if (entry.can_edit) {
    rows.push('        &nbsp;<a href="gbook.asp?act=edit&amp;id=' + entry.id +
      '" title="' + LBS.t('edit') + '/' + LBS.t('reply') + '"><img src="' +
      R.image('icon_edit.gif') + '" alt="' + LBS.t('edit') + '/' + LBS.t('reply') +
      '"></a>');
  }
  if (entry.can_delete) {
    rows.push('        &nbsp;<a href="gbook.asp?act=delete&amp;id=' + entry.id +
      '" title="' + LBS.t('delete') + '"><img src="' + R.image('icon_del.gif') +
      '" alt="' + LBS.t('delete') + '"></a>');
  }
  rows.push('      </div>');
  rows.push('    </div>');
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
  if (entry.has_reply) {
    rows.push('  <div class="gbbox-reply">');
    rows.push('    <div class="gbbox-reply-title">' +
      R.escapeHtml(entry.reply_username));
    rows.push('    <div class="gbbox-reply-label">[ ' +
      R.escapeHtml(entry.reply_time) + ' ]</div>');
    rows.push('    </div>');
    if (entry.visible) {
      rows.push('    ' + entry.reply_html);
    } else {
      rows.push('    <div class="hidden-note">' + LBS.t('hidden_comment') + '</div>');
    }
    rows.push('  </div>');
  }
  rows.push('</div>');
  return rows.join('\n');
}

function showMessage(style, title, content, target, auto) {
  R.setHtml(
    'editorMount',
    R.messageBox(R.escapeHtml(title), content, {
      style: style,
      target: target,
      linkText: LBS.t('redirect'),
      auto: auto,
    })
  );
  R.show('editorMount', true);
  R.show('guestbookTop', false);
  R.show('guestbookList', false);
  R.show('commentFormMount', false);
}

function renderForm() {
  R.setHtml('commentFormMount', window.LBSCommentForm.html({
    action: 'gbook.asp?act=save',
    title: LBS.t('post_comment'),
    ubbFlags: '110011',
  }));
  window.LBSCommentForm.wire(async (payload) => {
    try {
      await LBS.post('/api/guestbook', payload);
      showMessage('messagebox', LBS.t('done'), LBS.t('comment_save_done'),
        'gbook.asp', true);
    } catch (error) {
      const messages = (error.data && error.data.errors) || [error.message];
      showMessage('errorbox', LBS.t('error'), R.errorList(messages),
        'javascript:window.history.back();', false);
    }
  });
}

async function renderList() {
  const search = R.params().toString();
  const data = await LBS.get('/api/guestbook' + (search ? '?' + search : ''));

  const list = R.byId('guestbookList');
  if (!data.total) {
    list.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      LBS.t('no_entry') + '</div></div>';
  } else {
    list.innerHTML = data.items.map(entryHtml).join('\n');
  }
  const searchLabel = data.filters.keywords.length
    ? LBS.t('search') + ': ' + R.escapeHtml(data.filters.keywords.join(' ')) + ' | '
    : '';
  const summary = data.total + LBS.t('entries') + ' | ' + data.page_links;
  R.setHtml('guestbookPages', searchLabel + summary);
  R.setHtml('guestbookBottomPages', data.page_links);

  if (data.can_post) {
    renderForm();
  } else {
    R.setText('guestbookDisabled', LBS.t('comment_disabled'));
    R.show('guestbookDisabled', true);
  }
}

async function renderEditForm(entryId) {
  if (!LBS.user) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'gbook.asp', false);
    return;
  }
  try {
    const data = await LBS.get('/api/guestbook/' + entryId);
    const entry = data.entry;
    R.setHtml('editorMount', window.LBSCommentForm.html({
      action: 'gbook.asp?act=update&id=' + entryId,
      title: LBS.t('edit_gbook_entry'),
      content: entry.content,
      reply: entry.reply,
      hidden: entry.hidden,
      ubbFlags: entry.ubb_flags,
      showReplyArea: entry.show_reply_area,
      submitLabel: LBS.t('save_change'),
    }));
    R.show('editorMount', true);
    R.show('guestbookTop', false);
    R.show('guestbookList', false);
    R.show('commentFormMount', false);
    window.LBSCommentForm.wire(async (payload) => {
      try {
        await LBS.patch('/api/guestbook/' + entryId, payload);
        showMessage('messagebox', LBS.t('done'), LBS.t('comment_save_done'),
          'gbook.asp', true);
      } catch (error) {
        const messages = (error.data && error.data.errors) || [error.message];
        showMessage('errorbox', LBS.t('error'), R.errorList(messages),
          'javascript:window.history.back();', false);
      }
    });
  } catch (error) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'gbook.asp', false);
  }
}

async function deleteEntry(entryId) {
  if (!window.confirm(LBS.t('confirm_delete_comment') + '?')) {
    window.location.href = 'gbook.asp';
    return;
  }
  try {
    const response = await fetch(LBS.api('/api/guestbook/' + entryId), {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (!response.ok) {
      throw new Error('delete_failed');
    }
    showMessage('messagebox', LBS.t('done'), LBS.t('comment_delete_done'),
      'gbook.asp', true);
  } catch (error) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'gbook.asp', false);
  }
}

async function main() {
  await window.LBSLayout.mount({});
  const act = (R.params().get('act') || '').toLowerCase();
  const id = R.intParam('id', 0);
  if (act === 'edit' && id) {
    await renderEditForm(id);
    return;
  }
  if (act === 'delete' && id) {
    await deleteEntry(id);
    return;
  }
  await renderList();
}

main().catch((error) => {
  const node = R.byId('guestbookList');
  if (node) {
    node.innerHTML = '<div class="no-entry"><div class="no-entry-message">' +
      R.escapeHtml(error.message) + '</div></div>';
  }
});
