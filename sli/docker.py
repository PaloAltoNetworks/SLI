import docker
from sli.tools import expandedHomePath
import os
import shutil


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
        self._setup_system()
        self.clear_build_dir()

    def _setup_system(self):
        for d in self.docker_path, self.build_path:
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
