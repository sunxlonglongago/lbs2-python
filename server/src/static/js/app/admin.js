// Admin backend: port of admin.asp / source/src_admin.asp.
import './api.js';
import './render.js';
import './layout.js';

const R = window.LBSRender;

const SECTIONS = [
  ['', 'general_info'],
  ['settings', 'global_settings'],
  ['category', 'categories'],
  ['group', 'user_group'],
  ['smilies', 'smilies'],
  ['wordfilter', 'word_filter'],
  ['database', 'database'],
  ['attachment', 'attachments'],
  ['announce', 'announcement'],
  ['links', 'links'],
  ['misc', 'misc'],
];

function mount(html) {
  R.setHtml('adminMount', html);
}

function row(label, control) {
  return '<tr><td class="formbox-rowheader">' + label + ':</td>' +
    '<td class="formbox-content">' + control + '</td></tr>';
}

function textInput(name, value, size) {
  return '<input type="text" class="text" name="' + name + '" size="' +
    (size || 24) + '" value="' + R.escapeHtml(value) + '" />';
}

function checkbox(name, checked) {
  return '<input type="checkbox" name="' + name + '" value="1"' +
    (checked ? ' checked="checked"' : '') + ' />';
}

function select(name, options, value) {
  return '<select name="' + name + '">' + options.map(([optionValue, label]) =>
    '<option value="' + optionValue + '"' +
    (String(optionValue) === String(value) ? ' selected="selected"' : '') + '>' +
    label + '</option>').join('') + '</select>';
}

function message(style, text) {
  mount(R.messageBox(style === 'error' ? LBS.t('error') : LBS.t('op_done'), text, {
    style: style === 'error' ? 'errorbox' : 'messagebox',
    target: currentSectionUrl(),
    linkText: LBS.t('goback'),
  }));
}

function currentSectionUrl() {
  const section = R.params().get('in') || '';
  return section ? 'admin.asp?in=' + section : 'admin.asp';
}

function adminPanel() {
  R.setText('adminPanelTitle', LBS.t('admin_panel'));
  const links = SECTIONS.map(([name, key]) =>
    '<a href="admin.asp' + (name ? '?in=' + name : '') + '">- ' + LBS.t(key) +
    '</a><br />').join('');
  R.setHtml(
    'adminPanelLinks',
    links + '<br /><a href="#" id="adminLogout">- ' + LBS.t('logout') + '</a>'
  );
  const logout = R.byId('adminLogout');
  if (logout) {
    logout.addEventListener('click', async (event) => {
      event.preventDefault();
      await LBS.post('/api/admin/logout');
      window.location.reload();
    });
  }
}

function loginForm() {
  return '<div id="mainWrapper"><center><div class="messagebox">' +
    '<div class="messagebox-title">' + LBS.t('admin_login') + '</div>' +
    '<div class="messagebox-content"><center>' +
    '<form id="adminLoginForm" method="post" action="admin.asp?act=login" ' +
    'style="display: inline">' +
    '<input type="password" id="password" name="password" class="text" />&nbsp;' +
    '<input type="submit" id="submit" value=" ' + LBS.t('login') +
    ' " class="button" /></form></center></div></div></center></div>';
}

function generalInfo(info) {
  const rows = [
    row('LBS Version', '2.0.304 | ' +
      '<a href="#" id="siteStateToggle">' +
      (info.site_closed ? LBS.t('open_site') : LBS.t('close_site')) + '</a> | ' +
      '<a href="#" id="cleanCache">' + LBS.t('clean_cache') + '</a>'),
    row(LBS.t('server_software'), R.escapeHtml(info.software)),
    row(LBS.t('server_time'), R.escapeHtml(info.time)),
    row(LBS.t('app_path'), R.escapeHtml(info.data_dir)),
    row(LBS.t('db_path'), R.escapeHtml(info.database.path) + ' (' +
      info.database.size_text + ')'),
    row(LBS.t('stats'), LBS.t('articles') + ': ' + info.counters.counterArticle +
      ' | ' + LBS.t('comments') + ': ' + info.counters.counterComment + ' | ' +
      LBS.t('trackbacks') + ': ' + info.counters.counterTrackback + ' | ' +
      LBS.t('reg_users') + ': ' + info.counters.counterUser + ' | ' +
      LBS.t('visitors') + ': ' + info.counters.counterVisitor),
    row(LBS.t('online_user'), String(info.online)),
    row('Python', 'Flask (no ASP objects required)'),
  ];
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('general_info') + '</h4></div><div class="textbox-content">' +
    '<table cellpadding="2" cellspacing="1">' + rows.join('') +
    '</table></div></div>';
}

