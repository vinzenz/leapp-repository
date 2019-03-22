import os
import socket

from leapp.exceptions import CommandError
from leapp.utils.clicmd import command, command_opt

VERSION = "0.1.0"


@command('')
@command_opt('debug', is_flag=True, help='Enable debug mode', inherit=True)
@command_opt('verbose', is_flag=True, help='Enable verbose logging', inherit=True)
def cli(args):
    if os.getuid() != 0:
        raise CommandError("This tool has to be executed as root")
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else os.environ.get('LEAPP_DEBUG', '0')
    if os.environ['LEAPP_DEBUG'] == '1' or args.verbose:
        os.environ['LEAPP_VERBOSE'] = '1'
    else:
        os.environ['LEAPP_VERBOSE'] = os.environ.get('LEAPP_VERBOSE', '0')



def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    cli.command.execute('healthcheck version {}'.format(VERSION))
