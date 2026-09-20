# LBS^2 → Python porting plan

Porting LBS^2 v2.0.304 (ASP + JScript + ADODB + Access 2000) into this project:
Python backend + SQLite + a plain static frontend.

This directory is the implementation baseline. Every finished item is ticked
from `[ ]` to `[x]`, and the descriptions are kept in sync with the code.

## Decisions

1. Runtime is Python 3.10.6 (not 3.12).
2. Table and column names match the Access original exactly, with no renaming
   (the `blog_` prefix is kept).
3. The UI is English only (reusing the strings from `lang/blog.asp` and
   `lang/admin.asp`).
4. Every table gets one hello-world style demo row.
5. The schema comes from the Python derivation (`access_parser` reading the Jet
   table definition pages, cross-checked against the ASP code semantics).
   Verifying with mdbtools is no longer a required step.
6. The security code (`scode.asp`) is disabled for now: `enableSecurityCode = 0`,
   the frontend renders no captcha row, and `/scode` stays unimplemented.
7. Public URLs keep the ASP look: pages and API both end in `.asp`. A WSGI
   middleware (`app.AspPathMiddleware`) strips the suffix before routing, the
   files stay `.html`, and every `.html` URL 302s to its `.asp` form.

## Stack

The backend follows an already proven Flask project skeleton:

- Python 3.10.6, Flask, stdlib `sqlite3` (no ORM: `sqlite3.Row` plus
  parameterised SQL), `requests`.
- `uv` + `pyproject.toml` + `uv.lock` for dependencies and the virtualenv.
- A root `Makefile` driving build / dev / install / update / service-install /
  test.
- Production runs as a systemd service, optionally behind nginx.
- The runtime data directory is given by `--data`; the database, `secret_key`,
  caches and backups all live inside it.

The frontend deliberately avoids React/Vite: the requirement is a 100% port of
the static HTML/CSS/JS the ASP pages emitted, and a component framework would
change the DOM and break the three bundled theme stylesheets.

## Layout

```
lbs2-python/
├── Makefile                 root build entry point
├── README.md  AGENTS.md
├── docs/
│   ├── plan/                this plan
│   ├── database.md          data dictionary (generated)
│   ├── api.md               API reference (generated)
│   └── openapi.json         generated OpenAPI description
├── frontend/                static frontend sources
│   ├── *.html               page skeletons (served as *.asp)
│   ├── styles/              three themes, copied verbatim
│   └── js/                  common.js + messageform.js (verbatim) and app/
└── server/
    ├── Makefile
    ├── tests/api_e2e/       end-to-end scenarios + generated CASES.md
    └── src/
        ├── app.py           Flask app, routes, .asp middleware
        ├── config.py db.py schema.py utils.py
        ├── auth.py users.py cache.py settings.py state.py
        ├── articles.py comments.py guestbook.py trackback.py
        ├── ubbcode.py feed.py stats.py uploads.py visitors.py
        ├── admin.py calendar_view.py lang.py
        ├── openapi_spec.py export_openapi.py
        ├── tools/           import_access, seed_demo, dump_schema,
        │                    access_reference, export_docs
        ├── deploy/          systemd unit + nginx example
        └── static/          frontend output (committed)
```

## Task list

### M0 Data layer

- [x] T0.1 `schema.py`: SQLite DDL and indexes for the 11 tables
- [x] T0.2 `tools/import_access.py`: import `blog.mdb` / `gbook.mdb` into SQLite
- [x] T0.3 `tools/seed_demo.py`: one hello world row per table
- [x] T0.4 `tools/dump_schema.py`: dump the SQLite schema and diff it column by
      column against the Access reference
- [x] T0.5 ~~mdbtools verification~~: dropped by decision 5 (mdbtools 1.0.1 is
      installed if a manual `mdb-schema` comparison is ever wanted)

### M1 Backend skeleton

- [x] T1.1 `pyproject.toml`, `.python-version`, uv environment
- [x] T1.2 `config.py`: `--data` directory, password hashing
- [x] T1.3 `db.py`: connections, schema creation, transactions, query/insert helpers
- [x] T1.4 `users.py`: user CRUD, password verification, legacy MD5 upgrade
- [x] T1.5 `auth.py`: session login, `before_app_request` guard, `data/secret_key`
- [x] T1.6 `settings.py` / `cache.py`: settings, groups, categories, smilies and
      word filters, with caching
- [x] T1.7 `app.py`: application setup, static serving, error handling, `--data`
- [x] T1.8 root `Makefile` and `server/Makefile`
- [x] T1.9 `openapi_spec.py` plus the `docs/openapi.json` generator (`make docs`)

