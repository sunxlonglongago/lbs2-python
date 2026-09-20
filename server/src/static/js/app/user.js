// User page: port of user.asp (list / profile / profile form / delete).
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

function profileHtml(user, viewer) {
  const rows = [];
  rows.push('<div class="textbox">');
  rows.push('  <div class="textbox-title"><h4>' + LBS.t('user_info') + '</h4></div>');
  rows.push('  <div class="textbox-content">');
  rows.push('  <table cellpadding="2" cellspacing="1">');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('username') +
    ':</td><td class="formbox-content">' + R.escapeHtml(user.name) +
    (user.can_edit ? ' &nbsp;&nbsp; <a href="user.asp?act=edit&amp;id=' + user.id +
      '">[' + LBS.t('edit_profile') + ']</a>' : '') + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('user_group') +
    ':</td><td class="formbox-content">' + R.escapeHtml(user.group_name) + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('stats') +
    ':</td><td class="formbox-content">');
  rows.push('      <a href="default.asp?user=' + user.id + '" title="' +
    LBS.t('view_user_article') + '">' + LBS.t('articles') + ': ' +
    user.article_count + '</a> &nbsp;&nbsp;');
  rows.push('      <a href="comment.asp?user=' + user.id + '" title="' +
    LBS.t('view_user_comment') + '">' + LBS.t('comments') + ': ' +
    user.comment_count + '</a>');
  rows.push('    </td></tr>');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('gender') +
    ':</td><td class="formbox-content">' + LBS.t('gender' + (user.gender || 0)) +
    '</td></tr>');
  if (user.email_visible) {
    rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('email') +
      ':</td><td class="formbox-content">' + R.escapeHtml(user.email) + '</td></tr>');
  }
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('homepage') +
    ':</td><td class="formbox-content">' +
    (user.homepage
      ? '<a href="' + R.escapeHtml(user.homepage) + '" target="_blank" ' +
        'ref="nofollow">' + R.escapeHtml(user.homepage) + '</a>'
      : '') + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('last_visit') +
    ':</td><td class="formbox-content">' + R.escapeHtml(user.last_visit) + '</td></tr>');
  if (viewer && viewer.group_id === 1) {
    rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('ip') +
      ':</td><td class="formbox-content">' + R.escapeHtml(user.ip) + '</td></tr>');
  }
  rows.push('  </table>');
  rows.push('  </div>');
  rows.push('</div>');
  return rows.join('\n');
}

