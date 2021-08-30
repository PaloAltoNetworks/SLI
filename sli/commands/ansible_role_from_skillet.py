from .ansible_role_from_diff import AnsibleRoleCommand
from ..decorators import require_single_skillet
from ..decorators import require_skillet_type
from ..errors import InvalidArgumentsException
from ..tools import get_input


class SkilletToAnsibleRoleCommand(AnsibleRoleCommand):
    sli_command = "ansible_role_from_skillet"
    short_desc = "Builds an Ansible Role from the a Skillet"
    no_skillet = False
    capture_var = None
    pan = None
    suppress_output = True
    help_text = """
        ansible_role_from_skillet creates a complete Ansible Collection and Role directory structure from a skillet.

        Example: Create a collection in the /tmp/roles directory using the test_skillet from the /tmp/skillets directory

            user$ sli ansible_role_from_skillet --name test_skillet -sd /tmp/skillets -od /tmp/roles
    """

    def _parse_args(self) -> None:
        pass

    def _get_snippets(self) -> list:
        """
        Internal method to actually perform the diff operation.
        """

        skillet_dict = self.sli.skillet.skillet_dict
        return skillet_dict["snippets"]

    def _get_vars(self) -> list:
        return self.sli.skillet.skillet_dict["variables"]

    def _update_context(self, diff: list) -> None:
        pass

    def _get_version(self):
        """
        Sadly, we can't get this directly from the loaded skillet programmatically...
        """
        return get_input("PAN-OS Version to target", "10.0")

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    def run(self):
        """Get a diff of running and candidate configs"""

        try:
            self._parse_args()

        except InvalidArgumentsException:
            self._print_usage()
            return

        diff = self._get_snippets()
        variable_list = self._get_vars()
        self._update_context(diff)
        self._handle_snippets(diff, variable_list)
