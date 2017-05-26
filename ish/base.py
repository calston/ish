import requests

from bs4 import BeautifulSoup


class Web(object):
    def __init__(self, url, args={}, method='GET'):
        self.req = requests.request(method, url, params=args)

    def getBody(self):
        return BeautifulSoup(self.req.text, 'html.parser')


class Command(object):
    def __init__(self, shell):
        self.shell = shell

    def println(self, s):
        self.shell.stdout.write(str(s)+'\n')