function formHtml(user, viewer) {
  const rows = [];
  rows.push('<div class="textbox">');
  rows.push('  <div class="textbox-title"><h4>' + LBS.t('edit_profile') + '</h4></div>');
  rows.push('  <div class="textbox-content">');
  rows.push('  <form name="editprofile" id="editprofile" method="post" ' +
    'action="user.asp?act=update&amp;id=' + user.id + '">');
  rows.push('  <table cellpadding="2" cellspacing="1">');
  rows.push('    <tr><td class="formbox-rowheader" width="120">' + LBS.t('username') +
    ':</td><td class="formbox-content">' + R.escapeHtml(user.name));
  if (user.can_edit) {
    rows.push('      <a href="user.asp?act=delete&amp;id=' + user.id + '"><img src="' +
      R.image('icon_del.gif') + '" title="' + LBS.t('delete') + '" /></a>');
  }
  rows.push('    </td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('user_group') +
    ':</td><td class="formbox-content">');
  if (viewer && viewer.group_id === 1) {
    rows.push('      <select name="groupID" id="groupID">');
    (user.groups || []).forEach((group) => {
      rows.push('        <option value="' + group.id + '"' +
        (group.id === user.group_id ? ' selected="selected"' : '') + '>' +
        R.escapeHtml(group.name) + '</option>');
    });
    rows.push('      </select>');
  } else {
    rows.push('      ' + R.escapeHtml(user.group_name));
  }
  rows.push('    </td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('password') +
    ':</td><td class="formbox-content"><input name="oldpassword" type="password" ' +
    'id="oldpassword" size="16" maxlength="16" class="text" /> &nbsp;' +
    '<font color="#FF0000">*</font> ' + LBS.t('edit_password_req') + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('new_password') +
    ':</td><td class="formbox-content"><input name="password" type="password" ' +
    'id="password" size="16" maxlength="16" class="text" /> &nbsp; ' +
    LBS.t('password_req') + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('repassword') +
    ':</td><td class="formbox-content"><input name="repassword" type="password" ' +
    'id="repassword" size="16" maxlength="16" class="text" /> &nbsp; ' +
    LBS.t('repassword_req') + '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('gender') +
    ':</td><td class="formbox-content">');
  [0, 1, 2].forEach((value) => {
    rows.push('      <input name="gender" type="radio" value="' + value + '"' +
      (user.gender === value ? ' checked="checked"' : '') + ' />' +
      LBS.t('gender' + value));
  });
  rows.push('    </td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('email') +
    ':</td><td class="formbox-content"><input name="email" size="30" maxlength="50" ' +
    'type="text" value="' + R.escapeHtml(user.email) + '" class="text" /> ' +
    '<input type="checkbox" name="hideemail" value="true"' +
    (user.hide_email ? ' checked="checked"' : '') + ' /> ' + LBS.t('email_hide') +
    '</td></tr>');
  rows.push('    <tr><td class="formbox-rowheader">' + LBS.t('homepage') +
    ':</td><td class="formbox-content"><input name="homepage" size="30" maxlength="50" ' +
    'type="text" value="' + R.escapeHtml(user.homepage) + '" class="text" /></td></tr>');
  rows.push('    <tr><td></td><td><input type="Submit" name="Submit" value=" ' +
    LBS.t('save_change') + ' " class="button" /></td></tr>');
  rows.push('  </table>');
  rows.push('  </form>');
  rows.push('  </div>');
  rows.push('</div>');
  return rows.join('\n');
}

function listHtml(data, viewer) {
  const rows = [];
  rows.push('<div class="article-top"><div class="pages">' + data.page_links +
    '</div></div>');
  rows.push('<div class="listbox"><div style="width: 99%">');
  rows.push('<table cellpadding="2" cellspacing="2" width="100%">');
  rows.push('  <tr>');
  rows.push('    <td class="listbox-header">' + LBS.t('username') + ' / ' +
    LBS.t('homepage') + '</td>');
  rows.push('    <td class="listbox-header">' + LBS.t('articles') + '</td>');
  rows.push('    <td class="listbox-header">' + LBS.t('comments') + '</td>');
  rows.push('    <td class="listbox-header">' + LBS.t('last_visit') + '</td>');
  if (viewer) {
    rows.push('    <td class="listbox-header">' + LBS.t('email') + '</td>');
  }
  rows.push('  </tr>');
  data.items.forEach((user) => {
    rows.push('  <tr>');
    rows.push('    <td class="listbox-entry" style="word-break: normal;">');
    if (data.is_admin) {
      rows.push('    <a href="user.asp?act=delete&amp;id=' + user.id + '"><img src="' +
        R.image('icon_del.gif') + '" title="' + LBS.t('delete') + '" /></a>');
    }
    rows.push('    &nbsp;&nbsp;<a href="user.asp?id=' + user.id + '" title="' +
      LBS.t('user_info') + '">' + R.escapeHtml(user.name) + '</a>');
    if (user.homepage) {
      rows.push('    <a href="' + R.escapeHtml(user.homepage) +
        '" target="_blank" ref="nofollow"><img src="' + R.image('icon_website.gif') +
        '" title="' + R.escapeHtml(user.homepage) + '" /></a>');
    }
    rows.push('    </td>');
    rows.push('    <td class="listbox-entry" width="80"><a href="default.asp?user=' +
      user.id + '">' + user.article_count + '</a></td>');
    rows.push('    <td class="listbox-entry" width="80"><a href="comment.asp?user=' +
      user.id + '">' + user.comment_count + '</a></td>');
    rows.push('    <td class="listbox-entry" width="125">' +
      R.escapeHtml(user.last_visit) + '</td>');
    if (viewer) {
      rows.push('    <td class="listbox-entry">' +
        (user.email_visible ? R.escapeHtml(user.email) : '') + '</td>');
    }
    rows.push('  </tr>');
  });
  rows.push('</table>');
  rows.push('</div></div>');
  rows.push('<div class="article-bottom"><div class="pages">' + data.page_links +
    '</div></div>');
  return rows.join('\n');
}

