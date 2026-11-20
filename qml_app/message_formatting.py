"""Small, local rich-text editor adapter; no remote resources or active HTML."""
from html import escape
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QTextListFormat, QFont, QColor, QGuiApplication


class _SafeHTML(HTMLParser):
    tags = {'p', 'br', 'b', 'strong', 'i', 'em', 'u', 's', 'span', 'div', 'ul', 'ol',
            'li', 'a', 'blockquote', 'table', 'tbody', 'tr', 'td', 'th', 'hr'}
    styles = {'font-family', 'font-size', 'font-weight', 'font-style', 'text-decoration',
              'color', 'background-color', 'text-align', 'margin-left', 'margin-top', 'margin-bottom'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'head', 'iframe', 'object'}:
            self.hidden += 1
            return
        if self.hidden or tag not in self.tags: return
        safe = []
        for key, value in attrs:
            value = value or ''
            if key == 'style':
                declarations = []
                for entry in value.split(';'):
                    name, _, content = entry.partition(':')
                    if name.strip().lower() in self.styles and re.fullmatch(r"[\w\s#.,%()'\"-]{1,160}", content.strip()) and not re.search(r'url|expression|import', content, re.I):
                        declarations.append(name.strip().lower()+':'+content.strip())
                if declarations: safe.append(('style', ';'.join(declarations)))
            elif tag == 'a' and key == 'href' and urlsplit(value).scheme.lower() in {'https', 'http', 'mailto'}:
                safe.append((key, value))
            elif key in {'colspan', 'rowspan'} and value.isdigit() and 1 <= int(value) <= 20:
                safe.append((key, value))
        self.output.append('<'+tag+''.join(' '+k+'="'+escape(v, quote=True)+'"' for k, v in safe)+'>')

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'head', 'iframe', 'object'}:
            self.hidden = max(0, self.hidden-1)
        elif not self.hidden and tag in self.tags and tag not in {'br', 'hr'}:
            self.output.append('</'+tag+'>')

    def handle_data(self, data):
        if not self.hidden: self.output.append(escape(data))


def safe_html(value):
    if not isinstance(value, str) or len(value) > 500_000 or '\x00' in value:
        raise ValueError('Formatted message is too large or invalid.')
    parser = _SafeHTML()
    parser.feed(value)
    parser.close()
    return ''.join(parser.output)


class MessageFormatting(QObject):
    @Slot(result=str)
    def clipboardHtml(self):
        mime = QGuiApplication.clipboard().mimeData()
        if mime is None: return ''
        try:
            return safe_html(mime.html()) if mime.hasHtml() else escape(mime.text()).replace('\n', '<br>')
        except ValueError:
            return escape(mime.text()[:100_000]).replace('\n', '<br>')

    @Slot(QObject, int, int, str, str)
    def apply(self, quick_document, start, end, action, value=''):
        if quick_document is None: return
        doc = quick_document.textDocument()
        cursor = QTextCursor(doc)
        cursor.setPosition(max(0, min(start, doc.characterCount()-1)))
        cursor.setPosition(max(0, min(end, doc.characterCount()-1)), QTextCursor.KeepAnchor)
        fmt = QTextCharFormat()
        if action == 'bold': fmt.setFontWeight(QFont.Normal if cursor.charFormat().fontWeight() >= QFont.Bold else QFont.Bold)
        elif action == 'italic': fmt.setFontItalic(not cursor.charFormat().fontItalic())
        elif action == 'underline': fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        elif action == 'font': fmt.setFontFamilies([value[:80]])
        elif action == 'size': fmt.setFontPointSize(max(8, min(48, float(value))))
        elif action == 'color' and QColor(value).isValid(): fmt.setForeground(QColor(value))
        elif action == 'link':
            if urlsplit(value).scheme.lower() not in {'http', 'https', 'mailto'}: return
            fmt.setAnchor(True); fmt.setAnchorHref(value); fmt.setFontUnderline(True)
            fmt.setForeground(QColor('#2674aa'))
        elif action == 'unlink': fmt.setAnchor(False); fmt.setAnchorHref(''); fmt.setFontUnderline(False)
        elif action in {'left', 'center', 'right', 'justify'}:
            block = cursor.blockFormat()
            block.setAlignment({'left': Qt.AlignLeft, 'center': Qt.AlignHCenter, 'right': Qt.AlignRight, 'justify': Qt.AlignJustify}[action])
            cursor.mergeBlockFormat(block); return
        elif action in {'bullets', 'numbers'}:
            style = QTextListFormat(); style.setStyle(QTextListFormat.ListDisc if action == 'bullets' else QTextListFormat.ListDecimal)
            cursor.createList(style); return
        elif action in {'indent', 'outdent'}:
            block = cursor.blockFormat(); block.setIndent(max(0, min(8, block.indent()+(1 if action == 'indent' else -1))))
            cursor.setBlockFormat(block); return
        elif action == 'table': cursor.insertTable(2, 2); return
        elif action == 'clear': cursor.setCharFormat(QTextCharFormat()); return
        else: return
        if not cursor.hasSelection(): cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
