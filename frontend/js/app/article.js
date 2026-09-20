// Article page: port of article.asp (outputArticle).
import './api.js';
import './render.js';
import './layout.js';
import './commentform.js';

const R = window.LBSRender;

function canEdit(article) {
  const user = LBS.user;
  if (!user) {
    return false;
  }
  const level = (user.rights && user.rights.edit) || 0;
  return level > 1 || (level === 1 && user.id === article.author_id);
}

function canDelete(article) {
  const user = LBS.user;
  if (!user) {
    return false;
  }
  const level = (user.rights && user.rights.delete) || 0;
  return level > 1 || (level === 1 && user.id === article.author_id);
}

function commentBox(comment, articleAuthorId) {
  const quoteIcon = comment.author_id === articleAuthorId
    ? 'icon_quote_author.gif'
    : 'icon_quote.gif';
  return [
    '<div class="commentbox" id="comment' + comment.id + '">',
    '  <a name="comment' + comment.id + '"></a>',
    '  <div class="commentbox-title">',
    '    <a href="javascript:doQuote(\'comm_' + comment.id + '\',\'' +
      R.escapeHtml(comment.author) + '\')"><img src="' + R.image(quoteIcon) +
      '" alt="' + LBS.t('quote') + '" /></a>',
    '    <b><a href="' + R.userUrl(comment.author_id) + '">' +
      R.escapeHtml(comment.author) + (comment.author_id === 0 ? '*' : '') +
      '</a></b>',
    '    <div class="commentbox-label">',
    '      [ ' + R.escapeHtml(comment.post_time) +
      (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(comment.ip) : '') +
      ' ]',
    '    </div>',
    '  </div>',
    '  <div id="comm_' + comment.id + '" class="commentbox-content">',
    '    ' + comment.content_html,
    '  </div>',
    '</div>',
  ].join('\n');
}

function trackbackBox(trackback) {
  return [
    '<div class="trackbackbox" id="trackback' + trackback.id + '">',
    '  <a name="trackback' + trackback.id + '"></a>',
    '  <div class="trackbackbox-title">',
    '    <img src="' + R.image('icon_trackback.gif') + '" alt="' +
      LBS.t('trackback') + '" />',
    '    <b><a href="' + R.escapeHtml(trackback.url) + '" target="_blank">' +
      R.escapeHtml(trackback.title) + '</a></b>',
    '    <div class="trackbackbox-label">',
    '      [  ' + R.escapeHtml(trackback.blog) + ' | ' +
      R.escapeHtml(trackback.post_time) +
      (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(trackback.ip) : '') +
      ' ]',
    '    </div>',
    '  </div>',
    '  <div class="trackbackbox-content">' + R.escapeHtml(trackback.excerpt) + '</div>',
    '</div>',
  ].join('\n');
}

