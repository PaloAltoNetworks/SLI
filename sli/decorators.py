from getpass import getpass

def require_ngfw_connection_params(func):
    """
    Validate that SLI command has appropriate contexet paramaters
    to facilitate a connection to an NGFW
    """
    def wrap(command):
        if len(command.sli.context.get('TARGET_IP', '')) < 1:
            command.sli.context['TARGET_IP'] = input('Device: ')
        if len(command.sli.context.get('TARGET_USERNAME', '')) < 1:
            command.sli.context['TARGET_USERNAME'] = input('Username: ')
        if len(command.sli.context.get('TARGET_PASSWORD', '')) < 1:
            command.sli.context['TARGET_PASSWORD'] = getpass()
        return func(command)
    return wrap

def require_single_skillet(func):
    """Commands decorated with this require one skillet to be uniquely specified"""

    def wrap(command):
        if not command.sli.options.get('name') and len(command.sli.skillets) > 1:
            print(f'Specify a skillet to run with --name when more than 1 is present for command{command.sli_command}')
            exit(1)

        target_name = command.sli.options['name'] if command.sli.options['name'] else command.sli.skillets[0].name
        command.sli.skillet = command.sli.sl.get_skillet_with_name(target_name)
        if command.sli.skillet is None:
            print(f'Unable to load skillet {target_name} by name')
            exit(1)
        return func(command)
    return wrap
