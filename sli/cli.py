import click
from sli.skilletLineInterface import SkilletLineInterface
from sli.tools import load_config_file

@click.command()
@click.option("-c", "--config", help="Configuration file")
@click.option("-d", "--device", help="Device IP or hostname")
@click.option("-sd", "--directory", help="Directory to load skillets from", default="./")
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

    # Instantiate skillet and execute command
    sli = SkilletLineInterface(config_obj, action)
    sli.run_command()


if __name__ == "__main__":
    cli()