function renderArticle(payload) {
  const article = payload.article;
  const site = LBS.info;
  document.title = article.title + ' - ' + (site.title || 'LBS');

  R.setHtml(
    'prevArticle',
    payload.previous
      ? '<a href="' + R.articleUrl(payload.previous.id) + '" title="' +
        R.escapeHtml(payload.previous.title) + '">&laquo; ' +
        R.escapeHtml(window.LBSLayout.cutString(payload.previous.title, 20)) + '</a>'
      : ''
  );
  R.setHtml(
    'nextArticle',
    payload.next
      ? '<a href="' + R.articleUrl(payload.next.id) + '" title="' +
        R.escapeHtml(payload.next.title) + '">' +
        R.escapeHtml(window.LBSLayout.cutString(payload.next.title, 20)) + ' &raquo;</a>'
      : ''
  );
  R.setHtml(
    'categoryLabel',
    '<a href="' + R.categoryUrl(article.category.id) + '">' + LBS.t('category') +
      ': ' + R.escapeHtml(article.category.name) + '</a>'
  );

  const marks = [];
  if (article.selected) {
    marks.push(R.titleIcon('icon_star.gif', LBS.t('selected'), LBS.t('selected')));
  }
  if (article.locked || article.category.locked) {
    marks.push(R.titleIcon('icon_lock.gif', LBS.t('locked'), LBS.t('locked')));
  }
  const label = '[ ' + R.escapeHtml(article.post_time) + ' | ' + LBS.t('author') +
    ': <a href="' + R.userUrl(article.author_id) + '">' +
    R.escapeHtml(article.author) + '</a>' +
    (LBS.user && LBS.user.group_id === 1 ? ' | ' + R.escapeHtml(article.ip) : '') +
    ' ]';
  let actions = '';
  if (canEdit(article)) {
    actions += ' &nbsp;<a href="article.asp?act=edit&amp;id=' + article.id +
      '" title="' + LBS.t('edit') + '"><img src="' + R.image('icon_edit.gif') +
      '" alt="' + LBS.t('edit') + '" /></a>';
  }
  if (canDelete(article)) {
    actions += ' &nbsp;<a href="#" id="deleteArticle" title="' + LBS.t('delete') +
      '"><img src="' + R.image('icon_del.gif') + '" alt="' + LBS.t('delete') +
      '" /></a>';
  }

  R.setHtml(
    'articleTitle',
    '  ' + marks.join('') + '\n  <h4>' + R.escapeHtml(article.title) + '</h4>\n' +
      '  <div class="textbox-label">' + label + actions + '</div>'
  );
  const deleteLink = R.byId('deleteArticle');
  if (deleteLink) {
    deleteLink.addEventListener('click', async (event) => {
      event.preventDefault();
      if (!window.confirm(LBS.t('confirm_delete_article') + '?')) {
        return;
      }
      try {
        await fetch(LBS.api('/api/articles/' + article.id), {
          method: 'DELETE',
          credentials: 'same-origin',
        }).then((response) => {
          if (!response.ok) {
            throw new Error('delete_failed');
          }
        });
        showMessage('messagebox', LBS.t('done'), LBS.t('delete_done'), 'default.asp', true);
      } catch (error) {
        showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
      }
    });
  }

  const urls = [];
  urls.push(
    '<img src="' + R.image('rss_comment.png') + '" class="meta-button" alt="' +
      LBS.t('comment_feed') + '" /> <b>' + LBS.t('comment_feed') + ':</b> ' +
      R.escapeHtml((site.base_url || '') + 'feed.asp?q=comment&amp;id=' + article.id)
  );
  if (site.features && site.features.trackback_in && !article.locked && article.mode < 4) {
    urls.push(
      '<br /><img src="' + R.image('utf8.png') +
        '" class="meta-button" alt="UTF-8 Encoding" /> <b>' + LBS.t('trackback_url') +
        ':</b> ' + R.escapeHtml((site.base_url || '') + 'trackback.asp?id=' + article.id)
    );
  }
  R.setHtml(
    'textboxContent',
    article.content_html +
      '\n      <div class="editmark" id="editMark" style="display: none"></div>' +
      '\n      <div class="textbox-urls">' + urls.join('') + '</div>'
  );
  if (article.edit_mark) {
    const parts = String(article.edit_mark).split('$|$');
    R.setHtml('editMark', '[' + LBS.t('edited_by') + parts[0] + LBS.t('at') +
      parts[1] + ']');
    R.show('editMark', true);
  }

  const comments = payload.comments.items || [];
  if (comments.length) {
    R.show('commentWrapper', true);
    R.setHtml(
      'commentTop',
      LBS.t('view_mode') + ': <a href="javascript:toggleComments(true,true);">' +
        LBS.t('show_all') + '</a> | <a href="javascript:toggleComments(true,false);">' +
        LBS.t('comments') + ': ' + article.comment_count +
        '</a> | <a href="javascript:toggleComments(false,true);">' +
        LBS.t('trackbacks') + ': ' + article.trackback_count +
        '</a> | <a href="javascript:toggleOrder();">' + LBS.t('toggle_order') +
        '</a> | ' + LBS.t('views') + ': ' + article.view_count + ' '
    );
    R.setHtml(
      'commentList',
      comments
        .map((entry) => (entry.type === 0
          ? commentBox(entry, article.author_id)
          : trackbackBox(entry)))
        .join('\n')
    );
    R.setHtml('commentPages', payload.comments.page_links || '');
  }

  if (payload.can_comment) {
    R.setHtml('commentFormMount', window.LBSCommentForm.html({
      action: 'comment.asp?act=save&logid=' + article.id,
      title: LBS.t('post_comment'),
      ubbFlags: '110011',
    }));
    wireCommentForm(article);
  } else {
    R.setText('commentDisabled', LBS.t('comment_disabled'));
    R.show('commentDisabled', true);
  }

  R.setText('fontSizeLabel', LBS.t('font_size'));
  R.setText('fontLarge', LBS.t('large'));
  R.setText('fontMedium', LBS.t('medium'));
  R.setText('fontSmall', LBS.t('small'));
}

