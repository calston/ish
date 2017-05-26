import os
import requests

import urlparse

from colored import fg, bg, attr

from bs4 import BeautifulSoup

from ish.base import Command

class Module(Command):
    def __init__(self, *a):
        self.soup = None
        self.lastmap = {}

        Command.__init__(self, *a)

    def do_soup(self, arg):
        """Returns the body of the last request"""
        if not self.soup:
            self.println('No soup for you!')
        else:
            self.println(str(self.soup))

    def do_json(self, arg):
        """Make json requests"""
        self.println(self.stdin)

    def do_cd(self, arg):
        "Traverse the intertubes"

        cwd = self.shell.env.get('cwd', '/')

        if arg == '..':
            try:
                arg = cwd.rtrip('/').rsplit('/', 1)[0]
            except:
                arg = '/'

        if arg in self.lastmap:
            loc = self.lastmap[arg]

            if '//' in loc:
                p = urlparse.urlparse(loc)
                arg = os.path.join('/', p.netloc, p.path.lstrip('/'))

            elif loc.startswith('/'):
                r = cwd.strip('/').split('/')[0]
                arg = os.path.join('/', r, loc.lstrip('/'))
            else:
                arg = os.path.join(cwd, loc)

        self.lastmap = {}

        if not arg:
            d = '/'

        else:
            if arg.startswith('/'):
                d = arg
            else:
                d = os.path.join(cwd, arg)

        self.soup = None
        if d != '/':
            try:
                r = requests.get('https:/' + d, timeout=5, headers={'user-agent': 'Interpipe Shell/0.0.1'})
            except Exception, e:
                r = None
                self.shell.secure = False

            if r is None:
                # Try standard HTTP
                try:
                    r = requests.get('http:/' + d, timeout=5, headers={'user-agent': 'Interpipe Shell/0.0.1'})
                except Exception, e:
                    self.shell.stdout.write("Error connecting to " + d +str(e) +'\n')
                    r = None

            if r is not None:
                if r.history:
                    last = r.history[0]
                    if last.is_redirect:
                        loc = last.headers.get('Location', d+'??')
                        lp = urlparse.urlparse(loc)
                        d = '/%s%s' % (lp.netloc, lp.path)

                if r.status_code == 404:
                    self.shell.stdout.write(' %s: No such location [404]\n' % d)

                if r.ok:
                    self.soup = BeautifulSoup(r.text, 'html.parser')
                    self.request = r
                    self._get_links()
                else:
                    d = cwd

            else:
                d = cwd

        self.shell.setEnv('cwd', d)

    def _get_links(self):
        self.lastmap = {}
        if not self.soup:
            return {}

        links = self.soup.find_all('a')
        dr = {}
        m = {}
        for link in links:
            url = link.get('href', '#')

            dr[url] = link.text
            m[link.text] = url

        self.lastmap = m
        return dr

    def do_ls(self, args):
        self._get_links()

        results = [' %s/' % i for i, a in self.lastmap.items()]
        results.sort()

        for i in results:
            self.shell.stdout.write(i +'\n')

    def do_echo(self, args):
        """Echo arguments to stdout"""
        self.stdout.write(args + '\n')

    def do_cat(self, args):
        """Redireccts stdin to stdout
        """
        self.stdout.write(self.stdin.read())

    def do_e(self, args):
        """Run an application
        """
        if args:
            return self.shell.execute(args)
        else:
            self.stdout.write('Command required\n')

    def do_grep(self, args):
        return self.shell.execute('grep ' + args)