const SETTING_FIELDS = [
  ['blogtitle', 'blog_title', 'text', 40],
  ['blogdescription', 'blog_desc', 'text', 60],
  ['baseurl', 'blog_base_url', 'text', 40],
  ['logoimage', 'blog_logo_image', 'text', 40],
  ['blogwebmaster', 'webmaster_name', 'text', 24],
  ['blogwebmasteremail', 'webmaster_email', 'text', 24],
  ['bloglanguage', 'language_code', 'text', 8],
  ['defaultviewmode', 'default_view', 'select', [['0', 'Normal'], ['1', 'Article List']]],
  ['articleperpagenormal', 'article_per_page', 'text', 6],
  ['articleperpagelist', 'article_per_page', 'text', 6],
  ['listentryperpage', 'entry_per_page', 'text', 6],
  ['commentperpage', 'comment_per_page', 'text', 6],
  ['commenttimeorder', 'comment_time_order', 'select', [['0', 'time_asc'], ['1', 'time_desc']]],
  ['showtrackbackwithcomment', 'show_tb_w_comm', 'bool', null],
  ['showtrackbackposition', 'trackback', 'select',
    [['0', 'on_comm_top'], ['1', 'on_comm_top'], ['2', 'on_comm_bottom']]],
  ['recentarticlelist', 'recent_articles', 'text', 6],
  ['recentcommentlist', 'recent_comments', 'text', 6],
  ['enabledynamiccalendar', 'dynamic_calendar', 'bool', null],
  ['enablecontentautosplit', 'enable_split', 'bool', null],
  ['contentautosplitchars', 'split_at', 'text', 6],
  ['enableregister', 'enable_reg', 'bool', null],
  ['enablesecuritycode', 'enable_scode', 'bool', null],
  ['enabletrackbackin', 'enable_trackback', 'bool', null],
  ['enabletrackbackout', 'enable_trackback', 'bool', null],
  ['enablecomment', 'enable_comment', 'bool', null],
  ['maxcommentlength', 'max_comment_length', 'text', 6],
  ['enableguestbook', 'enable_guestbook', 'bool', null],
  ['entryperpageguestbook', 'gbook_page_size', 'text', 6],
  ['stylesheet', 'style_sheet', 'text', 40],
  ['imagefolder', 'image_folder', 'text', 40],
  ['smiliesfolder', 'smilies_folder', 'text', 40],
  ['smiliesperrow', 'smilies_per_row', 'text', 4],
  ['minpostduration', 'flood_control', 'text', 6],
  ['enablevisitorrecord', 'record_visitor', 'bool', null],
  ['maxvisitorrecord', 'record', 'text', 6],
  ['enableupload', 'enable_upload', 'bool', null],
  ['uploadsize', 'upload_size', 'text', 10],
  ['uploadpath', 'upload_path', 'text', 30],
  ['uploadtypes', 'upload_type', 'text', 40],
];

const SETTING_DB_NAMES = {
  blogtitle: 'blogTitle',
  blogdescription: 'blogDescription',
  baseurl: 'baseURL',
  logoimage: 'logoImage',
  blogwebmaster: 'blogWebMaster',
  blogwebmasteremail: 'blogWebMasterEmail',
  bloglanguage: 'blogLanguage',
  defaultviewmode: 'defaultViewMode',
  articleperpagenormal: 'articlePerPageNormal',
  articleperpagelist: 'articlePerPageList',
  listentryperpage: 'listEntryPerPage',
  commentperpage: 'commentPerPage',
  commenttimeorder: 'commentTimeOrder',
  showtrackbackwithcomment: 'showTrackbackWithComment',
  showtrackbackposition: 'showTrackbackPosition',
  recentarticlelist: 'recentArticleList',
  recentcommentlist: 'recentCommentList',
  enabledynamiccalendar: 'enableDynamicCalendar',
  enablecontentautosplit: 'enableContentAutoSplit',
  contentautosplitchars: 'contentAutoSplitChars',
  enableregister: 'enableRegister',
  enablesecuritycode: 'enableSecurityCode',
  enabletrackbackin: 'enableTrackbackIn',
  enabletrackbackout: 'enableTrackbackOut',
  enablecomment: 'enableComment',
  maxcommentlength: 'maxCommentLength',
  enableguestbook: 'enableGuestBook',
  entryperpageguestbook: 'entryPerPageGuestBook',
  stylesheet: 'styleSheet',
  imagefolder: 'imageFolder',
  smiliesfolder: 'smiliesFolder',
  smiliesperrow: 'smiliesPerRow',
  minpostduration: 'minPostDuration',
  enablevisitorrecord: 'enableVisitorRecord',
  maxvisitorrecord: 'maxVisitorRecord',
  enableupload: 'enableUpload',
  uploadsize: 'uploadSize',
  uploadpath: 'uploadPath',
  uploadtypes: 'uploadTypes',
};

