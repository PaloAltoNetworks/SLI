import click
from sli.skilletLineInterface import SkilletLineInterface
from sli.tools import print_table


class FormatHelp(click.Command):
    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        commands = SkilletLineInterface.get_commands()
        print("\nAvailable Actions:\n")
        command_list = [{"cmd": x, "desc": getattr(commands[x], "short_desc", None)} for x in commands.keys()]
        print_table(command_list, {"Command": "cmd", "Description": "desc"})
        print("")

    def parse_args(self, ctx, args):
        """
        Check args for available commands, and print help_text if found. Otherwise,
        default to normal help text via 'format_help'
        """

        if "--help" in args and len(args) > 1:
            commands = SkilletLineInterface.get_commands()
            for command in args:
                if command in commands:
                    c = commands[command]
                    if hasattr(c, "help_text"):
                        print(c.help_text)
                        ctx.exit()
                    elif hasattr(c, "short_desc"):
                        print(c.short_desc)
                        ctx.exit()

        super().parse_args(ctx, args)


@click.command(cls=FormatHelp, context_settings={"allow_extra_args": True}, no_args_is_help=True)
@click.option("-e", "--environment", help="Environment file")
@click.option("-cm", "--commit", is_flag=True, help="Commit configuration changes")
@click.option("-cf", "--config-file", help="Input configuration file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-d", "--device", help="Device IP or hostname")
@click.option("-dp", "--port", help="Device port")
@click.option("-db", "--debug", is_flag=True, help="Run a command in debug mode")
@click.option("-le", "--loader-error", is_flag=True, help="Fail on SkilletLoader errors")
@click.option("-sd", "--directory", help="Directory to load skillets from", default="./")
@click.option("-u", "--username", help="Device username")
@click.option("-o", "--out-file", help="Output file")
@click.option("-off", "--offline", is_flag=True, help="Offline Mode - Do not connect to Device", default=False)
@click.option("-od", "--output-directory", help="Output Directory")
@click.option("-p", "--password", help="Device password")
@click.option("-n", "--name", help="Name of skillet to execute")
@click.option("-r", "--report", is_flag=True, help="Generate a panforge formatted report")
@click.option("-rf", "--report-file", help="Location of HTML file to create")
@click.option("-re", "--raise-exception", is_flag=True, help="Raise any enountered exceptions")
@click.option("-uc", "--use-context", is_flag=True, help="Use a context manager, (global by default)")
@click.option("-cn", "--context-name", help="Use a context manager other than global")
@click.option("-ec", "--encrypt-context", is_flag=True, help="Encrypt the context object")
@click.option("-cp", "--context-password", help="Password for encrypted context", default="")
@click.option("-cv", "--context-var", help="Context variable to store output in")
@click.option("-w", "--wait", help="Wait for number of seconds for PAN-OS device to come online")
@click.option(
    "-nc",
    "--no-config",
    is_flag=True,
    help="Hide full device configuration from output",
)
@click.option(
    "-of",
    "--output-format",
    help="Output format, xml or set",
    type=click.Choice(["xml", "set", "skillet"]),
    default="xml",
)
@click.option("-ad", "--defaults", is_flag=True, help="Assume all default inputs, useful for development")
@click.argument("action", nargs=1, default="execute")
@click.pass_context
def cli(ctx, action, **kwargs):

    options = {key: kwargs[key] for key in kwargs if kwargs[key] is not None}
    action = action.replace("-", "_")
    sli = SkilletLineInterface(options, action, ctx.args)
    sli.execute()


if __name__ == "__main__":
    cli()
