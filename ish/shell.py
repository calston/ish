import os
import requests
import sys
import shlex
import importlib
import StringIO

from cmd import Cmd

from subprocess import Popen, PIPE

from colored import fg, bg, attr


class Shell(Cmd):
    prompt = "ISH#"

    def __init__(self):
        self.env = {
            'cwd': '/',
            'ps': "%s[%sish%s]%s%%(cwd)s%s$ %s" % (
                fg(14), fg(6), fg(14), fg(165), fg(11), attr(0)),
            'secure': False
        }


        self.prompt = self.env['ps'] % self.env

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

    def _lex_split(self, s, ws=None):
        lexer = shlex.shlex(s)
        if ws:
            lexer.whitespace = ws
        lexer.whitespace_split = True
        tokens = [t.strip() for t in lexer]

        return tokens

    def setEnv(self, key, val):
        self.env[key] = val

        self.prompt = self.env['ps'] % self.env

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
                p.stdin.write(self.stdin.read().encode('utf-8', 'replace'))
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

    def onecmd(self, line):
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
