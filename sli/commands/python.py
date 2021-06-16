from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.tools import hash_file_contents, hash_string
from .base import BaseCommand

import os
from pathlib import Path
from jinja2 import Template

docker_template = """FROM {{ base_image }}
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
        self.sli.skillet.execute(self.sli.context)