function settingsForm(settings) {
  const rows = SETTING_FIELDS.map(([name, labelKey, kind, extra]) => {
    const value = settings[SETTING_DB_NAMES[name]];
    let control;
    if (kind === 'bool') {
      control = checkbox(name, !!value);
    } else if (kind === 'select') {
      control = select(name, extra.map(([v, k]) => [v, LBS.t(k)]), value);
    } else {
      control = textInput(name, value === undefined ? '' : value, extra);
    }
    return row(LBS.t(labelKey), control);
  });
  rows.push('<tr><td></td><td class="formbox-content">' +
    '<input type="submit" id="saveSettings" value=" ' + LBS.t('save_change') +
    ' " class="button" /></td></tr>');
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('global_settings') + '</h4></div><div class="textbox-content">' +
    '<form id="settingsForm"><table cellpadding="2" cellspacing="1">' +
    rows.join('') + '</table></form></div></div>';
}

function categoriesForm(categories) {
  const rows = categories.map((category) => [
    '<tr>',
    '<td class="formbox-content"><input type="hidden" name="id" value="' +
      category.id + '" />' + textInput('name', category.name, 30) + '</td>',
    '<td class="formbox-content">' + textInput('order', category.order, 4) + '</td>',
    '<td class="formbox-content">' + checkbox('hidden', category.hidden) + '</td>',
    '<td class="formbox-content">' + checkbox('locked', category.locked) + '</td>',
    '<td class="formbox-content">' + checkbox('selected', false) + '</td>',
    '</tr>',
  ].join('')).join('');
  const newRow = [
    '<tr>',
    '<td class="formbox-content"><input type="hidden" name="id" value="0" />' +
      textInput('name', '', 30) + '</td>',
    '<td class="formbox-content">' + textInput('order', categories.length + 1, 4) + '</td>',
    '<td class="formbox-content">' + checkbox('newhidden', false) + '</td>',
    '<td class="formbox-content">' + checkbox('newlocked', false) + '</td>',
    '<td class="formbox-content">&nbsp;</td>',
    '</tr>',
  ].join('');
  const header = '<tr>' +
    '<td class="listbox-header">' + LBS.t('category') + '</td>' +
    '<td class="listbox-header">' + LBS.t('order') + '</td>' +
    '<td class="listbox-header">' + LBS.t('hidden') + '</td>' +
    '<td class="listbox-header">' + LBS.t('locked') + '</td>' +
    '<td class="listbox-header">' + LBS.t('delete') + '</td></tr>';
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('categories') + '</h4></div><div class="textbox-content">' +
    '<form id="categoryForm"><table cellpadding="2" cellspacing="1" width="100%">' +
    header + rows + newRow + '</table>' +
    '<div style="padding-top:8px">' +
    '<input type="button" id="saveCategories" value=" ' + LBS.t('save_change') +
    ' " class="button" /> ' +
    '<input type="button" id="deleteCategories" value=" ' + LBS.t('delete_cat') +
    ' " class="button" /> ' +
    '<input type="button" id="moveCategories" value=" ' + LBS.t('move_cat') +
    ' " class="button" /> ' +
    select('target', [['0', '- ' + LBS.t('select_target_cat') + ' -']].concat(
      categories.map((category) => [String(category.id), category.name])), 0) +
    '</div><div class="comment-text">' + LBS.t('delete_cat_note') + '</div>' +
    '</form></div></div>';
}

