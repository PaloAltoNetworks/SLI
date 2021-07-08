import os
from pathlib import Path

import yaml
from git import Repo
from skilletlib import Skillet
from skilletlib import SkilletLoader

from .diff import DiffCommand
from ..errors import InvalidArgumentsException
from ..errors import SLIException
from ..tools import get_input


class AnsibleRoleCommand(DiffCommand):
    sli_command = "ansible_role"
    short_desc = (
        "Builds an Ansible Role from the differences between two config versions, candidate, running, "
        "previous running, etc"
    )
    no_skillet = True
    repo_url = "https://gitlab.com/panw-gse/as/pan_community-ansible-collection-skeleton.git"
    help_text = """
        ansible_role module requires 0 to 2 arguments.

        - 0 arguments: Diff running config from previous running config
        - 1 argument: Diff previous config or named config against specified running config
        - 2 arguments: Diff first arg named config against second arg named config

        A named config can be either a stored config, candidate, running or a number.
        Positive numbers must be used to specify iterations, 1 means 1 config revision ago

        Example: Get diff between running config and previous running config

            user$ sli ansible_role 1 -uc  -od /tmp/roles

        Example: Get diff between running config and the candidate config

            user$ sli ansible_role running candidate -uc -od /tmp/roles

        Example: Get the diff of all changes made to this device using the autogenerated 'baseline' config, which is
        essentially blank.

            user$ sli ansible_role baseline -uc -od /tmp/roles

        Example: Get the diff between the second and third most recent running configs

            user$ sli ansible_role 3 2 -uc -od /tmp/roles
    """

    @staticmethod
    def __write_file_to_location(file_path_root: Path, file_name: str, file_contents: str) -> None:
        """
        utility method to ensure a path exists and write the file_contents into file_name at file_path_root

        :param file_path_root: directory in which to check for the existence of file_name
        :param file_name: name of the file to write
        :param file_contents: string contents of the file to write
        :return: None
        """

        file_path = file_path_root.joinpath(file_name).resolve()

        if not file_path_root.exists():
            raise SLIException("Could not write file!")

        try:
            with file_path.open(mode="w") as fp:
                fp.write(file_contents)
        except OSError as oe:
            raise SLIException(f"Could not write file! {oe}")

    @staticmethod
    def _load_skillet(skillet_name: str, source_dir: Path) -> Skillet:
        """
        Returns a skillet found in the source_dir folder
        """
        inline_sl = SkilletLoader(source_dir)
        app_skillet: Skillet = inline_sl.get_skillet_with_name(skillet_name)

        if not app_skillet:
            raise SLIException("Could not find required resources")

        return app_skillet

    def _get_vars(self) -> list:
        """
        Return a list of a single variable to populate the test, readme, and variable_list files
        """
        return [
            {
                "name": "custom_variable",
                "description": "Custom Variable",
                "default": "default_value",
                "type_hint": "text",
            }
        ]

    def _get_version(self) -> str:
        return self.pan.facts["sw-version"]

    def _handle_snippets(self, snippets: list, variable_list: list) -> None:
        """
         override method to perform action on the list of diffs. In this case, build the ansible role structure

        :param snippets: list of differences found from Skilletlib
        "param variable_list: list of variables as found in the snippets
        :return: None
        """
        if not len(snippets):
            print("No Configuration diffs found! Try a different combination of configuration sources")
            exit(1)

        namespace = get_input("Namespace", "pan_community")
        role_name = get_input("Role Name", "generated_role")
        description = get_input("Role Description", "generated_role")
        author_name = get_input("Author Name", "john doe")

        # get version and major version from connected NGFW
        version = self._get_version()
        major_version = ".".join(version.split(".")[0:2])

        # verify output dir structure and existence
        output_dir: str = self.sli.options.get("output_directory", None)

        if output_dir is None:
            output_dir = "./ansible_collections"

        if str(output_dir).startswith("./"):
            output_path = Path(os.getcwd()).joinpath(output_dir).resolve()
        else:
            output_path = Path(output_dir)
            if not output_path.exists() and not output_path.parent.exists():
                raise InvalidArgumentsException("Output directory does not exist!")

        if output_dir != "ansible_collections":
            output_path = output_path.joinpath("ansible_collections")
            output_path.mkdir(parents=True, exist_ok=True)

        if next(os.scandir(output_path), None):
            raise SLIException(f"Ansible Roles Directory: {output_path} must be empty!")

        # clone our skeleton repo
        Repo.clone_from(url=self.repo_url, to_path=output_path, env={"GIT_SSL_NO_VERIFY": "1"})

        # rename the directory structure appropriately
        # it comes from the skeleton repo as
        # example/
        #   skeleton/
        #       roles/
        #           skeleton/

        # rename example to namespace
        top_level = output_path.joinpath("example")
        namespace_path = output_path.joinpath(namespace)
        top_level.rename(namespace_path)

        # rename skeleton to role_name
        skeleton = namespace_path.joinpath("skeleton")
        collection_path = skeleton.parent.joinpath(role_name)
        skeleton.rename(collection_path)

        # rename roles/skeleton to roles/role_name
        skeleton_role_path = collection_path.joinpath("roles/skeleton")
        role_path = skeleton_role_path.parent.joinpath(role_name)
        skeleton_role_path.rename(role_path)

        # create our inline skilletloader instance
        inline_sl = SkilletLoader(output_path)

        # create README
        readme_skillet = inline_sl.get_skillet_with_name("readme_template")
        readme_outout = readme_skillet.execute(
            {
                "role_name": role_name,
                "description": description,
                "author_name": author_name,
                "namespace": namespace,
                "variable_list": variable_list,
            }
        )

        self.__write_file_to_location(output_path, "README.md", readme_outout["template"])
        self.__write_file_to_location(collection_path, "README.md", readme_outout["template"])

        # create Role README
        role_readme_skillet = inline_sl.get_skillet_with_name("role_readme_template")
        role_readme_outout = role_readme_skillet.execute(
            {
                "role_name": role_name,
                "description": description,
                "author_name": author_name,
                "namespace": namespace,
                "variable_list": variable_list,
            }
        )

        self.__write_file_to_location(role_path, "README.md", role_readme_outout["template"])

        # write out galaxy.yml file from template
        galaxy_skillet = inline_sl.get_skillet_with_name("ansible_galaxy_template")

        output = galaxy_skillet.execute(
            {"role_name": role_name, "description": description, "author_name": author_name}
        )

        self.__write_file_to_location(collection_path, "galaxy.yml", output["template"])

        # add major version to supported_versions list
        supported_versions = [major_version]

        # create role vars file
        vars_file_data = dict()
        vars_file_data["supported_versions"] = supported_versions
        supported_versions_yaml = yaml.safe_dump(vars_file_data)

        role_vars_path = role_path.joinpath("vars")
        self.__write_file_to_location(role_vars_path, "main.yml", supported_versions_yaml)

        # create version specific task file
        role_tasks_path = role_path.joinpath("tasks")
        ansible_task_template = inline_sl.get_skillet_with_name("ansible_task_template")
        task_output = ansible_task_template.execute({"snippets": snippets})
        self.__write_file_to_location(role_tasks_path, f"panos-{major_version}.yml", task_output["template"])

        # create role meta file
        role_meta_path = role_path.joinpath("meta")
        ansible_task_meta_template = inline_sl.get_skillet_with_name("ansible_task_meta_template")
        task_output = ansible_task_meta_template.execute(
            {
                "role_name": role_name,
                "description": description,
                "author_name": author_name,
                "variable_list": variable_list,
            }
        )
        self.__write_file_to_location(role_meta_path, "main.yml", task_output["template"])

        # create role test file
        role_test_path = role_path.joinpath("tests")
        ansible_test_template = inline_sl.get_skillet_with_name("ansible_test_template")
        task_output = ansible_test_template.execute({"role_name": role_name, "variable_list": variable_list})
        self.__write_file_to_location(role_test_path, "test.yml", task_output["template"])

        print(f"Ansible Role created in {output_path} successfully!")
