// Statistics page: port of stats.asp (visitor list, administrators only).
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

async function main() {
  // The original stats.asp called pageHeader/pageFooter but no sidebar(); same here.
  const payload = await window.LBSLayout.mount({});
  document.title = LBS.t('stats') + ' - ' +
    ((payload.site && payload.site.title) || 'LBS');
  const mount = R.byId('statsMount');
  try {
    const data = await LBS.get('/api/stats/visitors');
    const rows = data.visitors.map((visitor) => [
      '<tr>',
      '<td>' + R.escapeHtml(visitor.ip) + '</td>',
      '<td>' + R.escapeHtml(visitor.browser) + '<br />' +
        R.escapeHtml(visitor.os) + '</td>',
      '<td>' + R.escapeHtml(visitor.time) + '</td>',
      '<td><a href="' + R.escapeHtml(visitor.referer) + '" target="_blank">' +
        R.escapeHtml(visitor.referer_short) + '</a></td>',
      '</tr>',
    ].join('')).join('');
    mount.innerHTML = [
      '<div class="textbox-title"><h4>' + LBS.t('recent_visitors') + '</h4></div>',
      '<div class="listbox-table">',
      '<table cellpadding="2" cellspacing="2" width="100%">',
      '<tr>',
      '<td class="listbox-header" width="120">' + LBS.t('ip') + '</td>',
      '<td class="listbox-header" width="100">' + LBS.t('browser') + '/' +
        LBS.t('os') + '</td>',
      '<td class="listbox-header" width="100">' + LBS.t('timestamp') + '</td>',
      '<td class="listbox-header">' + LBS.t('referer') + '</td>',
      '</tr>',
      rows,
      '</table>',
      '</div>',
    ].join('\n');
  } catch (error) {
    mount.innerHTML = R.messageBox(LBS.t('error'), LBS.t('no_rights'), {
      style: 'errorbox',
      target: 'javascript:window.history.back();',
      linkText: LBS.t('goback'),
    });
  }
}

main();
