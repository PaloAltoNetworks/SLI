import click

from sli.skilletLineInterface import SkilletLineInterface
from sli.tools import load_config_file

@click.command()
@click.option("-c", "--config", help="Configuration file")
@click.option("-d", "--device", help="Device IP or hostname")
@click.option("-u", "--username", help="Device username")
@click.option("-p", "--password", help="Device password")
@click.option("-n", "--name", help="Name of skillet to execute")
@click.option("-r", "--report", is_flag=True, help="Generate a panforge formatted report")
@click.argument("action", nargs=1, default="execute")
def cli(action, **kwargs):

    # Load configuration options from file, override with click parameters
    config_obj = load_config_file(kwargs.get('config'))
    for key in kwargs:
        if kwargs[key] is not None:
            config_obj[key] = kwargs[key]

    actions = ['execute', 'test_load']
    if not action in actions:
        ctx = click.get_current_context()
        ctx.fail(f"Invalid action - {action}")

    # Instantiate skillet and execute command
    sli = SkilletLineInterface(config_obj)
    getattr(sli, action)()