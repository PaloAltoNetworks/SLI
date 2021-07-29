import asyncssh
import re


class AsyncSSHSession:

    BUFFER_LEN = 9999

    def __init__(self, device, username, password):
        self.device = device
        self.username = username
        self.password = password
        self.client = None
        self.c_stdin = None
        self.c_stdout = None
        self.c_stderr = None
        self.prompt = None
        self.hostname = None

    async def connect(self):
        self.client = await asyncssh.connect(
            self.device,
            username=self.username,
            password=self.password,
            known_hosts=None,
            request_pty="force",
            term_type="vt100"
        )
        self.c_stdin, self.c_stdout, self.c_stderr = await self.client.open_session()
        await self._read_until_hostname()
        await self._set_cli_options()

    async def _read_until_hostname(self):
        """
        Read from stdout until a prompt is found, this will be variable
        length depending on any banners
        """
        prompt_found = None
        while not prompt_found:
            data = await self.c_stdout.read(self.BUFFER_LEN)
            prompt_found = self._check_for_prompt(data)
        self.prompt = data.strip()
        self.hostname = self.prompt.split("@")[1]

    async def _set_cli_options(self):
        """
        Send cli options to make interactive session script friendly
        """
        await self.cli_command("set cli scripting-mode on")
        await self.cli_command("set cli pager off")

    @staticmethod
    def _check_for_prompt(data):
        """
        Check for a line containing a prompt in a block of output
        """
        test_data = data.split("\n")
        if len(test_data):
            return re.match('^.*@.*[#>]$', test_data[-1].strip())
        return None

    async def cli_command(self, command):
        """
        Sends a command and returns response as string
        """
        self.c_stdin.write(command + "\n")
        data = ''
        prompt_found = None
        while not prompt_found:
            recv_data = await self.c_stdout.read(self.BUFFER_LEN)
            recv_data = recv_data.replace("\r\n", "\n")
            data += recv_data
            prompt_found = self._check_for_prompt(recv_data)

        # Return all lines after the first line as that will contain the submitted command
        return "\n".join(data.split("\n")[1:])
