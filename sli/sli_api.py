"""
A Programamtic entrypoint for sli commands, populates sys.argv
as if the command were called from the CLI directly.
usage:

from sli.sli_api import run_command
run_command("sli configure -n my_skillet.skillet.yaml -d 192.168.1.1 -u username -p password")
"""

import sys
from sli.cli import cli
from sli.errors import SLIException, InvalidArgumentsException


def start_quote(text):
    """Check for text starting quote"""
    return text.startswith("'") or text.startswith('"')


def end_quote(text):
    """Check for text ending quote"""
    return text.endswith("'") or text.endswith('"')


def remove_quote(text):
    """Remove quotes from text"""
    return text.replace("'", "").replace('"', "")


def sli_command(command):
    """
    Break a given command apart and load it into sys.argv as if
    it was processed normally from the cli
    """
    cmd = command.strip().split(" ")
    if not cmd[0] == "sli":
        raise SLIException("SLI command did not start with sli")
    cmd = cmd[1:]
    arg = ''
    in_arg = False
    for c in cmd:
        if start_quote(c):
            in_arg = True
            arg += remove_quote(c)
        elif in_arg and end_quote(c):
            in_arg = False
            arg += " " + remove_quote(c)
            sys.argv.append(arg)
            arg = ''
        elif in_arg:
            arg += " " + c
        else:
            sys.argv.append(c)
    if in_arg:
        raise InvalidArgumentsException("No closing quote found in SLI arguments")
    cli(standalone_mode=False)
