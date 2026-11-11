"""Read-only descriptions of validated, account-owned cached files."""
from pathlib import Path
import re
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImageReader
from .school_services import MAX_DOWNLOAD_BYTES

LOCAL_APPLICATIONS = {'.doc','.docx','.xls','.xlsx','.ppt','.pptx','.odt','.ods','.odp','.rtf','.zip','.7z','.rar','.tar','.gz',
                      '.mp4','.webm','.mkv','.mov','.avi','.mp3','.wav','.m4a','.flac','.ogg'}
TEXT_FILES = {'.txt','.csv','.md','.log'}


def describe(path, name):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_DOWNLOAD_BYTES:
        raise ValueError('The saved file is unavailable or too large')
    with path.open('rb') as file:
        prefix = file.read(512)
        signature = prefix.lstrip(b'\xef\xbb\xbf \t\r\n')
        if signature.startswith((b'MZ',b'#!')):
            raise ValueError('This is not a supported document')
        info = dict(title=str(name)[:255], url=QUrl.fromLocalFile(str(path.resolve())), text='', truncated=False)
        if signature.startswith(b'%PDF-'):
            return dict(info, kind='pdf')
        reader = QImageReader(str(path))
        reader.setDecideFormatFromContent(True)
        if bytes(reader.format()).lower() in (b'png',b'jpg',b'jpeg',b'gif',b'bmp',b'webp',b'tiff'):
            size = reader.size()
            if size.width() <= 0 or size.height() <= 0 or size.width()*size.height() > 100_000_000:
                raise ValueError('This image is too large to preview')
            return dict(info, kind='image')
        suffix = path.suffix.lower()
        if suffix in TEXT_FILES:
            file.seek(0);body=file.read(256*1024+1);truncated=len(body)>256*1024;body=body[:256*1024]
            encoding = 'utf-16' if body.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
            text = body.decode(encoding, errors='replace')
            if '\x00' in text: raise ValueError('This file is not plain text')
            return dict(info, kind='text', text=text, truncated=truncated)
        if suffix in LOCAL_APPLICATIONS:
            if re.match(br'(?:<!doctype\s+html|<html|<script)',signature,re.I):
                raise ValueError('The saved file is a web page, not the requested document')
            return dict(info, kind='external')
        raise ValueError('This file type cannot be previewed or opened safely. Use Save as for the original file.')
