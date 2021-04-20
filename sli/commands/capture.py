from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params

from skilletlib import SkilletLoader
import yaml
from jinja2 import Template

skillet_template = f"""
name: sli_capture
type: pan_validation
snippets:

  - name: test_filter
    cmd: parse
    variable: config
    outputs:
      - name: url_filtering_profiles
        capture_list: /config/devices/entry[@name='localhost.localdomain']/vsys/entry/profiles/url-filtering/entry

"""

class Capture(BaseCommand):

    sli_command = 'capture'
    short_desc = 'Capture a value based on object, list, or expression'
    no_skillet = True

    @require_ngfw_connection_params
    def run(self):
        """
        Usage: sli capture [type] [xpath] [store_as]
        """

        # Render validation skillet for execution
        skillet_yaml = Template(skillet_template).render()
        skillet_dict = yaml.load(skillet_yaml)
        sl = SkilletLoader()
        skillet = sl.create_skillet(skillet_dict)

        # Execute skillet and extract values from target 
        exe = skillet.execute(self.sli.context)

        # Print captured JSON 

        # Update context if using context