// Port of redirectMessage(): the original shows a box and auto redirects.
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
  R.show('articleTop', false);
  R.show('articleBox', false);
  R.show('articleTail', false);
}

function wireCommentForm(article) {
  window.LBSCommentForm.wire(async (payload) => {
    try {
      await LBS.post('/api/articles/' + article.id + '/comments', payload);
      showMessage('messagebox', LBS.t('done'), LBS.t('comment_save_done'),
        'article.asp?id=' + article.id, true);
    } catch (error) {
      const messages = (error.data && error.data.errors) || [error.message];
      showMessage('errorbox', LBS.t('error'), R.errorList(messages),
        'article.asp?id=' + article.id, false);
    }
  });
}

function formHtml(article, isEdit) {
  const site = LBS.info;
  const categories = (LBS.data.sidebar && LBS.data.sidebar.categories) || [];
  const flags = article.ubb_flags || '111111';
  const html = flags === 'html';
  const checked = (condition) => (condition ? ' checked="checked"' : '');
  const selected = (condition) => (condition ? ' selected="selected"' : '');
  const rows = [];

  rows.push('<script type="text/javascript" src="js/messageform.js"></script>');
  rows.push('<form name="inputform" id="inputform" method="post" action="article.asp">');
  rows.push('<table width="100%" border="0" align="center" cellpadding="4" ' +
    'cellspacing="1" class="formbox">');
  rows.push('  <tr><td colspan="2" class="formbox-title">' +
    R.escapeHtml(isEdit ? LBS.t('edit') : LBS.t('new_article')) + ' [' +
    LBS.t('author') + ': ' + R.escapeHtml((LBS.user && LBS.user.name) || '') +
    ']</td></tr>');
  rows.push('  <tr>');
  rows.push('    <td class="formbox-rowheader" width="140"><b>' +
    LBS.t('category') + ':</b></td>');
  rows.push('    <td class="formbox-content">');
  rows.push('      <select name="log_catid" id="log_catid">');
  rows.push('        <option value="0">- ' + LBS.t('select_category') + ' -</option>');
  categories.forEach((category) => {
    rows.push('        <option value="' + category.id + '"' +
      selected(article.category && article.category.id === category.id) + '>' +
      R.escapeHtml(category.name) + ' [' + category.article_count + ']</option>');
  });
  rows.push('      </select>');
  rows.push('      &nbsp;&nbsp;<b>' + LBS.t('mode') + ':</b>');
  rows.push('      <select name="log_mode" id="log_mode">');
  [[1, 'public'], [2, 'draft'], [3, 'hidden'], [4, 'private']].forEach(([value, key]) => {
    rows.push('        <option value="' + value + '"' +
      selected((article.mode || 1) === value) + '>' + LBS.t(key) + '</option>');
  });
  rows.push('      </select>');
  rows.push('      &nbsp;&nbsp;<input name="log_locked" type="checkbox" ' +
    'id="log_locked" value="true"' + checked(article.locked) + ' /> ' +
    LBS.t('locked'));
  if (isEdit) {
    rows.push('      &nbsp;&nbsp;<a href="#" id="formDelete"><img src="' +
      R.image('icon_del.gif') + '" /> ' + LBS.t('delete') + '</a>');
  }
  rows.push('    </td>');
  rows.push('  </tr>');
  rows.push('  <tr>');
  rows.push('    <td class="formbox-rowheader"><b>' + LBS.t('title') + ':</b></td>');
  rows.push('    <td class="formbox-content">');
  rows.push('      <input name="log_title" type="text" id="log_title" size="60" ' +
    'value="' + R.escapeHtml(article.title || '') + '" maxlength="255" class="text" />');
  rows.push('      &nbsp;&nbsp;<input name="log_selected" type="checkbox" ' +
    'id="log_selected" value="true"' + checked(article.selected) + ' /> ' +
    LBS.t('selected'));
  rows.push('      <input name="log_id" type="hidden" value="' +
    (article.id || 0) + '" />');
  rows.push('    </td>');
  rows.push('  </tr>');
  rows.push('  <tr>');
  rows.push('    <td class="formbox-rowheader"><b>' + LBS.t('post_time') + ':</b></td>');
  rows.push('    <td class="formbox-content">');
  rows.push('      <input name="log_postTime" type="text" id="log_postTime" size="20" ' +
    'value="' + R.escapeHtml(article.post_time || '') + '" maxlength="20" class="text" />');
  rows.push('      &nbsp;&nbsp;<a href="javascript:setToCurrentTime()">' +
    LBS.t('set_to_current') + '</a>');
  rows.push('    </td>');
  rows.push('  </tr>');
  rows.push('  <tr>');
  rows.push('    <td class="formbox-rowheader" valign="top"><b>' + LBS.t('content') +
    ':</b><br /><br />');
  rows.push('      <div class="panel-smilies">');
  rows.push('        <div class="panel-smilies-title">' + LBS.t('smilies') + '</div>');
  rows.push('        <div class="panel-smilies-content">' + smileyLinks() + '</div>');
  rows.push('      </div>');
  rows.push('      <div style="font-weight: normal; text-align:left;">');
  rows.push('        <input name="e_html" type="checkbox" value="true"' +
    checked(html) + ' /> ' + LBS.t('e_html') + '<br />');
  rows.push('        <input name="e_ubb" type="checkbox" value="true"' +
    checked(!html && flags.charAt(0) === '1') + ' /> ' + LBS.t('e_ubb') + '<br />');
  rows.push('        <input name="e_autourl" type="checkbox" value="true"' +
    checked(!html && flags.charAt(1) === '1') + ' /> ' + LBS.t('e_autourl') + '<br />');
  rows.push('        <input name="e_image" type="checkbox" value="true"' +
    checked(!html && flags.charAt(2) === '1') + ' /> ' + LBS.t('e_image') + '<br />');
  rows.push('        <input name="e_media" type="checkbox" value="true"' +
    checked(!html && flags.charAt(3) === '1') + ' /> ' + LBS.t('e_media') + '<br />');
  rows.push('        <input name="e_smilies" type="checkbox" value="true"' +
    checked(!html && flags.charAt(4) === '1') + ' /> ' + LBS.t('e_smilies'));
  rows.push('      </div>');
  rows.push('    </td>');
  rows.push('    <td class="formbox-content">');
  rows.push('      <div style="padding-bottom:3px">');
  rows.push('        <select name="font" onfocus="this.selectedIndex=0" ' +
    'onchange="chfont(this.options[this.selectedIndex].value)">' +
    '<option value="" selected="selected">- Select Font -</option>' +
    ['Arial', 'Book Antiqua', 'Century Gothic', 'Courier New', 'Georgia', 'Impact',
      'Tahoma', 'Times New Roman', 'Verdana']
      .map((font) => '<option value="' + font + '">' + font + '</option>').join('') +
    '</select>');
  rows.push('        <select name="size" onfocus="this.selectedIndex=0" ' +
    'onchange="chsize(this.options[this.selectedIndex].value)">' +
    '<option value="" selected="selected">- Size (pt) -</option>' +
    [8, 9, 12, 16, 18, 24, 28, 32, 36]
      .map((size) => '<option value="' + size + '">' + size + '</option>').join('') +
    '</select>');
  rows.push('        <select name="color" onfocus="this.selectedIndex=0" ' +
    'onchange="chcolor(this.options[this.selectedIndex].value)">' +
    '<option value="" selected="selected">- Color -</option>' +
    ['White', 'Black', 'Red', 'Yellow', 'Pink', 'Green', 'Orange', 'Purple', 'Blue',
      'Beige', 'Brown', 'Teal', 'Navy', 'Maroon', 'LimeGreen']
      .map((color) => '<option value="' + color + '" style="background-color:' +
        color.toLowerCase() + ';color:' + color.toLowerCase() + ';">' + color +
        '</option>').join('') +
    '</select>');
  rows.push('        <input type="radio" name="mode" value="1" ' +
    'onclick="chmode(1)" checked="checked" /> Basic');
  rows.push('        <input type="radio" name="mode" value="0" onclick="chmode(0)" /> ' +
    'Prompt');
  rows.push('      </div>');
  rows.push('      <div>' + ubbToolbar() + '</div>');
  rows.push('      <div>');
  rows.push('        <textarea name="message" rows="18" cols="64" id="message" ' +
    'style="width:100%" onselect="storeCaret(this);" onclick="storeCaret(this);" ' +
    'onkeyup="storeCaret(this);CtrlEnter();">' +
    R.escapeHtml(article.content_raw || '') + '</textarea>');
  rows.push('      </div>');
  rows.push('    </td>');
  rows.push('  </tr>');
  void site;
  if (LBS.user && LBS.user.rights.upload > 0 && site.features && site.features.upload) {
    rows.push('  <tr class="formbox-content">' +
      '<td align="right"><b>' + LBS.t('attachment') + ':</b></td>' +
      '<td><iframe frameborder="0" height="21" marginheight="0" marginwidth="0" ' +
      'scrolling="no" width="99%" src="upload.asp"></iframe></td></tr>');
  }
  rows.push('  <tr class="formbox-content">');
  rows.push('    <td align="right"><b>' + LBS.t('trackback_url') + ':</b></td>');
  rows.push('    <td><input name="log_trackbackurl" type="text" ' +
    'id="log_trackbackurl" size="60" value="' +
    R.escapeHtml(article.trackback_url || '') + '" maxlength="255" class="text" /></td>');
  rows.push('  </tr>');
  rows.push('  <tr class="formbox-content">');
  rows.push('    <td></td>');
  rows.push('    <td>');
  rows.push('      <input name="btnSubmit" type="button" id="btnSubmit" value="' +
    LBS.t('save') + '" onclick="CheckInputForm();" class="button" />');
  rows.push('      <input name="btnReset" type="reset" id="btnReset" value="' +
    LBS.t('reset') + '" class="button" />');
  rows.push('      <input name="btnCancel" type="button" id="btnCancel" value="' +
    LBS.t('cancel') + '" onclick="window.history.back();" class="button" />');
  rows.push('    </td>');
  rows.push('  </tr>');
  rows.push('</table>');
  rows.push('</form>');
  return rows.join('\n');
}

