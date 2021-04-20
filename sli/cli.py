import click
from sli.skilletLineInterface import SkilletLineInterface
from sli.tools import load_config_file

class FormatHelp(click.Command):
    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        commands = SkilletLineInterface.get_commands()
        print('\nAvailable Commands:')
        for command in commands:
            c = commands[command]
            short_desc = getattr(c, 'short_desc', None)
            print(f'   {c.sli_command} {"- " + short_desc if short_desc else ""}')
        print('')

@click.command(cls=FormatHelp,
    context_settings={
        'allow_extra_args':True
    })
@click.option("-c", "--config", help="Configuration file")
@click.option("-cm", "--commit", is_flag=True, help="Commit configuration changes")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-d", "--device", help="Device IP or hostname")
@click.option("-le", "--loader-error", is_flag=True, help="Fail on SkilletLoader errors")
@click.option("-sd", "--directory", help="Directory to load skillets from", default="./")
@click.option("-u", "--username", help="Device username")
@click.option("-p", "--password", help="Device password")
@click.option("-n", "--name", help="Name of skillet to execute")
@click.option("-r", "--report", is_flag=True, help="Generate a panforge formatted report")
@click.option("-rf", "--report-file", help="Location of HTML file to create")
@click.option("-uc", "--use-context", is_flag=True, help="Use a context manager, (global by default)")
@click.option("-cn", "--context-name", help="Use a contexet manager other than global")
@click.option("-ec", "--encrypt-context", is_flag=True, help="Encrypt the context object")
@click.option("-cp", "--context-password", help="Password for encrypted context")
@click.option("-nc", "--no-config", is_flag=True, help="Hide full device configuration from output",)
@click.option("-of", "--output-format", help="Output format, xml or set",
    type=click.Choice(["xml", "set"]), default="xml"
    )
@click.argument("action", nargs=1, default="execute")
@click.pass_context
def cli(ctx, action, **kwargs):

    # Load configuration options from file, override with click parameters
    config_obj = load_config_file(kwargs.get('config'))
    for key in kwargs:
        if kwargs[key] is not None:
            config_obj[key] = kwargs[key]

    # Instantiate skillet and execute command
    sli = SkilletLineInterface(config_obj, action, ctx.args)
    sli.execute()


if __name__ == "__main__":
    cli()