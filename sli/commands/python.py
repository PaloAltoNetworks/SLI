from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.docker import DockerClient
from sli.tools import hash_file_contents
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
            docker_client = DockerClient()
            if not docker_client.connected:
                print("Unable to connect to docker")
                return

            # Check if existing image hash exists
            image_tag = DockerClient.base_image
            script_path = Path(os.path.normpath(os.path.join(self.sli.skillet.path, snippet.file)))
            script_dir = script_path.parent.absolute()
            reqs_file = script_dir.joinpath("requirements.txt")
            if os.path.exists(reqs_file):
                image_tag = "as-py:" + hash_file_contents(reqs_file)[:15]

            # Build a new image if couldn't find one
            if not docker_client.image_exists(image_tag):
                print(f"Building a new python image for {image_tag}")
                # docker_client.add_build_file(Dockerfile, "Dockerfile")
                # docker_client.add_build_file(reqs_path, "requirements.txt")
                # docker_client.build_image(image_tag)
                # docker_client.clear_build_dir()
            

            exit() # TODO: Delete before merging
            print(f"Using image {image_tag}")

            # Execute container