function ubbToolbar() {
  const buttons = [
    ['bold()', 'bb_bold.gif', 'Bold'],
    ['italicize()', 'bb_italicize.gif', 'Italic'],
    ['underline()', 'bb_underline.gif', 'Underline'],
    ['strike()', 'bb_strike.gif', 'Strike Line'],
    ['superscript()', 'bb_sup.gif', 'Insert Superscript'],
    ['subscript()', 'bb_sub.gif', 'Insert Subscript'],
    ['center()', 'bb_center.gif', 'Align Center'],
    ['hyperlink()', 'bb_url.gif', 'Insert URL'],
    ['email()', 'bb_email.gif', 'Insert Mail Link'],
    ['image()', 'bb_image.gif', 'Insert Image'],
    ['media()', 'bb_media.gif', 'Insert Flash'],
    ['code()', 'bb_code.gif', 'Insert Code Block'],
    ['quote()', 'bb_quote.gif', 'Insert Quote'],
    ['list()', 'bb_list.gif', 'Insert List'],
    ['seperator()', 'bb_seperator.gif', 'Insert Content Separator'],
  ];
  return buttons.map(([handler, file, alt]) =>
    '<a href="javascript:' + handler + '"><img src="' +
      R.image('ubbcode/' + file) + '" alt="' + alt + '" /></a>').join(' ');
}

