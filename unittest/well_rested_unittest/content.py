import traceback
import base64
from testtools.content import (Content, content_from_file,
                               TracebackContent as traceback_content,
                               json_content, text_content, istext)
from testtools.content_type import (ContentType, JSON, UTF8_TEXT)

TRACEBACK = ContentType('text', 'x-traceback',
            {"language": "python", "charset": "utf8"})
TGZ = ContentType('application', 'x-compressed')


def unittest_traceback_content(err):
    return Content(TRACEBACK, lambda: traceback.format_exception(*err))


URL = ContentType('text', 'x-url', {'charset': 'utf8'})
def url_content(url):
    if not istext(url):
        raise TypeError(
            "url must be given text, not '%s'." % type(url).__name__
        )
    return Content(URL, lambda: [url])


# designed to work with selenium's .get_screenshot_as_base64() method.
PNG = ContentType('image', 'png')
def png_content(data):
    return Content(PNG, lambda: base64.b64decode(data))


# designed to work with html returned from selenium's .page_source attribute
HTML = ContentType('text', 'html', {'charset': 'utf8'})
def html_content(html):
    html = html.encode('utf8')
    return Content(HTML, lambda: [html])


def tgz_content(filename):
    return content_from_file(filename, TGZ)


__all__ = [
    'Content', 'ContentType', 'content_from_file',
    'traceback_content', 'text_content', 'png_content',
    'json_content', 'url_content', 'unittest_traceback_content',
    'html_content', 'tgz_content',
    'URL', 'JSON', 'UTF8_TEXT', 'TRACEBACK', 'PNG', 'HTML', 'TGZ',
]
