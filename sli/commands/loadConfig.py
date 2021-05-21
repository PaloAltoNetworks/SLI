from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection
import requests
from lxml import etree
import os


class LoadConfig(BaseCommand):
    sli_command = "load_config"
    short_desc = "Load an XML configuration file onto an NGFW as candidate"
    no_skillet = True
    help_text = """
        Usage:
            sli load_config config_file.xml
    """

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):

        if not len(self.args) == 1:
            print(self.help_text)
            return
        file_name = self.args[0]
        if not file_name.endswith(".xml"):
            print("Target file must be an xml file")
            return

        # Push configuration file to the device
        print(f"Loading configuration file {file_name}")
        with open(file_name, 'rb') as f:
            params = {
                "type": "import",
                "category": "configuration",
                "key": pan.xapi.api_key
            }
            r = requests.post(
                f"https://{self.sli.context['TARGET_IP']}/api",
                params=params,
                verify=False,
                files={"file": f}
            )
        if not r.status_code == 200:
            print(f"Unable to load configuration on firewall, {r.status_code} received")
        print(f"Loaded {file_name}")
        xml = etree.fromstring(r.text)
        if not xml.xpath("@status")[0].lower() == "success":
            err = "".join(xml.xpath("//msg/text()"))
            if not len(err):
                err = "".join(xml.xpath("//line/text()"))
            if len(err):
                print(f"Error from device: \n{err}")
            else:
                print("Unable to push configuration to device")
            return

        # Configuration file is on device, load it as candidate config
        file_name = file_name.replace('/', os.path.sep).split(os.path.sep)[-1]
        xml = f"<load><config><from>{file_name}</from></config></load>"
        r = pan.execute_op(xml)
        xml = etree.fromstring(r)
        msg = xml.xpath("//line/text()")[0]
        if len(msg):
            print(msg)
        else:
            print("Unable to retrieve op results from device")
