"""Recover public instruction groups without rendering school HTML in the UI."""
import re
from bs4 import BeautifulSoup
from planner_details import html_to_text


def _text_sections(body, headings=()):
    sections, title, lines = [], 'Instructions', []
    for line in body.splitlines():
        label = line.strip()
        heading = (len(label) <= 80 and label.endswith(':') and not label.startswith(('•', '-', '*'))
                   or label in headings or label.casefold() == 'individually/pair/group')
        if heading:
            if lines or title != 'Instructions':
                sections.append(dict(title=title, body='\n'.join(lines).strip()))
            title, lines = label.rstrip(':').strip(), []
        else:
            lines.append(line)
    if lines or title != 'Instructions':
        sections.append(dict(title=title, body='\n'.join(lines).strip()))
    return [s for s in sections if s['body'] or s['title'] != 'Instructions']


def instruction_sections(item):
    body = html_to_text(str(item.get('body') or ''))
    if not body:
        return [dict(title='Instructions', body='No additional instructions.')]
    source = str(item.get('body') or '')
    # Cached public markup must describe this exact body, never another record or private field.
    for field in item.get('detail_fields') or []:
        if (isinstance(field, (list, tuple)) and len(field) == 2
                and field[0] in ('detail.publicInfo', 'detail.info') and isinstance(field[1], str)
                and html_to_text(field[1]) == body):
            source = field[1]
            break
    soup = BeautifulSoup(source, 'html.parser')
    tables = soup.find_all('table')
    if (tables and not any(t.find('table') for t in tables)
            and html_to_text(''.join(str(t) for t in tables)) == body):
        sections = []
        for row in soup.find_all('tr'):
            cells = [html_to_text(str(cell)) for cell in row.find_all(['td', 'th'], recursive=False)]
            content = '\n\n'.join(c for c in cells if c)
            if not content:
                continue
            heading = row.find(['b', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            title = html_to_text(str(heading)) if heading else ''
            if title and len(title) <= 80 and content.startswith(title):
                sections.append(dict(title=title.rstrip(':').strip(), body=content[len(title):].strip(' :\n')))
            else:
                sections.extend(_text_sections(content))
        if sections:
            return sections
    headings = [html_to_text(str(h)) for h in soup.find_all(re.compile(r'^h[1-6]$'))]
    return _text_sections(body, headings) or [dict(title='Instructions', body=body)]
