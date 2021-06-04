import docker
from sli.tools import expandedHomePath
import os
import shutil
import json
from pprint import pprint


class DockerClient:
    """
    Client for Docker Desktop API
    """

    base_url = "registry.gitlab.com/panw-gse/as/as-py-base-image:latest"
    base_image = base_url.split("/")[-1]

    def __init__(self):
        self.client = docker.APIClient()
        self.connected = self.client.ping()
        if not self.connected:
            print("Unable to connect to docker!")
            return
        self.docker_path = expandedHomePath(".sli/docker")
        self.build_path = expandedHomePath(".sli/docker/build")
        self.run_path = expandedHomePath(".sli/docker/run")
        self._setup_system()
        self.clear_build_dir()

    def _setup_system(self):
        for d in self.docker_path, self.build_path, self.run_path:
            if not os.path.exists(d):
                os.mkdir(d)

    def clear_build_dir(self):
        for item in os.listdir(self.build_path):
            item_path = self.build_path + os.sep + item
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

    def image_exists(self, image_tag):
        """Check by tag if an image exists"""
        return self.get_image(image_tag) is not None

    def get_image(self, image_tag):
        """Get an image by tag and return it, return None if not found"""
        found = []
        images = self.client.images()
        for image in images:
            repo_tags = image.get("RepoTags")
            if not isinstance(repo_tags, list):
                continue
            for tag in repo_tags:
                if tag.split("/")[-1] == image_tag:
                    found.append(image)
        if len(found) > 1:
            raise Exception(f"Docker image tag {tag} found on multiple images, docker image cleanup required.")
        if len(found) == 1:
            return found[0]
        return None

    def add_build_file(self, file_src, file_name, is_str=False):
        """Add a file to docker build director, is_str signifies if file is passed in as string"""
        file_name = file_name.replace("/", os.sep)
        dst_path = self.build_path + os.sep + file_name
        if is_str:
            with open(dst_path, "w") as f:
                f.write(file_src)
        else:
            if os.path.isdir(file_src):
                shutil.copytree(file_src, dst_path)
            else:
                shutil.copy(file_src, dst_path)

    def build_image(self, tag):
        """
        Build a docker image and tag it with supplied tag.
        Returns True if build success, False if build failed
        """
        for line in self.client.build(path=self.build_path, rm=True, tag=tag):
            strLine = line.decode("utf-8").strip()
            ll = [json.loads(x) for x in strLine.split('\r\n') if len(x)]
            if len(ll):
                for msg in ll:
                    if 'error' in msg:
                        return False
                    elif 'stream' in msg:
                        print(msg['stream'].strip())
                    else:
                        pprint(msg)
        return True

    def get_container(self, search_name):
        """Get a container based on name, return None if not found"""
        found = []
        containers = self.client.containers(all=True)
        for container in containers:
            names = container.get("Names")
            if isinstance(names, list):
                for name in names:
                    if name.replace("/", "") == search_name:
                        found.append(container)
        if len(found) > 1:
            raise Exception(f"Found more than one container when searching for {name}, please cleanup docker")
        if len(found) == 1:
            return found[0]
        return None

    def run_ephemeral(self, tag, container_name, run_dir, run_cmd):
        """
        Create an ephemeral container, execute, and remove container
        """

        # If a contianer by a name we are using already exists, remove it
        found = self.get_container(container_name)
        if found is not None:
            print(f"Found existing container, removing {container_name}")
            self.client.remove_container(found["Id"])

        container_obj = self.client.create_container(
                tag,
                name=container_name,
                command=run_cmd,
                volumes=["/app"],
                host_config=self.client.create_host_config(binds=[
                    f"{run_dir}:/app"
                ])
            )
        container_id = container_obj.get("Id")
        if not container_id:
            raise Exception(f"Unable to create container from image {tag}")

        self.client.start(container_id)
        exit_code = self.client.wait(container_id)
        if not exit_code["StatusCode"] == 0:
            print(f"Container error: {exit_code['Error']}")
            raise Exception(f"Container {container_id} returned exit code {exit_code}")
        print("Container ran successfully")
        container_logs = self.client.logs(container_id).decode("utf-8")
        print(container_logs)

        self.client.remove_container(container_id, force=True)
