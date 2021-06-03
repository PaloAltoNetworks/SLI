from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

import os
from pathlib import Path


class PythonCommand(BaseCommand):
    sli_command = 'python'
    short_desc = 'Execute a python skillet'

    @require_single_skillet
    @require_skillet_type('python3')
    @load_variables
    def run(self):

        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:
            if not snippet.should_execute(self.sli.context):
                continue

            # Check connectivity
            docker_client = docker.APIClient()
            if not docker_client.ping():
                print("Unable to connect to docker")
                return
            print("Connected to docker")

            # Check if existing image hash exists
            script_path = Path(os.path.normpath(os.path.join(self.sli.skillet.path, snippet.file)))
            script_dir = script_path.parent.absolute()
            reqs_file = script_dir.joinpath("requirements.txt")
            print(script_path)
            print(script_dir)
            print(reqs_file)
            if os.path.exists(reqs_file):
                print("reqs!")

            # Build a new image if couldn't find one

            # Execute container

            exit()

            # breakpoint()

base = "registry.gitlab.com/panw-gse/as/as-py-base-image:latest"

import docker


class DockerClient:

    def __init__(self):
        self.client = docker.APIClient()
        self.connected = self._check_connectivity()
    
    def _check_connectivity(self):
        self.connected = self.client.ping()
        if not self.connected:
            print("Unable to connect to docker!")