function groupsForm(groups) {
  const levels = (name, max) => {
    const options = [];
    for (let value = 0; value <= max; value += 1) {
      options.push([String(value), value === 0 ? LBS.t('disabled') :
        (value === 1 ? LBS.t('self') : LBS.t('all'))]);
    }
    return options;
  };
  const rows = groups.map((group) => {
    const rights = group.rights.padEnd(5, '0');
    const cells = [
      '<td class="formbox-content"><input type="hidden" name="id" value="' +
        group.id + '" />' +
        (group.id === 1
          ? R.escapeHtml(group.name) + '<input type="hidden" name="name" value="' +
            R.escapeHtml(group.name) + '" />'
          : textInput('name', group.name, 20)) + '</td>',
    ];
    const specs = [['view', 3], ['post', 2], ['edit', 2], ['delete', 2], ['upload', 1]];
    specs.forEach(([key, max], index) => {
      const value = parseInt(rights.charAt(index), 10) || 0;
      cells.push('<td class="formbox-content" data-right="' + key + '">' +
        (group.id === 1 ? String(value) : select(key, levels(key, max), value)) +
        '</td>');
    });
    cells.push('<td class="formbox-content">' + checkbox('selected', false) + '</td>');
    return '<tr>' + cells.join('') + '</tr>';
  }).join('');
  const newRow = [
    '<tr>',
    '<td class="formbox-content"><input type="hidden" name="id" value="0" />' +
      textInput('name', '', 20) + '</td>',
    '<td class="formbox-content">' + select('view', levels('view', 3), 1) + '</td>',
    '<td class="formbox-content">' + select('post', levels('post', 2), 0) + '</td>',
    '<td class="formbox-content">' + select('edit', levels('edit', 2), 0) + '</td>',
    '<td class="formbox-content">' + select('delete', levels('delete', 2), 0) + '</td>',
    '<td class="formbox-content">' + select('upload', levels('upload', 1), 0) + '</td>',
    '<td class="formbox-content">&nbsp;</td>',
    '</tr>',
  ].join('');
  const header = '<tr>' +
    '<td class="listbox-header">' + LBS.t('user_group') + '</td>' +
    '<td class="listbox-header">' + LBS.t('view') + '</td>' +
    '<td class="listbox-header">' + LBS.t('post') + '</td>' +
    '<td class="listbox-header">' + LBS.t('edit') + '</td>' +
    '<td class="listbox-header">' + LBS.t('delete') + '</td>' +
    '<td class="listbox-header">' + LBS.t('upload') + '</td>' +
    '<td class="listbox-header">' + LBS.t('delete') + '</td></tr>';
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('user_group') + '</h4></div><div class="textbox-content">' +
    '<form id="groupForm"><table cellpadding="2" cellspacing="1">' + header + rows +
    newRow + '</table><div style="padding-top:8px">' +
    '<input type="button" id="saveGroups" value=" ' + LBS.t('save_change') +
    ' " class="button" /> ' +
    '<input type="button" id="deleteGroups" value=" ' + LBS.t('delete_group') +
    ' " class="button" /></div>' +
    '<div class="comment-text">' + LBS.t('delete_group_note') + '</div>' +
    '</form></div></div>';
}

function smiliesForm(smilies) {
  const rows = smilies.map((smiley) => '<tr>' +
    '<td class="formbox-content"><input type="hidden" name="id" value="' +
      smiley.id + '" />' + textInput('code', smiley.code, 16) + '</td>' +
    '<td class="formbox-content">' + textInput('image', smiley.image, 30) +
      ' <img src="' + R.imageFolder() + '/smilies/' +
      R.escapeHtml(smiley.image) + '" alt="" /></td>' +
    '<td class="formbox-content">' + checkbox('selected', false) + '</td></tr>').join('');
  const newRow = '<tr>' +
    '<td class="formbox-content"><input type="hidden" name="id" value="0" />' +
      textInput('code', '', 16) + '</td>' +
    '<td class="formbox-content">' + textInput('image', '', 30) + '</td>' +
    '<td class="formbox-content">&nbsp;</td></tr>';
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('smilies') + '</h4></div><div class="textbox-content">' +
    '<form id="smiliesForm"><table cellpadding="2" cellspacing="1">' +
    '<tr><td class="listbox-header">' + LBS.t('code') + '</td>' +
    '<td class="listbox-header">' + LBS.t('image') + '</td>' +
    '<td class="listbox-header">' + LBS.t('delete') + '</td></tr>' +
    rows + newRow + '</table><div style="padding-top:8px">' +
    '<input type="button" id="saveSmilies" value=" ' + LBS.t('save_change') +
    ' " class="button" /> ' +
    '<input type="button" id="deleteSmilies" value=" ' + LBS.t('delete_smilies') +
    ' " class="button" /></div></form></div></div>';
}

