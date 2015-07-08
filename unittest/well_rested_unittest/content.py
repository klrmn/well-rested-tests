import traceback
import base64
from testtools.content import (Content, content_from_file,
                               TracebackContent as traceback_content,
                               json_content, text_content, istext)
from testtools.content_type import (ContentType, JSON, UTF8_TEXT)

URL = ContentType('text', 'x-url')
TRACEBACK = ContentType('text', 'x-traceback',
            {"language": "python", "charset": "utf8"})
PNG = ContentType('image', 'png')
HTML = ContentType('text', 'html')
TGZ = ContentType('application', 'x-compressed')


def unittest_traceback_content(err):
    return Content(TRACEBACK, lambda: traceback.format_exception(*err))


def url_content(url):
    if not istext(url):
        raise TypeError(
            "url must be given text, not '%s'." % type(url).__name__
        )
    return Content(URL, lambda: url)


def png_content(data):
    return Content(PNG, lambda: base64.b64decode(data))


def html_content(html):
    return Content(HTML, lambda: html)


def tgz_content(filename):
    return content_from_file(filename, TGZ)


__all__ = [
    'Content', 'ContentType', 'content_from_file',
    'traceback_content', 'text_content', 'png_content',
    'json_content', 'url_content', 'unittest_traceback_content',
    'html_content', 'tgz_content',
    'URL', 'JSON', 'UTF8_TEXT', 'TRACEBACK', 'PNG', 'HTML', 'TGZ',
]
