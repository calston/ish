import shlex
import argparse
from StringIO import StringIO

import requests
from bs4 import BeautifulSoup

import colored


class Web(object):
    def __init__(self, url, args={}, method='GET'):
        self.req = requests.request(method, url, params=args)

    def getBody(self):
        return BeautifulSoup(self.req.text, 'html.parser')

class ArgParse(argparse.ArgumentParser):
    def _print_message(self, message, file=None):
        self.stdout.write(message)

    def exit(self, status=0, message=None):
        if message:
            self.stdout.write(message)

    def error(self, message):
        self.print_usage()

class Command(object):
    def __init__(self, shell):
        self.shell = shell
        self.session = shell.session

    def parseargs(self, arg, doc={}, description="", name=""):
        parser = ArgParse(description=description, prog=name)
        parser.stdout = self.shell.stdout
        for k, v in doc:
            parser.add_argument(*k, **v)

        options = self.shell._lex_split(arg)
        return parser.parse_args(options)

    def println(self, s):
        self.shell.stdout.write(str(s)+'\n')

def renderImage(content):
    import img2txt
    import ansi

    img = img2txt.load_and_resize_image(
        StringIO(content),
        True,
        40,
        1.0
    )
    pixel = img.load()
    width, height = img.size

    fill_string = "\x1b[49m\x1b[K"

    text = ansi.generate_ANSI_from_pixels(pixel, width, height, None)[0]

    return fill_string + text + colored.attr(0)
    
