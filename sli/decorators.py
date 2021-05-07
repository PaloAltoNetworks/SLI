from getpass import getpass
from skilletlib.panoply import Panoply
from skilletlib.exceptions import TargetConnectionException
from sli.tools import get_var
from sli.ssh import SSHSession


def require_ngfw_connection_params(func):
    """
    Validate that SLI command has appropriate contexet paramaters
    to facilitate a connection to an NGFW
    """
    def wrap(command):

        # First, map CLI options into context dict
        device = command.sli.options.get('device', '')
        username = command.sli.options.get('username', '')
        password = command.sli.options.get('password', '')
        if len(device) > 0:
            command.sli.context['TARGET_IP'] = device
        if len(username) > 0:
            command.sli.context['TARGET_USERNAME'] = username
        if len(password) > 0:
            command.sli.context['TARGET_PASSWORD'] = password

        # If we don't have required input parameters, get them from the user
        if len(command.sli.context.get('TARGET_IP', '')) < 1:
            command.sli.context['TARGET_IP'] = input('Device: ')
        if len(command.sli.context.get('TARGET_USERNAME', '')) < 1:
            command.sli.context['TARGET_USERNAME'] = input('Username: ')
        if len(command.sli.context.get('TARGET_PASSWORD', '')) < 1:
            command.sli.context['TARGET_PASSWORD'] = getpass()
        return func(command)
    return wrap


def require_panoply_connection(func):
    """
    Requires a connected panoply session to the target device, will pass in
    the connected panoply instance as an argument
    """
    def wrap(command):
        pan = Panoply(
            command.sli.context['TARGET_IP'],
            command.sli.context['TARGET_USERNAME'],
            command.sli.context['TARGET_PASSWORD']
        )
        if not pan.connected:
            raise TargetConnectionException('Unable to connect to device')
        return func(command, pan)
    return wrap


def require_ngfw_ssh_session(func):
    def wrap(command):
        print(f"Connecting to {command.sli.context['TARGET_IP']}...")
        ssh = SSHSession(
            command.sli.context['TARGET_IP'],
            username=command.sli.context['TARGET_USERNAME'],
            password=command.sli.context['TARGET_PASSWORD']
        )
        print("Connected.")
        return func(command, ssh)
    return wrap


def load_variables(func):
    """Load variables from skillet and get user input if not supplied"""

    def wrap(command):
        for var in command.sli.skillet.variables:
            get_var(var, command.args, command.sli.context)
        if len(command.sli.skillet.variables):
            print("End of user variables.")
        return func(command)
    return wrap


def require_single_skillet(func):
    """Commands decorated with this require one skillet to be uniquely specified"""

    def wrap(command):
        if not command.sli.options.get('name') and len(command.sli.skillets) > 1:
            print(f'Specify a skillet to run with --name or -n when more than 1 is present for command {command.sli_command}')
            exit(1)

        target_name = command.sli.options.get('name') if command.sli.options.get('name') else command.sli.skillets[0].name
        command.sli.skillet = command.sli.sl.get_skillet_with_name(target_name)
        if command.sli.skillet is None:
            print(f'Unable to load skillet {target_name} by name')
            exit(1)
        return func(command)
    return wrap


def require_skillet_type(*args):
    """
    Commands decorated with this require a specific type of skillet to be executed.
    Inputs expected as *args, selected skillet type must match one
    """
    def inner(func):
        def wrap(command):
            skillet_type = command.sli.skillet.type
            if skillet_type not in args:
                print(f'Invalid type of skillet ({skillet_type}) for command {command.sli_command}, requires one of: {", ".join(args)}')
                exit(1)
            return func(command)
        return wrap
    return inner