async function renderEditor(act, article) {
  const isEdit = act === 'edit';
  if (!LBS.user) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
    return;
  }
  if (!isEdit && !((LBS.user.rights && LBS.user.rights.post) > 1)) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
    return;
  }
  if (isEdit && !canEdit(article)) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
    return;
  }
  R.setHtml('editorMount', formHtml(article, isEdit));
  R.show('editorMount', true);
  R.show('articleTop', false);
  R.show('articleBox', false);
  R.show('articleTail', false);

  const form = R.byId('inputform');
  const submit = async () => {
    const payload = {
      log_catid: form.log_catid.value,
      log_mode: form.log_mode.value,
      log_title: form.log_title.value,
      log_postTime: form.log_postTime.value,
      log_trackbackurl: form.log_trackbackurl.value,
      log_locked: form.log_locked.checked,
      log_selected: form.log_selected.checked,
      message: form.message.value,
      e_html: form.e_html.checked,
      e_ubb: form.e_ubb.checked,
      e_autourl: form.e_autourl.checked,
      e_image: form.e_image.checked,
      e_media: form.e_media.checked,
      e_smilies: form.e_smilies.checked,
    };
    try {
      if (isEdit) {
        await LBS.patch('/api/articles/' + article.id, payload);
        showMessage('messagebox', LBS.t('done'), LBS.t('update_done'),
          'article.asp?id=' + article.id, true);
      } else {
        const created = await LBS.post('/api/articles', payload);
        showMessage('messagebox', LBS.t('done'), LBS.t('save_done'),
          'article.asp?id=' + created.id, true);
      }
    } catch (error) {
      const messages = (error.data && error.data.errors) || [error.message];
      showMessage('errorbox', LBS.t('error'), R.errorList(messages),
        'javascript:window.history.back();', false);
    }
  };
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    submit();
  });
  form.submit = () => {
    submit();
  };
  const deleteLink = R.byId('formDelete');
  if (deleteLink) {
    deleteLink.addEventListener('click', async (event) => {
      event.preventDefault();
      if (!window.confirm(LBS.t('confirm_delete_article') + '?')) {
        return;
      }
      try {
        const response = await fetch(LBS.api('/api/articles/' + article.id), {
          method: 'DELETE',
          credentials: 'same-origin',
        });
        if (!response.ok) {
          throw new Error('delete_failed');
        }
        showMessage('messagebox', LBS.t('done'), LBS.t('delete_done'),
          'default.asp', true);
      } catch (error) {
        showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'),
          'javascript:window.history.back();', false);
      }
    });
  }
}

