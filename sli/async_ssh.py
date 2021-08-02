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
        self.has_error = False
        self.error = None

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

    def error_check_output(self, output):
        """
        Return True on detecting error in output
        """
        lines = output.split("\n")
        for line in lines:
            if line.startswith("Unknown command:"):
                self.has_error = True
                self.error = line

    async def recv_until_prompt(self, echo=False):
        """
        Receive data from stdin until a prompt is seen, return any text
        """
        prompt_found = None
        data = ''
        while not prompt_found:
            recv_data = await self.c_stdout.read(self.BUFFER_LEN)
            recv_data = recv_data.replace("\r\n", "\n")
            data += recv_data
            prompt_found = self._check_for_prompt(recv_data)

        # Return all lines except the first and last line
        if echo:
            return data
        return "\n".join(data.split("\n")[1:-1])

    async def cli_command(self, command, echo=False):
        """
        Sends a command and returns response as string
        """
        self.has_error = False
        self.c_stdin.write(command + "\n")
        output = await self.recv_until_prompt(echo=echo)
        self.error_check_output(output)
        return output

    async def run_command_script(self, lines, out_file=None):
        """
        Take a list of lines and run them as a script, return True if no error
        Return False if error
        """
        self.has_error = False
        ll = lines
        if isinstance(ll, str):
            ll = ll.split("\n")

        # Setup output options
        session_output = ""
        if out_file:
            session_output = open(out_file, "w")

        for line in ll:
            if not len(line):
                continue
            output = await self.cli_command(line.strip(), echo=True)

            # Save output to file if specified
            if out_file:
                session_output.write(output)
            else:
                session_output += output

            # Stop running the script if an error was found
            self.error_check_output(output)
            if self.has_error:
                if out_file:
                    session_output.close()
                    return False
                return session_output

        # Only return output lines if not saving to a file
        if out_file:
            session_output.close()
            return True
        return session_output
