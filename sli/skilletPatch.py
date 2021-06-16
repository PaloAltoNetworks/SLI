import os
from pathlib import Path
from jinja2 import Template
from sli.docker import DockerClient
from sli.tools import hash_file_contents, hash_string

# Imports to patch
from skilletlib.snippet.python3 import Python3Snippet

python_3_docker_template = """FROM {{ base_image }}
LABEL description="{{ tag }}"

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
"""


def python_3_snippet_execute(self, context):
    """
    Execute method for python3 snippets in a SLI specific environment
    """

    if not self.should_execute(context):
        return
    docker_client = DockerClient()

    # Check if existing image hash exists
    image_tag = docker_client.base_url
    script_path = Path(os.path.normpath(os.path.join(self.skillet.path, self.file)))
    script_dir = script_path.parent.absolute()
    reqs_file = script_dir.joinpath("requirements.txt")
    if os.path.exists(reqs_file):
        image_tag = "sli-py:" + hash_file_contents(reqs_file)[:15]

    # Build a new image if couldn't find one
    if not docker_client.image_exists(image_tag) and not image_tag == docker_client.base_url:
        print(f"Building a new python image for {image_tag}")
        docker_template = Template(python_3_docker_template)
        dockerfile = docker_template.render(tag=image_tag, base_image=docker_client.base_url)
        docker_client.add_build_file(dockerfile, "Dockerfile", is_str=True)
        docker_client.add_build_file(reqs_file, "requirements.txt")
        if not docker_client.build_image(image_tag):
            print(f"Docker build failed for image {image_tag}")
        docker_client.clear_build_dir()

    # Build and execute a container using script from snippet
    env = None
    if self.metadata.get("input_type") == "env":
        env = context
    print(f"Using image {image_tag}")
    script_name = self.file
    if "/" in script_name:
        script_name = script_name.split("/")[-1]
    docker_client.clear_run_dir()
    docker_client.add_run_file(script_path, script_name)
    print("Running container...")
    # Hash container name to ensure valid characters and exclusive execution
    container_name = hash_string(self.skillet.name + "-" + self.name)[:15]
    logs = docker_client.run_ephemeral(image_tag, container_name, f"python {script_name}", env=env)

    return logs, "success"


def patch_snippets():
    """
    Patch skilletlib provided methods that need to be replaced with SLI specific functionality
    """

    Python3Snippet.execute = python_3_snippet_execute
