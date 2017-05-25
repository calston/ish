import os
import sys
import shlex
import importlib
import StringIO

from cmd import Cmd

from subprocess import Popen, PIPE


class Shell(Cmd):
    prompt = "ISH#"

    def __init__(self):
        self.env = {
            'cwd': '/'
        }

        self.ps = "[ish]%(cwd)s$ "

        self.prompt = self.ps % self.env

        base_path = os.path.abspath(os.path.dirname(__file__))
        
        module_path = os.path.join(base_path, 'modules')

        modules = [fn[:-3] for fn in os.listdir(module_path)
                    if fn.endswith('.py') and fn[0] != '_']

        stdin = sys.stdin
        stdout = sys.stdout

        for m in modules:
            mod = getattr(importlib.import_module('websh.modules.%s' % m),
                            'Module')(self)

            for fn in dir(mod):
                if fn.startswith('do_'):
                    setattr(self.__class__, fn, getattr(mod, fn))

        Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.real_stdout = self.stdout
        self.real_stdin = self.stdin

    def setEnv(self, key, val):
        self.env[key] = val

        self.prompt = self.ps % self.env

    def execute(self, cmd):
        lexer = shlex.shlex(cmd)
        lexer.whitespace_split = True
        args = [t for t in lexer]
        
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
        lexer = shlex.shlex(line)
        lexer.whitespace = '|'
        lexer.whitespace_split = True

        tokens = [t.strip() for t in lexer]

        if len(tokens) <= 1:
            return Cmd.onecmd(self, line)

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
    Shell().cmdloop()
    
