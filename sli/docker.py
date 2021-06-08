import docker
from sli.tools import expandedHomePath
import os
import shutil
import json
import time
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
        self.home_path = expandedHomePath(".sli/docker/home")
        self._setup_system()
        self.clear_build_dir()

    def _setup_system(self):
        for d in self.docker_path, self.build_path, self.run_path, self.home_path:
            if not os.path.exists(d):
                os.mkdir(d)

    def clear_build_dir(self):
        self.clear_dir(self.build_path)

    def clear_run_dir(self):
        self.clear_dir(self.run_path)

    @staticmethod
    def file_system_name(name):
        """Convert a given name to be file system friendly"""
        char_map = {":": "_"}
        return "".join([char_map.get(x, x) for x in name])

    @staticmethod
    def clear_dir(target):
        for item in os.listdir(target):
            item_path = target + os.sep + item
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

    def add_run_file(self, file_src, file_name, is_str=False):
        self.add_file_to_dir(file_src, file_name, self.run_path, is_str=is_str)

    @staticmethod
    def add_file_to_dir(file_src, file_name, target_dir, is_str=False):
        file_name = file_name.replace("/", os.sep)
        dst_path = target_dir + os.sep + file_name
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

    def _setup_home_dir(self, dir_name):
        """Ensure a given image tag has a home directory available, assumes dir_name is file system friendly"""
        target_home = self.home_path + os.sep + dir_name
        if not os.path.exists(target_home):
            os.mkdir(target_home)
        return target_home

    def run_ephemeral(self, tag, container_name, run_cmd, env=None):
        """Create an ephemeral container, execute, and remove container"""

        home_dir = self._setup_home_dir(self.file_system_name(tag))

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
                environment=env,
                host_config=self.client.create_host_config(binds=[
                    f"{self.run_path}:/app",
                    f"{home_dir}:/root"
                ])
            )
        container_id = container_obj.get("Id")
        if not container_id:
            raise Exception(f"Unable to create container from image {tag}")

        # Start the container, monitor its status, display it's output
        self.client.start(container_id)
        container = self.get_container(container_name)
        logs = self.client.logs(container_id).decode("utf-8")
        print(logs)
        logs_len = len(logs)
        while container.get("State", "") == "running":
            time.sleep(1)
            container = self.get_container(container_name)
            logs = self.client.logs(container_id).decode("utf-8")
            if len(logs) > logs_len:
                print(logs[logs_len:])
                logs_len += len(logs)

        # State has changed, let it exit and grab the exit code
        exit_code = self.client.wait(container_id)
        if not exit_code["StatusCode"] == 0:
            print(f"Container error: {exit_code['Error']}")
            raise Exception(f"Container {container_id} returned exit code {exit_code}")
        print("Container ran successfully")

        logs = self.client.logs(container_id).decode("utf-8")
        self.client.remove_container(container_id, force=True)
        return logs
