// Port of global.asp: pageHeader(), sidebar() and pageFooter().
// The markup itself lives in the HTML files; this module fills the dynamic
// values (titles, panels, counters) from /api/site.
const LBSLayout = (() => {
  const R = LBSRender;

  const startedAt = Date.now();

  function lengthW(value) {
    const text = String(value == null ? '' : value);
    let total = 0;
    for (let index = 0; index < text.length; index += 1) {
      total += text.charCodeAt(index) > 255 ? 2 : 1;
    }
    return total;
  }

  function cutString(value, outputLen) {
    const text = String(value == null ? '' : value);
    let total = 0;
    for (let index = 0; index < text.length; index += 1) {
      total += text.charCodeAt(index) > 255 ? 2 : 1;
      if (total >= outputLen) {
        return text.slice(0, index) + '...';
      }
    }
    return text;
  }

  function header(site) {
    const logo = R.byId('logo');
    if (logo) {
      logo.src = site.logo_image || R.image('logo.gif');
    }
    const title = site.title || 'LBS';
    const pageTitle = document.body.getAttribute('data-page-title') || '';
    document.title = pageTitle ? pageTitle + ' - ' + title : title;
    const titleNode = R.byId('blogTitle');
    if (titleNode) {
      titleNode.textContent = title;
      titleNode.href = './';
    }
    R.setText('blogDescription', site.description || '');
    const stylesheet = R.byId('siteStylesheet');
    if (stylesheet && site.style_sheet) {
      stylesheet.href = site.style_sheet;
    }
    const feed = R.byId('siteFeed');
    if (feed) {
      feed.title = title;
      feed.href = 'feed.asp';
    }
    R.setText('menuIndex', LBS.t('index'));
    R.setText('menuSelected', LBS.t('selected'));
    R.setText('menuGuestbook', LBS.t('guestbook'));
    R.setText('menuToggle', LBS.t('toggle_sidebar'));
    R.setText('menuLogin', LBS.t('login'));
    R.show('siteClosedBanner', !!site.closed);
  }

  function userPanel(user, site) {
    const loggedIn = !!user;
    R.show('panel_user', loggedIn);
    R.show('panelUser', !loggedIn);
    if (loggedIn) {
      R.setHtml(
        'panelUserGreeting',
        LBS.t('login_as') + ' <b>' + R.escapeHtml(user.name) + '</b>'
      );
      const items = [];
      if (user.group_id === 1) {
        items.push('<li><a href="admin.asp">' + LBS.t('administration') + '</a></li>');
      }
      if (user.rights && user.rights.post > 1) {
        items.push(
          '<li><a href="article.asp?act=new">' + LBS.t('new_article') + '</a></li>'
        );
      }
      items.push(
        '<li><a href="user.asp?act=edit&amp;id=' + user.id + '">' +
          LBS.t('edit_profile') + '</a></li>'
      );
      items.push(
        '<li><a href="#" id="logoutLink">' + LBS.t('logout') + '</a></li>'
      );
      R.setHtml('panelUserLinks', items.join('\n'));
      const logout = R.byId('logoutLink');
      if (logout) {
        logout.addEventListener('click', async (event) => {
          event.preventDefault();
          await LBS.post('/api/auth/logout');
          window.location.reload();
        });
      }
    } else {
      R.setText('loginUsernameLabel', LBS.t('username') + ':');
      R.setText('loginPasswordLabel', LBS.t('password') + ':');
      R.setText('loginScodeLabel', LBS.t('scode') + ':');
      R.setText('loginRegisterLink', LBS.t('reg_now'));
      R.setText('loginSubmit', LBS.t('login'));
      const securityCode = !!(site.features && site.features.security_code);
      R.show('loginScodeRow', securityCode);
      const scodeImage = R.byId('loginScodeImage');
      if (scodeImage && securityCode) {
        // Only point at the captcha endpoint when the feature is on, so the
        // disabled form does not fire a useless request.
        scodeImage.src = 'scode.asp';
      }
      R.show('loginRegisterRow', !!(site.features && site.features.register));
    }
    R.show('menuLoginItem', !loggedIn);
  }

  function bindLoginForm() {
    const form = R.byId('loginForm');
    if (!form) {
      return;
    }
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const username = form.username.value.trim();
      const password = form.password.value;
      const remember = form.remember ? form.remember.checked : false;
      try {
        await LBS.post('/api/auth/login', { username, password, remember });
        window.location.reload();
      } catch (error) {
        alert(error.data && error.data.error === 'form_incomplete'
          ? LBS.t('form_incomplete')
          : LBS.t('login_fail'));
      }
    });
  }

  function categoryPanel(site) {
    const rows = [
      '<li><a href="default.asp"><b>' + LBS.t('index') + '</b></a></li>',
    ];
    (site.categories || []).forEach((category) => {
      const name = R.escapeHtml(category.name);
      let row = '<li><a href="default.asp?cat=' + category.id + '">' + name + '</a> [' +
        category.article_count + '] ';
      row += '<a href="feed.asp?cat=' + category.id + '" title="' + name + ' ' +
        LBS.t('rss_feed') + '" target="_blank"><img src="' + R.image('rss.png') +
        '" class="meta-button" alt="' + name + ' ' + LBS.t('rss_feed') + '" /></a>';
      if (category.locked) {
        row += '<img src="' + R.image('icon_lock.gif') + '" alt="' +
          LBS.t('locked') + '" />';
      }
      row += '</li>';
      rows.push(row);
    });
    R.setHtml('panelCategoryList', rows.join('\n'));
  }

  function recentArticles(site) {
    const rows = (site.recent_articles || []).map((article) => {
      const title = R.escapeHtml(article.title);
      return '<li><a href="' + R.articleUrl(article.id) + '" title="' + title + '">' +
        R.escapeHtml(cutString(article.title, 28)) + '</a></li>';
    });
    R.setHtml('panelArticleList', rows.join('\n'));
  }

  function recentComments(site) {
    const rows = (site.recent_comments || []).map((comment) => {
      const link = R.articleUrl(comment.article_id) + '#comment' + comment.id;
      if (comment.visible) {
        const title = comment.author + ' [' + comment.article_title + ']: \n' +
          comment.title_excerpt;
        return '<li><a href="' + link + '" title="' + R.escapeHtml(title) + '">' +
          R.escapeHtml(comment.excerpt) + '</a></li>';
      }
      const masked = (comment.excerpt || '').replace(/./g, '*').slice(0, 24);
      return '<li><a href="' + link + '" title="' + LBS.t('hidden') + '">' + masked +
        '</a></li>';
    });
    R.setHtml('panelCommentList', rows.join('\n'));
  }

  function buildSearchPanel() {
    R.setText('panelSearchTitle', LBS.t('search'));
    const options = [
      ['articles', LBS.t('articles')],
      ['comments', LBS.t('comments')],
      ['guestbook', LBS.t('guestbook')],
      ['trackbacks', LBS.t('trackbacks')],
    ];
    R.setHtml(
      'searchType',
      options.map(([value, label]) => '<option value="' + value + '">' + label +
        '</option>').join('')
    );
    R.setText('searchSubmit', ' ' + LBS.t('search') + ' ');
  }

  function statsPanel(site, counters, user) {
    R.setText('panelStatsTitle', LBS.t('stats'));
    const rows = [];
    if (user && user.group_id === 1) {
      rows.push(LBS.t('visitors') + ': <a href="stats.asp" target="_blank">' +
        (counters.counterVisitor || 0) + '</a>');
    } else {
      rows.push(LBS.t('visitors') + ': ' + (counters.counterVisitor || 0));
    }
    rows.unshift(
      LBS.t('articles') + ': ' + (counters.counterArticle || 0),
      '<a href="comment.asp">' + LBS.t('comments') + ': ' +
        (counters.counterComment || 0) + '</a>',
      '<a href="trackback.asp?act=list">' + LBS.t('trackbacks') + ': ' +
        (counters.counterTrackback || 0) + '</a>',
      '<a href="user.asp">' + LBS.t('reg_users') + ':  ' +
        (counters.counterUser || 0) + '</a>'
    );
    rows.push(
      LBS.t('online_user') + ': ' + (site.online || 1),
      '',
      '<a href="feed.asp" title="' + LBS.t('articles') + LBS.t('rss_feed') +
        '" target="_blank"><img src="' + R.image('rss_article.png') +
        '" class="meta-button" alt="' + LBS.t('articles') + LBS.t('rss_feed') +
        '" /></a>',
      '<a href="feed.asp?selected=true" title="' + LBS.t('selected') + LBS.t('rss_feed') +
        '" target="_blank"><img src="' + R.image('rss_selected.png') +
        '" class="meta-button" alt="' + LBS.t('selected') + LBS.t('rss_feed') +
        '" /></a>',
      '<a href="feed.asp?q=comment" title="' + LBS.t('comments') + LBS.t('rss_feed') +
        '" target="_blank"><img src="' + R.image('rss_comment.png') +
        '" class="meta-button" alt="' + LBS.t('comments') + LBS.t('rss_feed') +
        '" /></a>',
      '<a href="http://www.unicode.org/" title="Unicode.org" target="_blank">' +
        '<img src="' + R.image('utf8.png') +
        '" class="meta-button" alt="Unicode Encoding" /></a>',
      '<a href="http://creativecommons.org/licenses/by-nc-sa/1.0/" ' +
        'title="Creative Commons Licensed" target="_blank"><img src="' +
        R.image('cc.png') + '" class="meta-button" ' +
        'alt="Creative Commons Licensed" /></a>',
      '<a href="http://www.voidland.com/" title="Powered by LBS" target="_blank">' +
        '<img src="' + R.image('lbs.png') +
        '" class="meta-button" alt="Powered by LBS" /></a>'
    );
    R.setHtml(
      'panelStatsList',
      rows.map((row) => (row === '' ? '<br />' : row + '<br />')).join('\n')
    );
  }

  function sidebar(site, user) {
    const payload = LBS.data || {};
    const counters = payload.counters || {};
    R.setText('panelUserTitle', LBS.t('user_panel'));
    R.setText('panelCategoryTitle', LBS.t('categories'));
    R.setText('panelCalendarTitle', LBS.t('calendar'));
    R.setText('panelArticleTitle', LBS.t('recent_articles'));
    R.setText('panelCommentTitle', LBS.t('recent_comments'));
    R.setText('panelLinksTitle', LBS.t('links'));

    userPanel(user, site);
    categoryPanel(site);
    R.setHtml('panelCalendarBody', site.calendar_html || '');
    recentArticles(site);
    recentComments(site);
    buildSearchPanel();
    statsPanel(site, counters, user);
    R.setHtml('panelLinksBody', site.links_html || '');
  }

  // The ASP version includes global.asp from every page, so the sidebar markup
  // lives in one place here too. Pages that ship the markup inline (default.asp,
  // article.asp) keep theirs; the rest get it injected.
  function sidebarTemplate() {
    return [
      '<div id="innerSidebar">',
      '  <div id="panel_user" class="panel" style="display: none">',
      '  <h5 id="panelUserTitle">User Panel</h5>',
      '  <div class="panel-content">',
      '    <div class="comment-text" id="panelUserGreeting"></div><br />',
      '    <ul id="panelUserLinks"></ul>',
      '  </div>',
      '  </div>',
      '  <div id="panelUser" class="panel" style="display: none">',
      '  <h5>User Panel</h5>',
      '  <div class="panel-content">',
      '    <form id="loginForm" name="login" method="post" action="login.asp">',
      '    <table cellpadding="0" cellspacing="2" width="100%">',
      '      <tr><td align="right"><span id="loginUsernameLabel">Username</span>:</td>',
      '      <td><input name="username" type="text" size="12" maxlength="24" class="text" /></td></tr>',
      '      <tr><td align="right"><span id="loginPasswordLabel">Password</span>:</td>',
      '      <td><input name="password" type="password" size="12" maxlength="16" class="text" /></td></tr>',
      '      <tr id="loginScodeRow" style="display: none">',
      '      <td align="right"><span id="loginScodeLabel">Security Code</span>:</td>',
      '      <td><input name="scode" size="4" maxlength="4" type="text" class="text" />',
      '      <img id="loginScodeImage" alt="Security Code" /></td></tr>',
      '      <tr><td align="right"><span id="loginRememberLabel">Auto Login</span>:</td>',
      '      <td><input name="remember" type="checkbox" value="true" /></td></tr>',
      '      <tr><td align="center" id="loginRegisterRow">',
      '      <a href="register.asp" id="loginRegisterLink" ' +
        'style="text-decoration: underline; color: #666666;">Register Now</a></td>',
      '      <td><input name="Login" type="submit" id="loginSubmit" value="  Login  " class="button" /></td></tr>',
      '    </table>',
      '    </form>',
      '  </div>',
      '  </div>',
      '  <div id="panelCategory" class="panel">',
      '  <h5 id="panelCategoryTitle">Categories</h5>',
      '  <div class="panel-content"><ul id="panelCategoryList"></ul></div>',
      '  </div>',
      '  <div id="panelCalendar" class="panel">',
      '  <h5 id="panelCalendarTitle">Calendar</h5>',
      '  <div id="panelCalendarBody"></div>',
      '  </div>',
      '  <div id="panelArticle" class="panel">',
      '  <h5 id="panelArticleTitle">Recent Articles</h5>',
      '  <div class="panel-content"><ul id="panelArticleList"></ul></div>',
      '  </div>',
      '  <div id="panelComment" class="panel">',
      '  <h5 id="panelCommentTitle">Recent Comments</h5>',
      '  <div class="panel-content"><ul id="panelCommentList"></ul></div>',
      '  </div>',
      '  <div id="panelSearch" class="panel">',
      '  <h5 id="panelSearchTitle">Search</h5>',
      '  <div class="panel-content">',
      '    <form id="searchForm" name="searchForm" method="get" action="default.asp" onsubmit="return doSearch();">',
      '    <input name="q" type="text" id="q" class="text search-field" />',
      '    <select name="searchType" id="searchType"></select>',
      '    <input name="submit" type="submit" id="searchSubmit" value=" Search " class="button" />',
      '    </form>',
      '  </div>',
      '  </div>',
      '  <div id="panelStats" class="panel">',
      '  <h5 id="panelStatsTitle">Statistics</h5>',
      '  <div class="panel-content" id="panelStatsList"></div>',
      '  </div>',
      '  <div id="panelLinks" class="panel">',
      '  <h5 id="panelLinksTitle">Links</h5>',
      '  <div class="panel-content" id="panelLinksBody"></div>',
      '  </div>',
      '</div>',
    ].join('\n');
  }

  function footer() {
    R.setText('footerQueries', LBS.requests);
    R.setText('footerTime', Math.max(Date.now() - startedAt, 1));
  }

  async function mount(options) {
    const settings = options || {};
    const payload = await LBS.load();
    const sidebarNode = R.byId('sidebar');
    if (sidebarNode && !R.byId('innerSidebar')) {
      sidebarNode.innerHTML = sidebarTemplate();
    }
    const site = payload.site;
    site.categories = payload.sidebar ? payload.sidebar.categories : [];
    site.recent_articles = payload.sidebar ? payload.sidebar.recent_articles : [];
    site.recent_comments = payload.sidebar ? payload.sidebar.recent_comments : [];
    site.calendar_html = payload.sidebar ? payload.sidebar.calendar_html : '';
    site.links_html = site.links || '';

    header(site);
    sidebar(site, payload.user);
    bindLoginForm();
    footer();
    if (typeof settings.onReady === 'function') {
      settings.onReady(payload);
    }
    return payload;
  }

  return {
    mount,
    cutString,
    lengthW,
    escapeHtml: R.escapeHtml,
  };
})();

window.LBSLayout = LBSLayout;