function wordFilterForm(filters) {
  const modeOptions = [['0', LBS.t('replace')], ['1', LBS.t('block')]];
  const rows = filters.map((filter) => '<tr>' +
    '<td class="formbox-content"><input type="hidden" name="id" value="' +
      filter.id + '" />' + select('mode', modeOptions, filter.mode) + '</td>' +
    '<td class="formbox-content">' + textInput('text', filter.text, 20) + '</td>' +
    '<td class="formbox-content">' + textInput('replace', filter.replace, 20) + '</td>' +
    '<td class="formbox-content">' + checkbox('regexp', filter.regexp) + '</td>' +
    '<td class="formbox-content">' + checkbox('selected', false) + '</td></tr>').join('');
  const newRow = '<tr>' +
    '<td class="formbox-content"><input type="hidden" name="id" value="0" />' +
      select('mode', modeOptions, 0) + '</td>' +
    '<td class="formbox-content">' + textInput('text', '', 20) + '</td>' +
    '<td class="formbox-content">' + textInput('replace', '', 20) + '</td>' +
    '<td class="formbox-content">' + checkbox('newregexp', false) + '</td>' +
    '<td class="formbox-content">&nbsp;</td></tr>';
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('word_filter') + '</h4></div><div class="textbox-content">' +
    '<form id="wordFilterForm"><table cellpadding="2" cellspacing="1">' +
    '<tr><td class="listbox-header">' + LBS.t('mode') + '</td>' +
    '<td class="listbox-header">' + LBS.t('word_filter') + '</td>' +
    '<td class="listbox-header">' + LBS.t('replace') + '</td>' +
    '<td class="listbox-header">' + LBS.t('regexp') + '</td>' +
    '<td class="listbox-header">' + LBS.t('delete') + '</td></tr>' +
    rows + newRow + '</table><div style="padding-top:8px">' +
    '<input type="button" id="saveWordFilter" value=" ' + LBS.t('save_change') +
    ' " class="button" /> ' +
    '<input type="button" id="deleteWordFilter" value=" ' + LBS.t('delete_wordfilter') +
    ' " class="button" /></div></form></div></div>';
}

function databasePage(info) {
  const backups = (info.backups || []).map((backup) => '<tr>' +
    '<td class="listbox-entry">' + R.escapeHtml(backup.name) + '</td>' +
    '<td class="listbox-entry">' + backup.size_text + '</td>' +
    '<td class="listbox-entry">' + R.escapeHtml(backup.mtime) + '</td>' +
    '<td class="listbox-entry">' +
    '<a href="#" data-restore="' + R.escapeHtml(backup.name) + '">' +
    LBS.t('restore') + '</a> | ' +
    '<a href="#" data-delete="' + R.escapeHtml(backup.name) + '">' +
    LBS.t('delete') + '</a></td></tr>').join('');
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('database') + '</h4></div><div class="textbox-content">' +
    '<table cellpadding="2" cellspacing="1">' +
    row(LBS.t('db_path'), R.escapeHtml(info.path)) +
    row(LBS.t('db_size'), info.size_text) +
    '</table><div style="padding-top:8px">' +
    '<input type="button" id="dbCompact" value=" ' + LBS.t('compact') +
    ' " class="button" /> ' +
    '<input type="button" id="dbBackup" value=" ' + LBS.t('backup') +
    ' " class="button" /></div>' +
    '<h5>' + LBS.t('backup_list') + '</h5>' +
    '<table cellpadding="2" cellspacing="1" width="100%">' + backups +
    '</table></div></div>';
}

function attachmentsPage(listing) {
  const rows = listing.items.map((item) => '<tr>' +
    '<td class="listbox-entry">' +
    (item.type === 'folder'
      ? '<a href="admin.asp?in=attachment&amp;path=' +
        encodeURIComponent((listing.path ? listing.path + '/' : '') + item.name) +
        '">' + R.escapeHtml(item.name) + '/</a>'
      : R.escapeHtml(item.name)) + '</td>' +
    '<td class="listbox-entry">' + item.size_text + '</td>' +
    '<td class="listbox-entry"><a href="#" data-file="' + R.escapeHtml(item.name) +
    '" data-type="' + item.type + '">' + LBS.t('delete') + '</a></td></tr>').join('');
  const parent = listing.path
    ? '<a href="admin.asp?in=attachment&amp;path=' +
      encodeURIComponent(listing.path.split('/').slice(0, -1).join('/')) + '">' +
      LBS.t('parent_folder') + '</a>'
    : '';
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('attachments') + '</h4></div><div class="textbox-content">' +
    '<div>' + parent + '</div>' +
    '<table cellpadding="2" cellspacing="1" width="100%">' +
    rows + '</table>' +
    '<div class="comment-text">' + LBS.t('delete_folder_note') + '</div>' +
    '</div></div>';
}

