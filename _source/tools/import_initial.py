"""One-off import: builds the first version of the page sources (_source/pages/*.md)
from the old Weebly site (webpage/original) and the English CV.
After this first run, edit the .md files directly; this script is not needed again."""
import json, re, os, sys, shutil, html
import docx
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # .../site
ORIG = os.path.join(os.path.dirname(ROOT), 'original')
CV = r'D:/ClaudeProjects/currivulum_vitae/CV_English_long_2026_09_30.docx'
PAGES = os.path.join(ROOT, '_source', 'pages'); os.makedirs(PAGES, exist_ok=True)
FILES = os.path.join(ROOT, 'files'); os.makedirs(FILES, exist_ok=True)

chunks = json.load(open(os.path.join(ORIG, 'chunks.json'), encoding='utf-8'))

def md(c):
    """old-site chunk -> markdown"""
    def link(m):
        url, label = m.group(1), m.group(2).strip()
        if url.startswith('/uploads/'):
            url = 'files/' + os.path.basename(html.unescape(url))
        return '[%s](%s)' % (label or 'link', url)
    c = re.sub(r'\[\[A\|([^|]*)\|([^\]]*)\]\]', link, c)
    c = c.replace('** **', ' ').replace('****', '').replace('**:**', ':')
    c = re.sub(r'\*\*\s+', '**', c); c = re.sub(r'\s+\*\*(?=[,.;:)])', '**', c)
    return c.strip()

def between(page, start, stop=None):
    ch = chunks[page]; out = []; on = False
    for c in ch:
        if start in c: on = True; continue
        if on and (c.startswith('Powered by') or (stop and stop in c)): break
        if on: out.append(c)
    return out

# ---------- copy files ----------
for f in os.listdir(os.path.join(ORIG, 'uploads')):
    shutil.copy2(os.path.join(ORIG, 'uploads', f), os.path.join(FILES, f))

# ---------- CV text ----------
d = docx.Document(CV)
def vis(p):
    out = []
    for el in p.iter():
        if el.tag == qn('w:t') and not any(a.tag == qn('w:del') for a in el.iterancestors()): out.append(el.text or '')
        elif el.tag == qn('w:tab') and el.getparent().tag == qn('w:r'): out.append('\t')
    return ''.join(out)
ptx = [vis(p) for p in d.element.body.iter(qn('w:p'))]
def section(head, nxt):
    a = [i for i, t in enumerate(ptx) if t.strip().startswith(head)][0]
    b = [i for i, t in enumerate(ptx) if i > a and t.strip().startswith(nxt)][0]
    return [t for t in ptx[a + 1:b] if t.strip()]

# ---------- publications ----------
pub = ['# Publications', '']
heads = {'***Journal articles***': 'Journal articles', '***Books***': 'Books',
         '***Chapters in edited volumes***': 'Chapters in edited volumes', '***Other***': 'Other publications and reports'}
for c in between('publications', 'Media and blogs'):
    if c in heads:
        pub += ['', '## ' + heads[c], '']; continue
    if c.startswith('*Media coverage'):
        pub.append('  ' + md(c)); continue
    pub.append('- ' + md(c))
# items in the CV but not on the old site
pub_add = ['- Ayllón, S.; Ramos, X. (2025). \u2018Poverty in Catalonia: Evolution and composition from the financial crisis\u2019 <!-- TODO: complete reference from CV -->',
           '- Ayllón, S. (2005). \u2018How is income shared among households with young people? Implications for the analysis of youth poverty\u2019 <!-- TODO: complete reference from CV -->']
cv_other = section('Other publications and invited contributions', 'WORKING PAPERS')
for t in cv_other:
    t = re.sub(r'^\[\d+\.\]\s*', '', t.strip())
    if t.startswith('Ayllón, S.; Ramos, X. (2025)'): pub_add[0] = '- ' + t
    if t.startswith('Ayllón, S. (2005). ‘How is income shared'): pub_add[1] = '- ' + t
i = pub.index('## Other publications and reports') + 2
# insert 2025 item after the 2025 items, 2005 at the end
pos25 = max(k for k, t in enumerate(pub) if '(2025)' in t) + 1
pub.insert(pos25, pub_add[0]); pub.append(pub_add[1])
open(os.path.join(PAGES, 'publications.md'), 'w', encoding='utf-8').write('\n'.join(pub) + '\n')

