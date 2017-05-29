import os
import requests

import urlparse
import argparse

from colored import fg, bg, attr

from bs4 import BeautifulSoup

from ish.base import Command

class Module(Command):
    def __init__(self, *a):
        self.soup = None
        self.request = None
        self.lastmap = {}

        Command.__init__(self, *a)

    def do_soup(self, arg):
        """Returns the body of the last request"""
        if not self.soup:
            self.println('No soup for you!')
        else:
            self.println(str(self.soup))

    def do_env(self, arg):
        for k, v in self.shell.env.items():
            self.println('%s=%s' % (k, repr(v)))

    def do_request(self, arg):
        """Make HTTP requests"""
        args = self.parseargs(
            arg,
            name='req',
            description="A function for performing HTTP requests",
            doc=[
                [
                    ('-m', '--method'),
                    {
                        'type': str,
                        'default': 'GET',
                        'help': "HTTP request method (GET, PUT, POST, HEAD, etc)",
                    }
                ],
                [
                    ('-v', '--verbose'),
                    {'action': 'count', 'help': 'Verbose'}
                ],
                [
                    ('-t', '--timeout'),
                    {
                        'type': int,
                        'default': 5,
                        'help': 'request timeout'
                    }
                ],
                [
                    ('url',),
                    {'metavar': 'url', 'type': str, 'help': 'Request URL'}
                ]
            ]
        )

        try:
            req = requests.request(args.method, args.url, timeout=args.timeout)
            if args.verbose:
                self.println("Status: %s" % req.status_code)
                self.println("Headers: %s" % repr(req.headers))
                self.println("Body: %s" % req.text)

        except Exception, e:
            self.println(e)

    def do_json(self, arg):
        """Make json requests"""
        options = self.shell._lex_split(arg)

        parser = argparse.ArgumentParser(
                    description="A function for handling JSON requests")

        parser.add_argument('url', metavar='u', type=str,
                            help="A url to request")

        import json

    def do_cd(self, arg):
        "Traverse the intertubes"

        cwd = self.shell.getEnv('cwd', '/')

        self.shell.setEnv('secure', False)

        if arg == '..':
            try:
                arg = cwd.rstrip('/').rsplit('/', 1)[0]
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
            if arg.startswith('/') or '://' in arg:
                d = arg
            else:
                d = os.path.join(cwd, arg)

        self.soup = None
        if d != '/':
            if not '://' in d:
                try:
                    r = self.session.get('https:/' + d, timeout=5, headers={'user-agent': 'Interpipe Shell/0.0.1'})
                    self.shell.setEnv('secure', True)
                except Exception, e:
                    r = None
                    self.shell.setEnv('secure', False)

                if r is None:
                    # Try standard HTTP
                    try:
                        r = self.session.get('http:/' + d, timeout=5, headers={'user-agent': 'Interpipe Shell/0.0.1'})
                    except Exception, e:
                        self.println("Error connecting to " + d + str(e))
                        r = None
            else:
                try:
                    r = self.session.get(d, timeout=5, headers={'user-agent': 'Interpipe Shell/0.0.1'})
                    self.shell.setEnv('secure', d.startswith('https'))
                    p = urlparse.urlparse(d)
                    d = "/%s%s" % (p.netloc, p.path)
                except Exception, e:
                    r = None
                    self.shell.setEnv('secure', False)

            if r is not None:
                if r.history:
                    last = r.history[0]
                    if last.is_redirect:
                        loc = last.headers.get('Location', d+'??')
                        lp = urlparse.urlparse(loc)
                        d = '/%s%s' % (lp.netloc, lp.path)

                if r.status_code == 404:
                    self.println(' %s: No such location [404]' % d)

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
            name = link.text.strip().strip('/').encode('ascii', 'ignore')
            dr[url] = name
            m[name] = url

        self.lastmap = m
        return dr

    def do_ls(self, args):
        self._get_links()

        results = [' %s/' % i for i, a in self.lastmap.items()]

        results.sort()

        for i in results:
            self.println(i.encode('utf-8', 'replace'))

        if (not results) and self.soup:
            self.println(self.soup)

    def do_echo(self, args):
        """Echo arguments to stdout"""
        self.println(args)

    def do_cat(self, args):
        """Redireccts stdin to stdout
        """
        self.shell.stdout.write(self.shell.stdin.read())

    def do_e(self, args):
        """Run an application
        """
        if args:
            return self.shell.execute(args)
        else:
            self.println('Command required')

    def do_grep(self, args):
        return self.shell.execute('grep ' + args)