function announcePage(announcement) {
  return '<div class="textbox"><div class="textbox-title"><h4>' +
    LBS.t('announcement') + '</h4></div><div class="textbox-content">' +
    '<form id="announceForm"><table cellpadding="2" cellspacing="1">' +
    row(LBS.t('show_announce'), checkbox('show', announcement.show)) +
    row(LBS.t('e_ubb'), checkbox('e_ubb',
      announcement.ubb_flags !== 'html' && announcement.ubb_flags.charAt(0) === '1') +
      checkbox('e_autourl', false) + ' ' + LBS.t('e_autourl') + ' ' +
      checkbox('e_image', false) + ' ' + LBS.t('e_image') + ' ' +
      checkbox('e_media', false) + ' ' + LBS.t('e_media') + ' ' +
      checkbox('e_smilies', false) + ' ' + LBS.t('e_smilies') + ' ' +
      checkbox('e_html', announcement.ubb_flags === 'html') + ' ' + LBS.t('e_html')) +
    '<tr><td class="formbox-rowheader" valign="top">' + LBS.t('content') +
    ':</td><td class="formbox-content">' +
    '<textarea name="message" rows="8" cols="60" style="width:100%">' +
    R.escapeHtml(announcement.message) + '</textarea></td></tr>' +
    '</table><div style="padding-top:8px">' +
    '<input type="submit" value=" ' + LBS.t('save_change') +
    ' " class="button" /></div></form></div></div>';
}

function linksPage(links) {
  return '<div class="textbox"><div class="textbox-title"><h4>' + LBS.t('links') +
    '</h4></div><div class="textbox-content">' +
    '<form id="linksForm">' +
    '<textarea name="links" rows="8" cols="60" style="width:100%">' +
    R.escapeHtml(links) + '</textarea>' +
    '<div style="padding-top:8px"><input type="submit" value=" ' +
    LBS.t('save_change') + ' " class="button" /></div></form></div></div>';
}

function miscPage(info) {
  const buttons = [
    ['resync_g', 'resync_global_stats'],
    ['resync_c', 'resync_cat_stats'],
    ['resync_a', 'resync_article_stats'],
    ['resync_u', 'resync_user_stats'],
    ['clean_u', 'clean_user'],
    ['clean_vc', 'clean_visitor_record'],
    ['clean_gb', 'clean_gbook_record'],
  ].map(([action, key]) =>
    '<input type="button" data-misc="' + action + '" value=" ' + LBS.t(key) +
    ' " class="button" /><br />').join('');
  return '<div class="textbox"><div class="textbox-title"><h4>' + LBS.t('misc') +
    '</h4></div><div class="textbox-content">' + buttons +
    '<div class="comment-text">' + LBS.t('resync_note') + '</div>' +
    '<div id="miscResult"></div>' +
    '<div style="padding-top:8px">' +
    '<input type="button" id="siteToggle" value=" ' +
    (info.site_closed ? LBS.t('open_site') : LBS.t('close_site')) +
    ' " class="button" /></div></div></div>';
}

// --- form collection helpers ------------------------------------------------

function collectRows(form, fields) {
  const rows = [];
  form.querySelectorAll('input[name=id]').forEach((hidden, index) => {
    const row = form.querySelectorAll('input[name=id]')[index].closest('tr');
    const entry = { id: hidden.value };
    fields.forEach((field) => {
      const node = row.querySelector('[name="' + field + '"]');
      if (!node) {
        entry[field] = '';
        return;
      }
      if (node.type === 'checkbox') {
        entry[field] = node.checked;
      } else {
        entry[field] = node.value;
      }
    });
    rows.push(entry);
  });
  return rows;
}

function selectedIds(form) {
  const ids = [];
  form.querySelectorAll('input[name=id]').forEach((hidden) => {
    const row = hidden.closest('tr');
    const box = row.querySelector('input[name=selected]');
    if (box && box.checked) {
      ids.push(hidden.value);
    }
  });
  return ids;
}

function rowsToColumns(rows) {
  const columns = {};
  Object.keys(rows[0] || {}).forEach((key) => {
    columns[key] = rows.map((row) => row[key]);
  });
  return columns;
}

// --- sections ---------------------------------------------------------------

async function renderGeneral() {
  const info = await LBS.get('/api/admin/info');
  mount(generalInfo(info));
  const toggle = R.byId('siteStateToggle');
  toggle.addEventListener('click', async (event) => {
    event.preventDefault();
    await LBS.post('/api/admin/site-state', { closed: !info.site_closed });
    renderGeneral();
  });
  R.byId('cleanCache').addEventListener('click', async (event) => {
    event.preventDefault();
    message('done', LBS.t('op_done'));
  });
}

async function renderSettings() {
  const data = await LBS.get('/api/admin/settings');
  mount(settingsForm(data.settings));
  R.byId('settingsForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {};
    SETTING_FIELDS.forEach(([name, , kind]) => {
      const node = document.querySelector('#settingsForm [name="' + name + '"]');
      if (!node) {
        return;
      }
      payload[name] = kind === 'bool' ? node.checked : node.value;
    });
    const result = await LBS.post('/api/admin/settings', payload);
    message('done', LBS.t('op_done') + ' (' + result.written.length + ')');
  });
}

