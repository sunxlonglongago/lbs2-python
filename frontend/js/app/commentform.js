// Port of commentForm() in global.asp: the shared comment / guestbook form.
const LBSCommentForm = (() => {
  const R = window.LBSRender;

  function smileyLinks() {
    const sidebar = (LBS.data && LBS.data.sidebar) || {};
    const folder = LBS.info.smilies_folder || 'styles/default/images/smilies';
    const perRow = sidebar.smilies_per_row || 4;
    const parts = [];
    (sidebar.smilies || []).forEach((smiley, index) => {
      parts.push(
        '<a href="javascript:insertSmilies(\'' + smiley.code + '\')"><img src="' +
          R.escapeHtml(folder + '/' + smiley.image) + '" alt="' +
          R.escapeHtml(smiley.code) + '" /></a>'
      );
      if ((index + 1) % perRow === 0) {
        parts.push('<br />');
      }
    });
    return parts.join('\n');
  }

  function html(options) {
    const opts = options || {};
    const site = LBS.info || {};
    const flags = String(opts.ubbFlags || '110011');
    const checked = (condition) => (condition ? ' checked="checked"' : '');
    const rows = [];

    rows.push('<div id="commentForm">');
    rows.push('<form name="inputform" id="inputform" method="post" action="' +
      (opts.action || '#') + '">');
    rows.push('<table width="100%" border="0" align="center" cellpadding="4" ' +
      'cellspacing="1" class="formbox-comment">');
    rows.push('  <tr><td colspan="2" class="formbox-comment-title">' +
      R.escapeHtml(opts.title || LBS.t('post_comment')) + '</td></tr>');
    rows.push('  <tr>');
    rows.push('    <td class="formbox-comment-rowheader" width="140">');
    rows.push('      <div class="panel-smilies">');
    rows.push('        <div class="panel-smilies-title">' + LBS.t('smilies') + '</div>');
    rows.push('        <div class="panel-smilies-content">' + smileyLinks() + '</div>');
    rows.push('      </div>');
    rows.push('      <div style="font-weight: normal; text-align:left;">');
    rows.push('        <input name="e_ubb" type="checkbox" value="true"' +
      checked(flags.charAt(0) === '1') + ' /> ' + LBS.t('e_ubb') + '<br />');
    rows.push('        <input name="e_autourl" type="checkbox" value="true"' +
      checked(flags.charAt(1) === '1') + ' /> ' + LBS.t('e_autourl') + '<br />');
    rows.push('        <input name="e_smilies" type="checkbox" value="true"' +
      checked(flags.charAt(4) === '1') + ' /> ' + LBS.t('e_smilies') + '<br />');
    rows.push('        <input name="comm_hidden" type="checkbox" value="true"' +
      checked(opts.hidden) + ' /> ' + LBS.t('comm_hidden'));
    rows.push('      </div>');
    rows.push('    </td>');
    rows.push('    <td class="formbox-comment-content" valign="top">');
    if (!LBS.user) {
      rows.push('      <div style="padding-bottom:5px">');
      rows.push('        ' + LBS.t('username') + ': <input name="comm_username" ' +
        'type="text" size="12" maxlength="24" class="text" />&nbsp;');
      rows.push('        ' + LBS.t('password') + ': <input name="comm_password" ' +
        'type="password" size="12" maxlength="16" class="text" />&nbsp;');
      if (site.features && site.features.register) {
        rows.push('        <input name="comm_register" type="checkbox" value="true" /> ' +
          LBS.t('reg_now') + '?');
      }
      rows.push('      </div>');
    }
    if (site.features && site.features.security_code) {
      rows.push('      <div style="padding-bottom:5px">');
      rows.push('        <input name="scode" size="4" maxlength="4" type="text" ' +
        'class="text" /> <img src="scode" alt="' + LBS.t('scode') + '" />');
      rows.push('        <span class="comment-text">* ' + LBS.t('scode_req') +
        '</span>');
      rows.push('      </div>');
    }
    if (opts.showReplyArea) {
      rows.push('      <textarea name="entry" cols="64" rows="10" id="entry" ' +
        'style="width:100%" onkeyup="CtrlEnter();">' +
        R.escapeHtml(opts.content || '') + '</textarea>');
      rows.push('      <textarea name="message" cols="64" rows="10" id="message" ' +
        'style="width:100%" onselect="storeCaret(this);" onclick="storeCaret(this);" ' +
        'onkeyup="storeCaret(this);CtrlEnter();">' +
        R.escapeHtml(opts.reply || '') + '</textarea>');
    } else {
      rows.push('      <textarea name="message" cols="64" rows="10" id="message" ' +
        'style="width:100%" onselect="storeCaret(this);" onclick="storeCaret(this);" ' +
        'onkeyup="storeCaret(this);CtrlEnter();">' +
        R.escapeHtml(opts.content || '') + '</textarea>');
    }
    if (LBS.user && LBS.user.rights.upload > 0 && site.features && site.features.upload) {
      rows.push('      <div><iframe frameborder="0" height="21" marginheight="0" ' +
        'marginwidth="0" scrolling="no" width="100%" src="upload.asp"></iframe></div>');
    }
    rows.push('      <div style="padding-top:10px">');
    rows.push('        <input type="submit" name="btnSubmit" value=" ' +
      (opts.submitLabel || LBS.t('post_comment')) + ' " class="button" />&nbsp;');
    rows.push('        <input name="Reset" type="reset" value=" ' + LBS.t('reset') +
      ' " class="button" />');
    rows.push('      </div>');
    rows.push('    </td>');
    rows.push('  </tr>');
    rows.push('</table>');
    rows.push('</form>');
    rows.push('</div>');
    return rows.join('\n');
  }

  // CheckInputForm() in messageform.js submits the form directly, which would
  // bypass a submit listener; override submit() so both paths share a handler.
  function wire(onSubmit) {
    const form = R.byId('inputform');
    if (!form) {
      return null;
    }
    const run = () => onSubmit(collect(form));
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      run();
    });
    form.submit = run;
    return form;
  }

  function collect(form) {
    const payload = {
      message: form.message.value,
      comm_hidden: form.comm_hidden ? form.comm_hidden.checked : false,
      e_ubb: form.e_ubb.checked,
      e_autourl: form.e_autourl.checked,
      e_smilies: form.e_smilies.checked,
    };
    if (form.entry) {
      payload.entry = form.entry.value;
    }
    if (!LBS.user) {
      payload.comm_username = form.comm_username ? form.comm_username.value : '';
      payload.comm_password = form.comm_password ? form.comm_password.value : '';
      payload.comm_register = form.comm_register ? form.comm_register.checked : false;
    }
    return payload;
  }

  return { html, wire, smileyLinks };
})();

window.LBSCommentForm = LBSCommentForm;
