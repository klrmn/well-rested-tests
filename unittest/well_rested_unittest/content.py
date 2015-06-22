from testtools.content import (Content, content_from_file,
                               TracebackContent as traceback_content,
                               json_content, text_content, istext)
from testtools.content_type import (ContentType, JSON, UTF8_TEXT)

URL = ContentType('text', 'x-url')


def url_content(url):
    if not istext(url):
        raise TypeError(
            "url must be given text, not '%s'." % type(url).__name__
        )
    return Content(URL, lambda: url)


__all__ = [
    Content, ContentType, content_from_file,
    traceback_content, text_content,
    json_content, url_content,
    URL, JSON, UTF8_TEXT
]