async function renderCategories() {
  const data = await LBS.get('/api/admin/categories');
  mount(categoriesForm(data.categories));
  const form = R.byId('categoryForm');
  R.byId('saveCategories').addEventListener('click', async () => {
    const rows = collectRows(form, ['name', 'order', 'hidden']);
    await LBS.post('/api/admin/categories', { act: 'update', ...rowsToColumns(rows) });
    message('done', LBS.t('op_done'));
  });
  R.byId('deleteCategories').addEventListener('click', async () => {
    const selected = selectedIds(form);
    if (!selected.length || !window.confirm(LBS.t('delete_cat') + '?')) {
      return;
    }
    await LBS.post('/api/admin/categories', { act: 'delete', selected });
    message('done', LBS.t('op_done'));
  });
  R.byId('moveCategories').addEventListener('click', async () => {
    const selected = selectedIds(form);
    const target = form.target.value;
    if (!selected.length || target === '0') {
      window.alert(LBS.t('select_target_cat'));
      return;
    }
    await LBS.post('/api/admin/categories', { act: 'move', selected, target });
    message('done', LBS.t('op_done'));
  });
}

async function renderGroups() {
  const data = await LBS.get('/api/admin/groups');
  mount(groupsForm(data.groups));
  const form = R.byId('groupForm');
  R.byId('saveGroups').addEventListener('click', async () => {
    const rows = [];
    form.querySelectorAll('input[name=id]').forEach((hidden) => {
      const rowNode = hidden.closest('tr');
      const entry = { id: hidden.value };
      ['name', 'view', 'post', 'edit', 'delete', 'upload'].forEach((field) => {
        const node = rowNode.querySelector('[name="' + field + '"]');
        if (!node) {
          entry[field] = 0;
        } else if (node.tagName === 'SELECT') {
          entry[field] = node.value;
        } else {
          entry[field] = node.value;
        }
      });
      rows.push(entry);
    });
    await LBS.post('/api/admin/groups', { act: 'update', ...rowsToColumns(rows) });
    message('done', LBS.t('op_done'));
  });
  R.byId('deleteGroups').addEventListener('click', async () => {
    const selected = selectedIds(form);
    if (!selected.length || !window.confirm(LBS.t('delete_group') + '?')) {
      return;
    }
    await LBS.post('/api/admin/groups', { act: 'delete', selected });
    message('done', LBS.t('op_done'));
  });
}

async function renderSmilies() {
  const data = await LBS.get('/api/admin/smilies');
  mount(smiliesForm(data.smilies));
  const form = R.byId('smiliesForm');
  R.byId('saveSmilies').addEventListener('click', async () => {
    const rows = collectRows(form, ['code', 'image']);
    await LBS.post('/api/admin/smilies', { act: 'update', ...rowsToColumns(rows) });
    message('done', LBS.t('op_done'));
  });
  R.byId('deleteSmilies').addEventListener('click', async () => {
    const selected = selectedIds(form);
    if (!selected.length || !window.confirm(LBS.t('delete_smilies') + '?')) {
      return;
    }
    await LBS.post('/api/admin/smilies', { act: 'delete', selected });
    message('done', LBS.t('op_done'));
  });
}

async function renderWordFilter() {
  const data = await LBS.get('/api/admin/wordfilter');
  mount(wordFilterForm(data.filters));
  const form = R.byId('wordFilterForm');
  R.byId('saveWordFilter').addEventListener('click', async () => {
    const rows = collectRows(form, ['mode', 'text', 'replace', 'regexp']);
    await LBS.post('/api/admin/wordfilter', { act: 'update', ...rowsToColumns(rows) });
    message('done', LBS.t('op_done'));
  });
  R.byId('deleteWordFilter').addEventListener('click', async () => {
    const selected = selectedIds(form);
    if (!selected.length || !window.confirm(LBS.t('delete_wordfilter') + '?')) {
      return;
    }
    await LBS.post('/api/admin/wordfilter', { act: 'delete', selected });
    message('done', LBS.t('op_done'));
  });
}

