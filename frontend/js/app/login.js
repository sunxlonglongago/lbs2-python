// Login page: port of login.asp (outputLoginForm).
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

function loginForm(site) {
  const rows = [];
  rows.push('<table width="500px" align="center" cellspacing="1" class="formbox">');
  rows.push('<form name="Login" id="loginPageForm" method="post" action="login.asp?act=login">');
  rows.push('  <tr><td class="formbox-title" colspan="2">' + LBS.t('login') + '</td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('username') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="username" type="text" ' +
    'id="username" size="24" maxlength="24" class="text" /></td></tr>');
  rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('password') + ':</td>');
  rows.push('  <td class="formbox-content"><input name="password" type="password" ' +
    'id="password" size="24" maxlength="16" class="text" /></td></tr>');
  if (site.features && site.features.security_code) {
    rows.push('  <tr><td class="formbox-rowheader">' + LBS.t('scode') + ':</td>');
    rows.push('  <td class="formbox-content"><input name="scode" size="4" maxlength="4" ' +
      'type="text" id="scode" class="text" /> <img src="scode" /></td></tr>');
  }
  rows.push('  <tr><td class="formbox-rowheader" valign="top">' + LBS.t('auto_login') +
    ':</td>');
  rows.push('  <td class="formbox-content">');
  rows.push('    <input type="radio" name="CookiesDay" value="1" checked="checked" /> ' +
    LBS.t('disabled') + '<br />');
  rows.push('    <input type="radio" name="CookiesDay" value="30" /> 1 ' +
    LBS.t('month') + '<br />');
  rows.push('    <input type="radio" name="CookiesDay" value="365" /> 1 ' +
    LBS.t('year'));
  rows.push('  </td></tr>');
  rows.push('  <tr><td class="formbox-content"></td>');
  rows.push('  <td class="formbox-content">');
  rows.push('    <input name="Login" type="submit" id="agree" value="   ' +
    LBS.t('login') + '   " class="button" />');
  rows.push('    &nbsp; <input name="Register" type="button" id="Register" ' +
    'value=" ' + LBS.t('register') + ' " class="button" ' +
    'onclick="javascript:document.location.href=\'register.asp\';" />');
  rows.push('  </td></tr>');
  rows.push('</form>');
  rows.push('</table>');
  return rows.join('\n');
}

async function main() {
  await window.LBSLayout.mount({});
  const params = R.params();
  const act = (params.get('act') || '').toLowerCase();
  const site = LBS.info;
  const next = params.get('next') || '';

  if (act === 'logout') {
    await LBS.post('/api/auth/logout');
    R.setHtml('loginMount', R.messageBox(LBS.t('done'), LBS.t('logout_done'), {
      style: 'messagebox',
      target: 'default.asp',
      linkText: LBS.t('redirect'),
      auto: true,
    }));
    return;
  }

  if (LBS.user && !act) {
    R.setHtml('loginMount', R.messageBox(LBS.t('error'), LBS.t('login_already'), {
      style: 'errorbox',
      target: 'default.asp',
      linkText: LBS.t('goback'),
    }));
    return;
  }

  R.setHtml('loginMount', loginForm(site));
  const form = R.byId('loginPageForm');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const cookiesDay = form.CookiesDay.value;
    try {
      await LBS.post('/api/auth/login', {
        username: form.username.value.trim(),
        password: form.password.value,
        remember: cookiesDay !== '1',
      });
      R.setHtml('loginMount', R.messageBox(LBS.t('done'), LBS.t('login_done'), {
        style: 'messagebox',
        target: next || 'default.asp',
        linkText: LBS.t('redirect'),
        auto: true,
      }));
    } catch (error) {
      const code = error.data && error.data.error ? error.data.error : 'login_fail';
      R.setHtml('loginMount', R.messageBox(
        LBS.t('error'),
        LBS.t('login_error') + '<ul id="errorlist"><li>' + LBS.t(code) + '</li></ul>',
        {
          style: 'errorbox',
          target: 'javascript:window.history.back();',
          linkText: LBS.t('goback'),
        }
      ));
    }
  });
}

main();