function smileyLinks() {
  return window.LBSCommentForm.smileyLinks();
}

async function main() {
  await window.LBSLayout.mount({});
  const act = (R.params().get('act') || '').toLowerCase();
  if (act === 'new') {
    await renderEditor('new', {});
    return;
  }
  const id = R.intParam('id', 0);
  if (!id) {
    window.location.href = 'default.asp';
    return;
  }
  const search = R.params().toString();
  try {
    const payload = await LBS.get('/api/articles/' + id + (search ? '?' + search : ''));
    if (act === 'edit') {
      await renderEditor('edit', payload.article);
      return;
    }
    if (act === 'delete') {
      await deleteArticleFlow(payload.article);
      return;
    }
    renderArticle(payload);
  } catch (error) {
    R.setHtml(
      'textboxContent',
      '<div class="no-comment-box">' +
        (error.status === 404 ? LBS.t('article_not_found') : R.escapeHtml(error.message)) +
        '</div>'
    );
  }
}

async function deleteArticleFlow(article) {
  if (!LBS.user || !canDelete(article)) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
    return;
  }
  if (!window.confirm(LBS.t('confirm_delete_article') + '?')) {
    window.location.href = 'article.asp?id=' + article.id;
    return;
  }
  try {
    const response = await fetch(LBS.api('/api/articles/' + article.id), {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (!response.ok) {
      throw new Error('delete_failed');
    }
    showMessage('messagebox', LBS.t('done'), LBS.t('delete_done'), 'default.asp', true);
  } catch (error) {
    showMessage('errorbox', LBS.t('error'), LBS.t('no_rights'), 'default.asp', false);
  }
}

main();
