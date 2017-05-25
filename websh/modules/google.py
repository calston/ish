import requests

import urlparse

from colored import fg, bg, attr

from bs4 import BeautifulSoup

from websh.base import Command

class Module(Command):
    def do_google(self, arg):
        "Google the intertubes"
        
        r = requests.get('https://www.google.co.za/search', params={'q': arg})

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

                blocklen = 78
                if content:
                    t = content[0].text.replace('\n', '')
                    if len(t) > blocklen:
                        while len(t) > blocklen:
                            ln = t[:blocklen]
                            t = t[blocklen:]

                            if len(t) > 0 and not t.startswith(' ') and not ln.endswith(' '):
                                ln, e = ln.rsplit(None, 1)
                                t = e + t

                            self.shell.stdout.write(' ' + ln.strip() + '\n')
                        self.shell.stdout.write(' ' + t.strip() + '\n')
                    else: 
                        self.shell.stdout.write(' ' + t.strip() + '\n')
            except Exception, e:
                self.shell.stdout.write('Parse error')

            self.shell.stdout.write('-' * 80 + '\n')
