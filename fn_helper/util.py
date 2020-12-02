import re
import os.path
from urllib.parse import urlparse


def remove_prefix(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):]
    return text


def id_from_uri(resource):
    """ Extract id from uri, refer to:
        https://developer.spotify.com/documentation/web-api/#spotify-uris-and-ids
    """
    return resource.split(':')[-1]


def id_from_url(url):
    return os.path.split(urlparse(url).path)[1]


def is_uri(resource):
    """ Check resource is in uri format.
    """
    return bool(re.match(r"^(\w+):(\w+):([0-9a-zA-Z])+$", resource))


def chunk_gen(seq, size=100):
    for pos in range(0, len(seq), size):
        yield(seq[pos:pos + size])


class ElementIterator:
    n = 0
    current_element = None
    elements = []

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.current_element = self.elements[self.n]
        except IndexError:
            raise StopIteration()
        else:
            self.n += 1
        return self.current_element

    @property
    def checkpoint(self):
        return str(self.current_element)

    def move_to_checkpoint(self, checkpoint):
        if not checkpoint:
            return
        while self.checkpoint != checkpoint:
            next(self)
