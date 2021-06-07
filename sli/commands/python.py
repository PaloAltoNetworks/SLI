from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.decorators import require_docker_client
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
    @require_docker_client
    def run(self, docker_client):

        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:
            if not snippet.should_execute(self.sli.context):
                continue

            # Check if existing image hash exists
            image_tag = docker_client.base_image
            script_path = Path(os.path.normpath(os.path.join(self.sli.skillet.path, snippet.file)))
            script_dir = script_path.parent.absolute()
            reqs_file = script_dir.joinpath("requirements.txt")
            if os.path.exists(reqs_file):
                image_tag = "sli-py:" + hash_file_contents(reqs_file)[:15]

            # Build a new image if couldn't find one
            if not docker_client.image_exists(image_tag) and not image_tag == docker_client.base_image:
                print(f"Building a new python image for {image_tag}")
                dockerfile = Template(docker_template).render(tag=image_tag)
                docker_client.add_build_file(dockerfile, "Dockerfile", is_str=True)
                docker_client.add_build_file(reqs_file, "requirements.txt")
                if not docker_client.build_image(image_tag):
                    print(f"Docker build failed for image {image_tag}")
                docker_client.clear_build_dir()

            # Build an execute a container using script from snippet
            print(f"Using image {image_tag}")
            script_name = snippet.file
            if "/" in script_name:
                script_name = script_name.split("/")[-1]
            docker_client.clear_run_dir()
            docker_client.add_run_file(script_path, script_name)
            print("Running container...")
            # Hash container name to ensure valid characters and exclusive execution
            container_name = hash_string(self.sli.skillet.name + "-" + snippet.name)[:15]
            logs = docker_client.run_ephemeral(image_tag, container_name, f"python {script_name}")

            # Capture outputs
            snippet.capture_outputs(logs, "success")
