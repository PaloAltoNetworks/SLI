from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.docker import DockerClient
from sli.tools import hash_file_contents, hash_string
from .base import BaseCommand

import os
from pathlib import Path
from jinja2 import Template

docker_template = """FROM registry.gitlab.com/panw-gse/as/as-py-base-image:latest
LABEL description="{{ tag }}"

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
"""


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
                image_tag = "sli-py:" + hash_file_contents(reqs_file)[:15]

            # Build a new image if couldn't find one
            if not docker_client.image_exists(image_tag):
                print(f"Building a new python image for {image_tag}")
                dockerfile = Template(docker_template).render(tag=image_tag)
                docker_client.add_build_file(dockerfile, "Dockerfile", is_str=True)
                docker_client.add_build_file(reqs_file, "requirements.txt")
                if not docker_client.build_image(image_tag):
                    print(f"Docker build failed for image {image_tag}")
                docker_client.clear_build_dir()

            # Build an execute a container using script from snippet
            print(f"Using image {image_tag}")
            docker_client.clear_run_dir()
            docker_client.add_run_rile(script_path)
            breakpoint()
            print("Running container...")
            # Hash container name to ensure valid characters and exclusive execution
            container_name = hash_string(self.sli.skillet.name + "-" + snippet.name)[:15]
            docker_client.run_ephemeral(image_tag, container_name, "C:/Users/amall/.sli/docker/run/", "python test.py")

            exit()  # TODO: Delete before merging

            # Capture outputs
