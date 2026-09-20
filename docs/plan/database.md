# Database

Source: the original LBS^2 `data/blog.mdb` and `data/gbook.mdb`
(Access 2000 / Jet 4).

How it was recovered: a pure-Python `access_parser` run reads the table
definition pages and pulls out each column's Jet type code, length, flags
(autonumber, nullable, Unicode compressed) and the primary key. The derived
layout is cross-checked against how the ASP code uses every field.

## Type mapping

| Jet type code | Access type | SQLite |
|---|---|---|
| 1 | Yes/No | `INTEGER` (0/1) |
| 2 | Byte | `INTEGER` |
| 3 | Integer | `INTEGER` |
| 4 | Long Integer (autonumber) | `INTEGER PRIMARY KEY AUTOINCREMENT` / `INTEGER` |
| 8 | Date/Time | `TEXT`, `YYYY-MM-DD HH:MM:SS` |
| 10 | Text(n) | `TEXT` (the length is kept in a comment; SQLite does not enforce it) |
| 12 | Memo | `TEXT` |

Text lengths: for Unicode compressed columns the character count is the
definition length divided by two — `user_password` 80 → 40, exactly the length of
a SHA1 hex digest, and `user_salt` 12 → 6, matching `randomStr(6)`. Non-compressed
columns keep their raw value.

## blog_Article

| Column | Type | Notes |
|---|---|---|
| log_id | INTEGER PRIMARY KEY AUTOINCREMENT | article id |
| log_catID | INTEGER | category id |
| log_title | TEXT(255) | title |
| log_authorID | INTEGER | author user id |
| log_author | TEXT(25) | author name snapshot |
| log_editMark | TEXT(50) | last-edit marker |
| log_trackbackURL | TEXT(255) | outbound trackback URL |
| log_content0 | TEXT | first half of the body |
| log_content1 | TEXT | second half (auto split) |
| log_mode | INTEGER | visibility 1–4 |
| log_locked | INTEGER | comments locked |
| log_selected | INTEGER | featured |
| log_ubbFlags | TEXT(100) | UBB flag string, or `html` |
| log_postTime | TEXT | post time |
| log_ip | TEXT(15) | author IP |
| log_commentCount | INTEGER | comment counter snapshot |
| log_viewCount | INTEGER | view counter |
| log_trackbackCount | INTEGER | trackback counter snapshot |

## blog_Category

| Column | Type |
|---|---|
| cat_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| cat_name | TEXT(50) |
| cat_order | INTEGER |
| cat_articleCount | INTEGER |
| cat_hidden | INTEGER |
| cat_locked | INTEGER |

## blog_Comment

| Column | Type |
|---|---|
| comm_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| log_id | INTEGER |
| comm_content | TEXT |
| comm_authorID | INTEGER |
| comm_author | TEXT(25) |
| comm_editMark | TEXT(50) |
| comm_hidden | INTEGER |
| comm_ubbFlags | TEXT(20) |
| comm_postTime | TEXT |
| comm_ip | TEXT(15) |

## blog_Settings

| Column | Type | Notes |
|---|---|---|
| set_name | TEXT(25) PRIMARY KEY | setting name |
| set_type | INTEGER | 0 numeric, 1 string |
| set_value0 | INTEGER | value when `set_type=0` |
| set_value1 | TEXT | value when `set_type=1` |

`set_name` is declared `COLLATE NOCASE`: `updateSettings` in the admin backend
addresses rows with lower case names (`blogtitle`) while the stored names are
camel case (`blogTitle`), and Jet compares strings case insensitively. Without it
SQLite would silently create a duplicate row.

## blog_Smilies

| Column | Type |
|---|---|
| sm_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| sm_image | TEXT(50) |
| sm_code | TEXT(25) |

## blog_Trackback

| Column | Type |
|---|---|
| tb_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| log_id | INTEGER |
| tb_url | TEXT(100) |
| tb_title | TEXT(100) |
| tb_blog | TEXT(100) |
| tb_excerpt | TEXT |
| tb_time | TEXT |
| tb_ip | TEXT(15) |

## blog_User

| Column | Type | Notes |
|---|---|---|
| user_id | INTEGER PRIMARY KEY AUTOINCREMENT | user id |
| user_name | TEXT(25) | login name (`COLLATE NOCASE`, see above) |
| user_password | TEXT(40) | `SHA1(password + salt)` hex; legacy rows hold MD5 |
| user_salt | TEXT(6) | random salt |
| user_groupID | INTEGER | user group |
| user_gender | INTEGER | gender |
| user_email | TEXT(50) | email |
| user_hideEmail | INTEGER | hide the email |
| user_homepage | TEXT(50) | homepage |
| user_articleCount | INTEGER | article counter |
| user_commentCount | INTEGER | comment counter |
| user_lastVisit | TEXT | last visit |
| user_ip | TEXT(15) | last IP |
| user_hashKey | TEXT(40) | auto-login hash |

## blog_UserGroup

| Column | Type | Notes |
|---|---|---|
| group_id | INTEGER PRIMARY KEY AUTOINCREMENT | 1 Admin / 2 Guest / 3 Registered / 4 Author / 5 Editor |
| group_name | TEXT(50) | group name |
| group_rights | TEXT(50) | five digits: view/post/edit/delete/upload |

Built-in rights strings: Admin `99999`, Guest `11110`, Registered `11110`,
Author `22111`, Editor `22221`.

## blog_VisitorRecord

| Column | Type |
|---|---|
| vr_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| vr_ip | TEXT(15) |
| vr_os | TEXT(20) |
| vr_browser | TEXT(30) |
| vr_time | TEXT |
| vr_referer | TEXT(250) |
| vr_target | TEXT(50) |

## blog_WordFilter

| Column | Type |
|---|---|
| wf_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| wf_mode | INTEGER (0 replace, 1 block) |
| wf_text | TEXT(50) |
| wf_replace | TEXT(50) |
| wf_regExp | INTEGER |

## Guestbook

| Column | Type |
|---|---|
| gb_id | INTEGER PRIMARY KEY AUTOINCREMENT |
| gb_username | TEXT(50) |
| gb_userID | INTEGER |
| gb_content | TEXT |
| gb_editMark | TEXT(50) |
| gb_ubbFlags | TEXT(10) |
| gb_postTime | TEXT |
| gb_replyUsername | TEXT(50) |
| gb_reply | TEXT |
| gb_replyTime | TEXT |
| gb_hidden | INTEGER |
| gb_ip | TEXT(15) |

The original kept the guestbook in its own `gbook.mdb`; the port keeps the same
table inside the single SQLite file.

## Indexes

Added from the query shapes in the original SQL (the original only indexed
primary keys):

| Table | Index | Reason |
|---|---|---|
| blog_Article | `log_postTime DESC` | index lists newest first |
| blog_Article | `log_catID` | category filter |
| blog_Article | `log_authorID` | author filter |
| blog_Comment | `log_id` | comments of one article |
| blog_Comment | `comm_postTime DESC` | recent comments |
| blog_Trackback | `log_id` | trackbacks of one article |
| Guestbook | `gb_postTime` | guestbook ordering |
| blog_VisitorRecord | `vr_time` | visitor record cleanup |

## Demo data

Every table gets at least one hello-world style row so the frontend and backend
can be exercised end to end:

- one `Default` category, one `Hello World` article, one comment, one trackback
- one Admin user (displayed as `Admin`) and the five built-in user groups
- one guestbook entry, one visitor record, one word filter, one smiley
- `blog_Settings` filled in with the 49 defaults the original ships
