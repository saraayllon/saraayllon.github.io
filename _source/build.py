"""Builds the website: turns _source/pages/*.md into the .html files at the top of the repository.

Usage (from the repository folder):   python _source/build.py
Then check the pages in a browser, and commit + push to publish.

Markdown supported: '# ', '## ', '### ' headings; '- ' list items (lines starting with two spaces
continue the item above); blank line = new paragraph; **bold**, *italic*, [text](url); lines starting
with '<' are copied as raw HTML; <!-- comments --> are removed.
"""
import os, re, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGES = os.path.join(HERE, 'pages')

NAV = [('index', 'Home'), ('publications', 'Publications'), ('working-papers', 'Working papers'),
       ('projects', 'Projects'), ('talks', 'Talks'), ('media', 'Media and blogs')]
SITE = 'Sara Ayllón Gatnau'
PROFILES = [('Google Scholar', 'https://scholar.google.com/citations?user=O_1DEpYAAAAJ'),
            ('ORCID', 'https://orcid.org/0000-0002-3338-1183'), ('RePEc', 'https://ideas.repec.org/e/pay16.html'),
            ('IZA', 'https://www.iza.org/people/fellows/5118/sara-ayllon'), ('NBER', 'https://www.nber.org/people/sara_ayllon'),
            ('Bluesky', 'https://bsky.app/profile/ayllonsara.bsky.social')]
CV_PDF = 'files/cv_english_long_2026_09_30.pdf'
LINKS = ''.join('<a href="%s">%s</a>' % (u, n) for n, u in PROFILES) + '<a class="cv" href="%s">CV (pdf)</a>' % CV_PDF


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\[\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)', lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    return t


def render(md):
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    out, para, items, cur = [], [], None, None

    def flush_para():
        nonlocal para
        if para:
            out.append('<p>%s</p>' % inline(' '.join(para)))
            para = []

    def flush_list():
        nonlocal items, cur
        if cur is not None:
            items.append(cur); cur = None
        if items is not None:
            out.append('<ul>\n%s\n</ul>' % '\n'.join('<li>%s</li>' % inline(i) for i in items))
            items = None

    for line in md.split('\n'):
        s = line.rstrip()
        if not s.strip():
            flush_para()
            if cur is not None: items.append(cur); cur = None
            continue
        if s.startswith('- '):
            flush_para()
            if items is None: items = []
            if cur is not None: items.append(cur)
            cur = s[2:].strip(); continue
        if s.startswith('  ') and cur is not None:
            cur += '<br>' + s.strip() if s.strip().startswith('*Media') else ' ' + s.strip()
            continue
        flush_list()
        if s.startswith('<'):
            flush_para(); out.append(s); continue
        m = re.match(r'^(#{1,3}) (.*)$', s)
        if m:
            flush_para()
            n = len(m.group(1)); txt = m.group(2).strip()
            anchor = re.sub(r'[^a-z0-9]+', '-', txt.lower()).strip('-')
            out.append('<h%d id="%s">%s</h%d>' % (n, anchor, inline(txt), n)); continue
        para.append(s.strip())
    flush_para(); flush_list()
    return '\n'.join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Sara Ayllón Gatnau, economist at the Universitat de Girona: poverty, inequality, family and labour economics.">
<link rel="stylesheet" href="style.css">
</head>
<body class="page-{slug}">
<div class="topbar"><div class="wrap">{links}</div></div>
<header class="menubar"><div class="wrap">
  <a class="name" href="index.html">Sara Ayllón Gatnau</a>
  <nav>{nav}</nav>
</div></header>
{hero}
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">Sara Ayllón Gatnau · Universitat de Girona · Last updated {date}</div></footer>
</body>
</html>
"""


def build():
    date = datetime.date.today().strftime('%-d %B %Y') if os.name != 'nt' else datetime.date.today().strftime('%#d %B %Y')
    for slug, label in NAV:
        md = open(os.path.join(PAGES, slug + '.md'), encoding='utf-8').read()
        nav = ''.join('<a href="%s.html"%s>%s</a>' % (s, ' class="here"' if s == slug else '', l) for s, l in NAV)
        title = SITE if slug == 'index' else '%s – %s' % (label, SITE)
        if slug == 'index':
            hero = ('<section class="banner"><div class="wrap"><div class="bname">Sara Ayllón Gatnau</div>'
                    '<div class="credit">Picture by Massimiliano Minocri – El País</div></div></section>')
        else:
            hero = '<section class="pagehead"><div class="wrap"><h1>%s</h1></div></section>' % label
        page = TEMPLATE.format(title=title, slug=slug, nav=nav, body=render(md), date=date, hero=hero, links=LINKS)
        open(os.path.join(ROOT, slug + '.html'), 'w', encoding='utf-8', newline='\n').write(page)
        print('built', slug + '.html')
    open(os.path.join(ROOT, '.nojekyll'), 'w').close()


if __name__ == '__main__':
    build()
