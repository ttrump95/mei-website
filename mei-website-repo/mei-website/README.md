# Miller Engineering website

A self-contained static website that builds itself from simple data files.
Add a project or a person through a form, and the card, the map marker, the
project page, and the team grid all update automatically.

## How it fits together

```
content/projects/*.json   ← one file per project   (edited via /admin)
content/team/*.json        ← one file per person     (edited via /admin)
templates/                 ← the page design (rarely touched)
static/assets/             ← logo; static/uploads/ ← photos from the forms
build.py                   ← reads content/ + templates/ → writes _site/
admin/                     ← the Decap CMS form editor (lives at /admin)
netlify.toml               ← tells Netlify to run build.py and publish _site/
```

Everything the public sees is generated into `_site/` by `build.py`.
You never edit `_site/` by hand.

## Editing content

**The easy way — the form editor:** go to `https://millereng.net/admin`,
log in with GitHub, and use the **Projects** and **People** collections.
Fill the form, click Publish. About a minute later it's live.

**The direct way:** edit a file in `content/projects/` or `content/team/`
(they're plain JSON), commit, and Netlify rebuilds automatically.

## Building locally (optional)

```
python3 build.py      # writes the finished site to _site/
```
Then open `_site/index.html` in a browser. No dependencies — standard library only.

## Setup

See **MEI_GitHub_Netlify_Setup.pdf** for the one-time steps: create the GitHub
repo, connect Netlify, turn on the /admin login, and point millereng.net at it.