### M2 Read-only frontend

- [x] T2.1 `GET /api/articles`: category / author / selected / search / date /
      view mode plus pagination
- [x] T2.2 `GET /api/articles/<id>`: body, neighbours, comments, trackbacks
- [x] T2.3 `GET /api/categories`, `/api/archive` (calendar), `/api/stats`
- [x] T2.4 frontend skeleton: `layout.js` recreating `global.asp`'s
      header/sidebar/footer
- [x] T2.5 index page: normal and list views, announcement, pagination bar
- [x] T2.6 article page: body, UBB rendering, comment list, trackback list
- [x] T2.7 the three themes (`styleSheet` / `imageFolder` / `smiliesFolder` /
      `logoImage`)

### M3 Interactive features

- [x] T3.1 create / edit / delete articles (`act=new|edit|save|update|delete`)
- [x] T3.2 comments (`act=save|update|delete`) with guest posting and
      username/password auto-login
- [x] T3.2b guestbook (the `gbook.asp` page and its endpoints)
- [x] T3.3 UBB toolbar, smilies panel, Ctrl+Enter, form validation (reusing
      `messageform.js` verbatim)
- [x] T3.4 sidebar toggle, login box, quote, comment toggle, search, font size
      (reusing `common.js` verbatim)
- [x] T3.5 search highlighting, width-aware length, pagination links

### M4 Authentication and permissions

- [x] T4.1 login / logout / registration (captcha disabled per decision 6)
- [x] T4.2 user pages: profile, user list, profile edit, password change, delete
- [x] T4.3 permission matrix: the five `group_rights` digits →
      `view/post/edit/delete/upload`
- [x] T4.4 article visibility: `log_mode` 1–4 and `cat_hidden`
- [x] T4.5 visitor records and the online counter

### M5 Admin backend

- [x] T5.1 settings / category / group / smilies / wordfilter
- [x] T5.2 database: compact / backup / restore / cleanup / `resync_*`
- [x] T5.3 attachments: browse and delete
- [x] T5.4 announcement / links / misc (close and open the site)

### M6 Advanced features

- [x] T6.1 trackback receive and send, plus the trackback list page
- [x] T6.2 RSS feed (`/feed`, including `?cat=`, `?selected=`, `?q=comment`,
      `?type=js`)
- [x] T6.3 file upload (`upload.asp`) with type and size limits
- [x] T6.4 statistics page (`stats.asp`)

### M7 Documentation and tests

- [x] T7.1 `docs/database.md`, generated by `tools/export_docs.py`
- [x] T7.2 `docs/api.md` and `docs/openapi.json`
- [x] T7.3 `server/tests/api_e2e/` scenarios plus generated `CASES.md`
- [x] T7.4 `make test_api_full` runs green (10 scenarios, 277 assertions)

## Behaviour contract with the original

These points have to stay equivalent to the ASP implementation:

- `blog_Settings`: `set_type=0` takes the value from `set_value0` (numeric),
  `set_type=1` from `set_value1` (string).
- Rights string: the five digits of `blog_UserGroup.group_rights` are
  `view/post/edit/delete/upload`, each 0/1/2/3.
- Article visibility: `log_mode` 1 public, 2 needs login, 3 needs `view>=2`,
  4 needs `view>=3`.
- Passwords: prefer `SHA1(password + user_salt)`; a legacy `MD5(password)` row is
  verified once and then upgraded with a fresh salt.
- UBB/HTML: `log_ubbFlags` equal to `html` is emitted raw, otherwise rendered as
  UBB markup.
- URL semantics: `?mode=`, `?cat=`, `?user=`, `?q=`, `?hl=`, `?date=`,
  `?selected=`, `?page=` all keep working.
- Login brake: four failures in one session and the fifth attempt onwards return
  `login_fail_ban` for three minutes — a faithful copy of the `Session("loginfail")`
  check in `lbsUser.login`, including the JScript quirk where comparing against
  an unset value yields `NaN`.

## Intentional deviations

- Deleting users refuses to remove the last administrator (the original lets you
  leave the site with nobody in charge).
- Deleting a trackback uses the same rule as articles (`delete>1` covers
  everything, `==1` only your own articles'). The original `trackbackDelete`
  required being the article author **and** `delete>=2`, so even an administrator
  could not delete a trackback on somebody else's article while the UI happily
  showed the delete icon.
- The original concatenates SQL in JScript; this port uses parameterised queries
  throughout, with equivalent behaviour.
