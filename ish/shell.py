import os
import fcntl
import termios
import struct
import requests
import sys
import shlex
import importlib
import StringIO

from cmd import Cmd

from subprocess import Popen, PIPE

from colored import fg, bg, attr

try:
    from pipes import quote
except:
    from shlex import quote


class Shell(Cmd):
    prompt = "ISH#"
    def __init__(self):
        self.env = {
            'CWD': '/',
            'PS': "%s[%sish%s]%s%%(CWD)s%s$ %s" % (
                fg(14), fg(6), fg(14), fg(165), fg(11), attr(0)),
            'SECURE': False,
            'TERM': self.getTerminalSize()
        }

        self.prompt = self.env['PS'] % self.env

        self.session = requests.Session()

        base_path = os.path.abspath(os.path.dirname(__file__))

        module_path = os.path.join(base_path, 'modules')

        modules = [fn[:-3] for fn in os.listdir(module_path)
                    if fn.endswith('.py') and fn[0] != '_']

        stdin = sys.stdin
        stdout = sys.stdout

        for m in modules:
            mod = getattr(importlib.import_module('ish.modules.%s' % m),
                            'Module')(self)

            for fn in dir(mod):
                if fn.startswith('do_'):
                    setattr(self.__class__, fn, getattr(mod, fn))

        Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.real_stdout = self.stdout
        self.real_stdin = self.stdin

    def ioctl_GWINSZ(self, fd):
        try:
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr

    def getTerminalSize(self):
        env = os.environ

        cr = self.ioctl_GWINSZ(0) or self.ioctl_GWINSZ(1) \
                or self.ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = self.ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        return int(cr[1]), int(cr[0])

    def _lex_split(self, s, ws=None, posix=True):
        lexer = shlex.shlex(s, posix=posix)
        if ws:
            lexer.whitespace = ws
        lexer.whitespace_split = True
        tokens = [t.strip() for t in lexer]

        return tokens

    def setEnv(self, key, val):
        self.env[key.upper()] = val

        self.prompt = self.env['PS'] % self.env

    def getEnv(self, key, default=None):
        return self.env.get(key.upper(), default)

    def execute(self, cmd):
        args = self._lex_split(cmd)

        if "fileno" not in dir(self.stdout):
            self.stdout = PIPE

        if "fileno" in dir(self.stdin):
            stdin = self.stdin
        else:
            stdin = PIPE

        try:
            p = Popen(args, stdin=stdin, stdout=self.stdout)
            if self.stdin and p.stdin:
                p.stdin.write(self.stdin.read())
                p.stdin.close()
            p.wait()

            if p.stdout:
                self.stdout = p.stdout
        except Exception, e:
            self.real_stdout.write('Error: ' + str(e) + '\n')

        if self.stdout == PIPE:
            self.stdout = StringIO.StringIO()

    def emptyline(self):
        return None

    def _parse_variables(self, s):

        escaped = False

        rlist = []

        for loc, ch in enumerate(s):
            # Char by char...
            if ch == "'":
                escaped = not escaped

            if (not escaped) and ch=='$':
                if (loc > 0) and (s[loc-1] == '\\'):
                    continue

                else:
                    segment = s[loc:]
                    pos = 1
                    while pos < len(segment) and segment[pos].isalpha():
                        pos += 1
                    var = segment[:pos]
                    nvar = var[1:].upper()

                    if var and (nvar in self.env):
                        rlist.append((var, loc, len(var),
                                        str(self.getEnv(nvar))))
        ln = s
        for var, loc, chars, env in rlist:
            ln = ln[:loc] + quote(env) + ln[loc+chars:]

        return ln


    def onecmd(self, line):
        line = self._parse_variables(line)

        # Process ; separated commands
        commands = self._lex_split(line, ws=';')
        if len(commands) > 1:
            for cmd in commands:
                self.onecmd(cmd)

            return None

        # Parse pipe directives
        tokens = self._lex_split(line, ws='|')

        if len(tokens) <= 1:
            # If it's a simple line then use the standard parser
            return Cmd.onecmd(self, line)

        # Parse out a redirected set of pipes
        lastResult = None
        stdin = None
        for i, token in enumerate(tokens):
            if stdin:
                try:
                    stdin.seek(0)
                except:
                    pass
                self.stdin = stdin

            if i == len(tokens) - 1:
                self.stdout = self.real_stdout
            else:
                self.stdout = StringIO.StringIO()

            cmd, arg, line = self.parseline(token)

            self.lastcmd = line

            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                lastResult = self.default(line)

            lastResult = func(arg)
            stdin = self.stdout

        self.stdout = self.real_stdout
        self.stdin = self.real_stdin
        return lastResult

    def do_exit(self, line):
        "Quit interpipe shell"
        self.stdout.write("\n")
        return True

    def do_EOF(self, line):
        "Quit interpipe shell"
        self.stdout.write("\n")
        return True

def init():
    if len(sys.argv) > 1:
        ln = ' '.join(sys.argv[1:])
        Shell().onecmd(ln)
    else:
        Shell().cmdloop()
