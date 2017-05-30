import textwrap

from bs4 import element

from colored import fg, bg, attr


class HTMLParser(object):
    def __init__(self, soup, shell):
        self.soup = soup
        self.shell = shell

        self.x = 0

    def _align_term(self, s, width=80):
        return textwrap.wrap(s, width - self.x, replace_whitespace=False)

    def _flatten_content(self, content):
        return u' '.join([text for tag, text in content]).rstrip()

    def render_span(self, tag, content):
        return self._flatten_content(content)

    def render_div(self, tag, content):
        return u'\n' + self._flatten_content(content) + u'\n'

    def render_p(self, tag, content):
        t = self._flatten_content(content)
        blocks = self._align_term(t, 76)
        cstr = "\n"
        for b in blocks:
            cstr += "    " + b + '\n'

        return cstr + '\n'

    def render_b(self, tag, content):
        return attr(1) + self._flatten_content(content) + attr(0)

    def render_u(self, tag, content):
        return attr(4) + self._flatten_content(content) + attr(0)

    def render_a(self, tag, content):
        link = tag.get('href', u'').encode('utf8', 'ignore')
        text = self._flatten_content(content)
        return u"%s [%s]" % (text, link)

    def render_h1(self, tag, content):
        return content.upper(self._flatten_content(content))

    def render_h2(self, tag, content):
        return content.upper(self._flatten_content(content))

    def render_h3(self, tag, content):
        return content.upper(self._flatten_content(content))

    def render_h4(self, tag, content):
        return content.upper(self._flatten_content(content))

    def render_h5(self, tag, content):
        return content.upper(self._flatten_content(content))

    def render_hr(self, tag, content):
        ln = "_" * 80
        return '\n' + ln + '\n'

    def render_br(self, tag, content):
        return "\n"

    def render_li(self, tag, content):
        n = self._flatten_content(content)
        o = n + '\n'
        return o

    def render_tt(self, tag, content):
        return self._flatten_content(content)

    def render_pre(self, tag, content):
        return u'\n' + self._flatten_content(content) + u'\n'

    def render_ul(self, tag, content):
        l = u"\n"
        for tag, text in content:
            if tag != 'li':
                continue

            w = textwrap.wrap(text, 76)
            l += u'  * '
            n = 0
            for ln in w:
                if n == 0:
                    l += ln + '\n'
                else:
                    l +=  u'    ' + ln + '\n'
                n += 1
            l += '\n'
        return l

    def render_body(self, tag, content):
        return self._flatten_content(content)

    def render_head(self, tag, content):
        return ""

    def render_script(self, tag, content):
        # Discard
        return ""

    def render_tr(self, tag, content):
        return self._flatten_content(content)

    def render_td(self, tag, content):
        return self._flatten_content(content)

    def render_th(self, tag, content):
        return self._flatten_content(content)

    def render_tbody(self, tag, content):
        return self._flatten_content(content)

    def render_thead(self, tag, content):
        return self._flatten_content(content)

    def render_table(self, tag, content):
        return self._flatten_content(content)

    def iterTags(self, tag):
        cont = []
        if not tag:
            return u""

        for c in tag.children:
            if isinstance(c, element.Tag):
                et = self.iterTags(c)

            elif isinstance(c, element.Comment):
                continue

            else:
                # Sanitise tag text content
                t = u' '.join(textwrap.dedent(c).split())
                if t:
                    et = ('text', t)
                else:
                    et = None

            if isinstance(et, list):
                cont.extend([i for i in et if i])
            elif et:
                cont.append(et)
        content = [c for c in cont]

        caller = 'render_%s' % tag.name
        if caller in dir(self.__class__):
            cfn = getattr(self, caller)
            return (tag.name, cfn(tag, content))
        else:
            #print "Need to implement %s" % caller
            pass

        return (tag.name, self._flatten_content(content))

    def parse(self):
        if self.soup.body:
            st = self.iterTags(self.soup.body)[1]
            print st
            return st
        #blocks = self._align_term(st.encode('ascii', 'ignore'), 80)

        #return '\n'.join(blocks)