# ---------- working papers ----------
wp = ['# Working papers', ''] + ['- ' + md(c) for c in between('working-papers', 'Media and blogs')]
open(os.path.join(PAGES, 'working-papers.md'), 'w', encoding='utf-8').write('\n'.join(wp) + '\n')

# ---------- projects & contracts (from the corrected CV) ----------
def dated(lines):
    out = []
    for t in lines:
        t = t.strip().replace('\t', ' ')
        m = re.match(r'^(\d{4}\s*[–-]\s*\d{4})\s*:\s*(.*)$', t)
        out.append('- **%s:** %s' % (m.group(1).replace(' ', ''), m.group(2).strip()) if m else '- ' + t)
    return out
proj = section('PARTICIPATION IN RESEARCH PROJECTS', 'RESEARCH CONTRACTS')
cont = section('RESEARCH CONTRACTS AND COMMISSIONED RESEARCH', 'RESEARCH VISITS')
pj = ['# Research projects', '', '*Budgets are shown only for projects I lead, when the amount is 50,000 euros or more.*', ''] + dated(proj)
pj += ['', '## Research contracts and commissioned research', ''] + dated(cont)
open(os.path.join(PAGES, 'projects.md'), 'w', encoding='utf-8').write('\n'.join(pj) + '\n')

# ---------- talks (from the CV) ----------
conf = section('PRESENTATIONS IN INTERNATIONAL CONFERENCES/WORKSHOPS', 'INVITED SEMINARS')
sem = section('INVITED SEMINARS', 'WORKSHOP, MEETINGS AND SEMINAR ORGANIZATION')
tk = ['# Talks', '', '## Conferences and workshops', '']
year = None
for t in conf:
    t = t.strip()
    m = re.match(r'^(\d{4})\s*\t?\s*(.*)$', t)
    if m and not t.startswith('['): year, t = m.group(1), m.group(2).strip()
    if m and t.startswith('['): pass
    if re.match(r'^\d{4}', t): year, t = t[:4], t[4:].strip()
    t = t.lstrip('\t ')
    m2 = re.match(r'^\[(\d+)\.\]\s*(.*)$', t)
    num, body = (m2.group(1), m2.group(2)) if m2 else ('', t)
    if year and (not tk[-1].startswith('### ' + year)) and not any(x == '### ' + year for x in tk):
        tk += ['', '### ' + year, '']
    tk.append('- [%s.] %s' % (num, body) if num else '- ' + body)
tk += ['', '## Invited seminars', '']
for t in sem:
    m2 = re.match(r'^\[(\d+)\.\]\s*(.*)$', t.strip())
    tk.append('- [%s.] %s' % (m2.group(1), m2.group(2)) if m2 else '- ' + t.strip())
open(os.path.join(PAGES, 'talks.md'), 'w', encoding='utf-8').write('\n'.join(tk) + '\n')

# ---------- media and blogs ----------
mb = ['# Media and blogs', '', '## Media (a selection of recent appearances)', '']
blog = False
for c in between('media-and-blogs', 'Media and blogs'):
    if 'Media (a selection' in c: continue
    if 'Blog posts' in c:
        mb += ['', '## Blog posts', '']; blog = True; continue
    mb.append('- ' + md(c))
mb.append('- 10/2009: \u2018Pobreza juvenil y familia en España\u2019, Divulga UAB (in Spanish). [link](https://www.uab.cat/web/detalle-noticia/pobreza-juvenil-y-familia-en-espana-1345680342040.html?articleId=1255415637196)')
open(os.path.join(PAGES, 'media.md'), 'w', encoding='utf-8').write('\n'.join(mb) + '\n')

# ---------- about / news (old site) ----------
news = [md(c) for c in chunks['index'] if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}:', c)]
json.dump({'news': news}, open(os.path.join(ROOT, '_source', 'tools', 'old_news.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pages written:', sorted(os.listdir(PAGES)))
print('talk lines:', sum(1 for t in tk if t.startswith('- ')), '| projects:', len(proj), '| contracts:', len(cont), '| news:', len(news))
