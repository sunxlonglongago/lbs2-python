// Register page: port of register.asp (agreement -> form -> save).
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

function agreementHtml() {
  return [
    '<center>',
    '<div class="messagebox">',
    '  <div class="messagebox-title">' + LBS.t('reg_agreement') + '</div>',
    '  <div class="messagebox-content">',
    '    ' + LBS.t('reg_agreement_text'),
    '    <div align="center"><form name="aform" id="aform" method="post" action="register.asp?act=agree">',
    '      <input name="agreesubmit" type="submit" id="agree" value=" ' +
      LBS.t('reg_agree') + ' " class="button" /> &nbsp;',
    '      <input type="button" name="return" value=" ' + LBS.t('reg_decline') +
      ' " onclick="javascript:history.go(-1);" class="button" />',
    '    </form></div>',
    '  </div>',
    '</div>',
    '</center>',
  ].join('\n');
}

function countdown() {
  const seconds = 9;
  const agree = document.getElementById('agree');
  if (!agree) {
    return;
  }
  const label = ' ' + LBS.t('reg_agree') + ' ';
  let left = seconds;
  agree.disabled = true;
  agree.value = label + '(' + left + ') ';
  const timer = window.setInterval(() => {
    left -= 1;
    if (left <= 0) {
      window.clearInterval(timer);
      agree.disabled = false;
      agree.value = label;
      return;
    }
    agree.value = label + '(' + left + ') ';
  }, 1000);
}

function formHtml(site) {
  const rows = [];
  rows.push('<form name="register" id="registerForm" method="post" action="register.asp?act=save">');
  rows.push('<table cellspacing="1" width="500px" align="center" class="formbox">');
  rows.push('  <tr><td class="formbox-title" colspan="2">' + LBS.t('reg_title') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('username') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="username" type="text" id="username" ' +
    'size="24" maxlength="24" class="text" /> <font color="#FF0000">&nbsp;*</font> ' +
    LBS.t('username_req') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('password') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="password" type="password" ' +
    'id="password" size="16" maxlength="16" class="text" /> &nbsp;' +
    '<font color="#FF0000">*</font> ' + LBS.t('password_req') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('repassword') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="repassword" type="password" ' +
    'id="repassword" size="16" maxlength="16" class="text" /> &nbsp;' +
    '<font color="#FF0000">*</font> ' + LBS.t('repassword_req') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('gender') + ':</td>');
  rows.push('  <td class="formbox-content">');
  rows.push('    <input name="gender" type="radio" value="0" checked="checked" />' +
    LBS.t('gender0'));
  rows.push('    <input name="gender" type="radio" value="1" />' + LBS.t('gender1'));
  rows.push('    <input name="gender" type="radio" value="2" />' + LBS.t('gender2'));
  rows.push('  </td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('email') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="email" size="30" maxlength="50" ' +
    'type="text" id="email" class="text" /> <input type="checkbox" name="hideemail" ' +
    'value="true" checked="checked" /> ' + LBS.t('email_hide') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('homepage') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="homepage" size="30" maxlength="50" ' +
    'type="text" id="homepage" class="text" /></td></tr>');
  if (site.features && site.features.security_code) {
    rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('scode') + ':</td>');
    rows.push('  <td class="formbox-content"><input name="scode" size="4" maxlength="4" ' +
      'type="text" id="scode" class="text" /> <img src="scode" align="absmiddle" />' +
      '&nbsp;<font color="#FF0000">*</font> ' + LBS.t('scode_req') + '</td></tr>');
  }
  rows.push('  <tr><td class="formbox-content"></td>');
  rows.push('  <td class="formbox-content">');
  rows.push('    <input name="Submit" type="submit" id="Submit" value=" ' +
    LBS.t('submit') + ' " class="button" /> &nbsp;');
  rows.push('    <input name="Reset" type="reset" id="Reset" value=" ' + LBS.t('reset') +
    ' " class="button" />');
  rows.push('  </td></tr>');
  rows.push('</table>');
  rows.push('</form>');
  return rows.join('\n');
}

function showError(messages) {
  R.setHtml('registerMount', R.messageBox(
    LBS.t('error'),
    LBS.t('reg_error') + R.errorList(messages),
    {
      style: 'errorbox',
      target: 'javascript:window.history.back();',
      linkText: LBS.t('goback'),
    }
  ));
}

async function main() {
  await window.LBSLayout.mount({});
  const site = LBS.info;
  const act = (R.params().get('act') || '').toLowerCase();
  const mount = R.byId('registerMount');
  document.title = LBS.t('reg_title') + ' - ' + ((site && site.title) || 'LBS');

  if (!(site.features && site.features.register)) {
    mount.innerHTML = R.messageBox(LBS.t('error'), LBS.t('reg_disabled'), {
      style: 'errorbox',
      target: 'default.asp',
      linkText: LBS.t('goback'),
    });
    return;
  }
  if (LBS.user) {
    mount.innerHTML = R.messageBox(LBS.t('error'), LBS.t('reg_already'), {
      style: 'errorbox',
      target: 'default.asp',
      linkText: LBS.t('goback'),
    });
    return;
  }

  if (act === 'agree' || act === 'save') {
    mount.innerHTML = formHtml(site);
    const form = R.byId('registerForm');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const gender = form.gender.value;
      try {
        await LBS.post('/api/auth/register', {
          username: form.username.value.trim(),
          password: form.password.value,
          repassword: form.repassword.value,
          email: form.email.value.trim(),
          hideemail: form.hideemail.checked,
          homepage: form.homepage.value.trim(),
          gender: parseInt(gender, 10) || 0,
        });
        mount.innerHTML = R.messageBox(LBS.t('done'), LBS.t('reg_done'), {
          style: 'messagebox',
          target: 'default.asp',
          linkText: LBS.t('redirect'),
          auto: true,
        });
      } catch (error) {
        showError([(error.data && error.data.error) || error.message]);
      }
    });
    return;
  }

  mount.innerHTML = agreementHtml();
  countdown();
}

main();