function showMessage(html) {
  R.setHtml('userMount', html);
}

async function deleteUser(userId) {
  if (!window.confirm(LBS.t('confirm_delete_user') + '?')) {
    window.location.href = 'user.asp';
    return;
  }
  try {
    const response = await fetch(LBS.api('/api/users/' + userId), {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (!response.ok) {
      throw new Error('delete_failed');
    }
    showMessage(R.messageBox(LBS.t('done'), LBS.t('user_deleted'), {
      style: 'messagebox',
      target: 'user.asp',
      linkText: LBS.t('redirect'),
      auto: true,
    }));
  } catch (error) {
    showMessage(R.messageBox(LBS.t('error'), LBS.t('no_rights'), {
      style: 'errorbox',
      target: 'javascript:window.history.back();',
      linkText: LBS.t('goback'),
    }));
  }
}

async function main() {
  await window.LBSLayout.mount({});
  const params = R.params();
  const act = (params.get('act') || '').toLowerCase();
  const id = R.intParam('id', 0);
  const viewer = LBS.user;
  const siteTitle = (LBS.info && LBS.info.title) || 'LBS';

  if (!id) {
    document.title = LBS.t('reg_users') + ' - ' + siteTitle;
    const search = params.toString();
    const data = await LBS.get('/api/users' + (search ? '?' + search : ''));
    showMessage(listHtml(data, viewer));
    return;
  }

  if (act === 'delete') {
    await deleteUser(id);
    return;
  }

  const profile = (await LBS.get('/api/users/' + id)).user;
  if (act === 'edit') {
    document.title = LBS.t('edit_profile') + ' - ' + siteTitle;
    if (!profile.can_edit) {
      showMessage(R.messageBox(LBS.t('error'), LBS.t('no_rights'), {
        style: 'errorbox',
        target: 'javascript:window.history.back();',
        linkText: LBS.t('goback'),
      }));
      return;
    }
    showMessage(formHtml(profile, viewer));
    const form = R.byId('editprofile');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const gender = form.querySelector('input[name=gender]:checked');
      try {
        await LBS.patch('/api/users/' + id, {
          oldpassword: form.oldpassword.value,
          password: form.password.value,
          repassword: form.repassword.value,
          email: form.email.value.trim(),
          hideemail: form.hideemail.checked,
          homepage: form.homepage.value.trim(),
          gender: gender ? parseInt(gender.value, 10) : 0,
          groupID: form.groupID ? parseInt(form.groupID.value, 10) : undefined,
        });
        showMessage(R.messageBox(LBS.t('done'), LBS.t('profile_updated'), {
          style: 'messagebox',
          target: 'user.asp?id=' + id,
          linkText: LBS.t('redirect'),
          auto: true,
        }));
      } catch (error) {
        const messages = (error.data && error.data.errors) || [error.message];
        showMessage(R.messageBox(LBS.t('error'), R.errorList(messages), {
          style: 'errorbox',
          target: 'javascript:window.history.back();',
          linkText: LBS.t('goback'),
        }));
      }
    });
    return;
  }

  document.title = LBS.t('user_info') + ' - ' + siteTitle;
  showMessage(profileHtml(profile, viewer));
}

main().catch((error) => {
  showMessage(R.messageBox(LBS.t('error'), R.escapeHtml(error.message), {
    style: 'errorbox',
    target: 'default.asp',
    linkText: LBS.t('goback'),
  }));
});
