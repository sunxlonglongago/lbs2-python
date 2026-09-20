# Frontend design

Goal: a 100% port of the static HTML/CSS/JS of the original LBS^2. The ASP pages
mixed server-side interpolation (`<%= ... %>`) into their markup; the port keeps
the DOM structure and styling and replaces the interpolation with `fetch` calls
plus plain JavaScript rendering.

## Assets kept verbatim

| Original | Port | Notes |
|---|---|---|
| `styles/default/{styles.css,images/**}` | `frontend/styles/default/` | default theme |
| `styles/evergreen/{styles.css,images/**}` | `frontend/styles/evergreen/` | theme two |
| `styles/oldschool/{styles.css,images/**}` | `frontend/styles/oldschool/` | theme three |
| `common.js` | `frontend/js/common.js` | sidebar, login box, quote, comment toggle, search, font size |
| `messageform.js` | `frontend/js/messageform.js` | UBB toolbar, smilies, caret insertion, form validation |

The active theme comes from the `styleSheet` / `imageFolder` / `smiliesFolder` /
`logoImage` settings, and neither the CSS nor the images were touched — which is
why the DOM ids and classes have to match the original exactly.

## Pages

| Original | File | Main blocks |
|---|---|---|
| `global.asp` | `js/app/layout.js` | header, blog title/description, menu, sidebar, footer |
| `default.asp` | `index.html` | announcement, view mode, pagination, article list, sidebar |
| `article.asp` | `article.html` | body, edit form, comments, trackbacks |
| `comment.asp` | `comment.html` | comment list, edit form |
| `user.asp` | `user.html` | profile, user list, edit form |
| `gbook.asp` | `gbook.html` | guestbook list, entry form, replies |
| `login.asp` | `login.html` | login form, auto-login choice |
| `register.asp` | `register.html` | agreement, registration form |
| `stats.asp` | `stats.html` | visitor statistics |
| `about.asp` | `about.html` | static content template |
| `admin.asp` | `admin.html` | every admin section |
| `trackback.asp` | `trackback.html` | trackback list |
| `upload.asp` | `upload.html` | upload frame embedded by the message forms |

The file names above are what lives in `frontend/`; **the public URLs are the
`.asp` ones**. `index.html` is served as `default.asp`, `article.html` as
`article.asp?id=N`, and so on. `app.PAGE_REDIRECTS` 302s every `.html` URL to its
`.asp` form, which also means the `default.asp` / `comment.asp` / `gbook.asp` /
`trackback.asp` paths hard-coded inside `common.js` needed no changes. The upload
page is addressed as `upload.asp` too.

## Rendering

- Each page is a static HTML skeleton that keeps the original ids and classes:
  `#wrapper`, `#innerWrapper`, `#header`, `#sidebar`, `.panel`, `.textbox`,
  `.textbox-title`, `.textbox-content`, `.textbox-bottom`, `.listbox`, `.pages`,
  `.announce` and friends.
- `layout.js` plays the role of `global.asp`: it fills the header, the sidebar
  panels and the footer from `/api/site.asp` (site title, description, theme
  paths, categories, calendar, announcement, recent articles/comments, links,
  counters, current user and rights).
- All data comes from the `/api/*.asp` endpoints; the API client appends the
  suffix in one place, and raw `fetch` call sites go through `LBS.api()`.
- Interaction keeps the original URL semantics: `?mode=`, `?cat=`, `?user=`,
  `?q=`, `?hl=`, `?date=`, `?selected=`, `?page=` — old links and bookmarks keep
  working.
- `common.js` and `messageform.js` are used as-is, with their original function
  names and call sites. The one adaptation is that forms which rely on
  `form.submit()` from `CheckInputForm()` have that method overridden so the
  request goes through `fetch`; the files themselves are untouched.

## Layers

```
frontend/
├── index.html article.html comment.html user.html gbook.html
├── login.html register.html stats.html about.html admin.html
├── trackback.html upload.html
├── js/
│   ├── common.js            original, untouched
│   ├── messageform.js       original, untouched
│   └── app/
│       ├── api.js           request wrapper, .asp suffix, language strings
│       ├── render.js        escaping, message boxes, page URLs
│       ├── layout.js        header / sidebar / footer + login handling
│       ├── commentform.js   shared comment and guestbook form
│       └── *.js             one loader per page
└── styles/{default,evergreen,oldschool}/
```

## Language

English only. The strings are ported from `lang/blog.asp` and `lang/admin.asp`
into `server/src/lang.py` and served through `/api/lang.asp`, so the key names
still line up with the original `lang[...]` lookups and both sides share one
source of truth.

## Build

No component framework and no bundler: `make fe` simply copies `frontend/` into
`server/src/static/`, which Flask serves. The output is committed, so a
deployment host needs no frontend toolchain at all.