async function renderDatabase() {
  const data = await LBS.get('/api/admin/database');
  mount(databasePage(data.database));
  R.byId('dbCompact').addEventListener('click', async () => {
    await LBS.post('/api/admin/database', { act: 'compact' });
    message('done', LBS.t('compact_db') + ' - ' + LBS.t('op_done'));
  });
  R.byId('dbBackup').addEventListener('click', async () => {
    const result = await LBS.post('/api/admin/database', { act: 'backup' });
    message('done', LBS.t('copy_to_backup') + ': ' + result.name);
  });
  document.querySelectorAll('[data-restore]').forEach((link) => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      const name = link.getAttribute('data-restore');
      if (!window.confirm(LBS.t('confirm_restore'))) {
        return;
      }
      await LBS.post('/api/admin/database', { act: 'restore', file: name });
      message('done', LBS.t('restore_db') + ' - ' + LBS.t('op_done'));
    });
  });
  document.querySelectorAll('[data-delete]').forEach((link) => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      await LBS.post('/api/admin/database', {
        act: 'delete', file: link.getAttribute('data-delete'),
      });
      renderDatabase();
    });
  });
}

async function renderAttachments() {
  const path = R.params().get('path') || '';
  const listing = await LBS.get('/api/admin/attachments?path=' + encodeURIComponent(path));
  mount(attachmentsPage(listing));
  document.querySelectorAll('[data-file]').forEach((link) => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      const name = link.getAttribute('data-file');
      const isFolder = link.getAttribute('data-type') === 'folder';
      const prompt = isFolder ? LBS.t('confirm_delete_folder')
        : LBS.t('confirm_delete_file');
      if (!window.confirm(prompt)) {
        return;
      }
      await LBS.post('/api/admin/attachments', { path: listing.path, name });
      renderAttachments();
    });
  });
}

async function renderAnnounce() {
  const data = await LBS.get('/api/admin/announce');
  mount(announcePage(data.announcement));
  const form = R.byId('announceForm');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    await LBS.post('/api/admin/announce', {
      show: form.show.checked,
      message: form.message.value,
      e_ubb: form.e_ubb.checked,
      e_autourl: form.e_autourl.checked,
      e_image: form.e_image.checked,
      e_media: form.e_media.checked,
      e_smilies: form.e_smilies.checked,
      e_html: form.e_html.checked,
    });
    message('done', LBS.t('op_done'));
  });
}

async function renderLinks() {
  const data = await LBS.get('/api/admin/links');
  mount(linksPage(data.links));
  const form = R.byId('linksForm');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    await LBS.post('/api/admin/links', { links: form.links.value });
    message('done', LBS.t('op_done'));
  });
}

async function renderMisc() {
  const info = await LBS.get('/api/admin/info');
  mount(miscPage(info));
  document.querySelectorAll('[data-misc]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = button.getAttribute('data-misc');
      let result = await LBS.post('/api/admin/misc', { act: action, start: 1 });
      // resync_a / resync_u walk the tables in pages, like the ASP version.
      while (result.next) {
        result = await LBS.post('/api/admin/misc', { act: action, start: result.next });
      }
      R.setHtml('miscResult', '<div class="messagebox"><div class="messagebox-title">' +
        LBS.t('op_done') + '</div><div class="messagebox-content">' +
        R.escapeHtml(JSON.stringify(result)) + '</div></div>');
    });
  });
  R.byId('siteToggle').addEventListener('click', async () => {
    await LBS.post('/api/admin/site-state', { closed: !info.site_closed });
    renderMisc();
  });
}

const RENDERERS = {
  '': renderGeneral,
  settings: renderSettings,
  category: renderCategories,
  group: renderGroups,
  smilies: renderSmilies,
  wordfilter: renderWordFilter,
  database: renderDatabase,
  attachment: renderAttachments,
  announce: renderAnnounce,
  links: renderLinks,
  misc: renderMisc,
};

async function main() {
  const payload = await window.LBSLayout.mount({});
  const user = payload.user;
  if (!user || user.group_id !== 1) {
    mount(R.messageBox(LBS.t('error'), LBS.t('no_rights'), {
      style: 'errorbox',
      target: 'default.asp',
      linkText: LBS.t('goback'),
    }));
    return;
  }
  const section = (R.params().get('in') || '').toLowerCase();
  adminPanel();

  const render = RENDERERS[section] || renderGeneral;
  try {
    await render();
  } catch (error) {
    if (error.status === 403 && error.data && error.data.error === 'admin_login') {
      mount(loginForm());
      const form = R.byId('adminLoginForm');
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
          await LBS.post('/api/admin/login', { password: form.password.value });
          window.location.reload();
        } catch (loginError) {
          message('error', LBS.t('password_invalid'));
        }
      });
      return;
    }
    mount(R.messageBox(LBS.t('error'), R.escapeHtml(error.message), {
      style: 'errorbox',
      target: 'default.asp',
      linkText: LBS.t('goback'),
    }));
  }
}

main();
