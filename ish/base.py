import shlex
import argparse

import requests
from bs4 import BeautifulSoup


class Web(object):
    def __init__(self, url, args={}, method='GET'):
        self.req = requests.request(method, url, params=args)

    def getBody(self):
        return BeautifulSoup(self.req.text, 'html.parser')

class ArgParse(argparse.ArgumentParser):
    def _print_message(self, message, file=None):
        self.stdout.write(message)

class Command(object):
    def __init__(self, shell):
        self.shell = shell
        self.session = shell.session

    def parseargs(self, arg, doc={}, description="", name=""):
        # Example doc:
        parser = ArgParse(description=description, prog=name)
        parser.stdout = self.shell.stdout
        for k, v in doc:
            parser.add_argument(*k, **v)

        options = self.shell._lex_split(arg)
        return parser.parse_args(options)

    def println(self, s):
        self.shell.stdout.write(str(s)+'\n')
