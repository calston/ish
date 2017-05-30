import requests
import textwrap

import urlparse

from colored import fg, bg, attr

from bs4 import BeautifulSoup

from ish.base import Command

class Module(Command):
    def do_google(self, arg):
        "Google the intertubes"

        r = self.session.get('https://www.google.co.za/search', params={'q': arg})

        b = BeautifulSoup(r.text, 'html.parser')

        results = b.body.find_all('div', id='ires')[0].find_all('div', class_='g')
        for result in results:
            try:
                title = result.h3.a.text
                if title.startswith('News for '):
                    continue
                link = urlparse.urlparse(result.h3.a['href'])
                url = urlparse.parse_qs(link.query).get('q', [''])[0]

                self.shell.stdout.write('%s%s %s[%s%s%s]%s\n' % (
                    fg(10), title, fg(11), fg(1), url, fg(11), attr(0)
                ))

                content = result.find_all('span', class_='st')

                if content:
                    t = textwrap.wrap(content[0].text.replace('\n', ''), 78)
                    for l in t:
                        self.shell.stdout.write('  ' + l.strip() + '\n')
            except Exception, e:
                self.shell.stdout.write('Parse error')

            self.shell.stdout.write('-' * 80 + '\n')
