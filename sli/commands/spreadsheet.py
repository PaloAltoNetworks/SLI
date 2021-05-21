from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

from jinja2 import Environment, meta
import xlsxwriter
import os

"""
Generate output of a panos skillet and write to file
"""


class SpreadsheetCommand(BaseCommand):
    sli_command = 'spreadsheet'
    short_desc = 'Generate a user editable spreadsheet from a template'
    suppress_output = True
    help_text = """

        Load a template skillet, and convert it to a spreadsheet a user
        can edit to manipulate the set commands output

        Usage:
            sli spreadsheet -n template_skillet -o output_directory
"""

    @require_single_skillet
    @require_skillet_type('template')
    def run(self):

        out_directory = self.sli.options.get("out_file", "")

        for snippet in self.sli.skillet.get_snippets():

            # Find out_file
            out_file = snippet.file + ".xlsx"
            file_split = snippet.file.split(".")
            if len(file_split) > 1:
                out_file = out_directory + ".".join(file_split[:-1]) + ".xlsx"

            # Verify input file is a set command template
            with open(self.sli.skillet.path + os.path.sep + snippet.file, "r") as f:
                contents = f.readlines()
            i = 1
            for line in [x for x in contents if len(x.strip()) > 1]:
                if len(line) and not any([line.strip().startswith(x) for x in ["set", "delete", "#"]]):
                    print(f"Problem at line {i}\n  {line.strip()}")
                    print("Invalid file, only configuration mode commands and comments starting with # are allowed")
                    return
                i += 1

            workbook = xlsxwriter.Workbook(out_file)

            # add columns and format width
            worksheet_values = workbook.add_worksheet("values")
            worksheet_values.set_column(0, 0, 30)
            worksheet_values.set_column(1, 1, 30)
            worksheet_set = workbook.add_worksheet("set commands")

            # Add a bold format to use to highlight cells.
            bold = workbook.add_format({"bold": 1})

            # positional list to map variables into formula
            # padded since variables start at row 2 with zero offset
            variable_list = ['first row', 'second row']

            worksheet_values.write(0, 0, 'Variable Name', bold)
            worksheet_values.write(0, 1, 'Variable Value', bold)

            # Add variables to workbook
            row = 1
            for variable in self.sli.skillet.variables:
                worksheet_values.write(row, 0, variable['name'])
                worksheet_values.write(row, 1, variable['default'])
                worksheet_values.write(row, 2, variable['description'])
                variable_list.append(variable['name'])
                row += 1
            row = 1

            # Add set commands to workbook
            for line in contents:

                # Read the line and create a variable set
                env = Environment()
                var_set = sorted(meta.find_undeclared_variables(env.parse(line)))

                # Check if line has a single variable
                if len(var_set) == 1:
                    # Replace quote with 2xquotes to be excel friendly
                    line = line.replace('"', '""').strip()
                    var_name = var_set[0]
                    jinja_var = "{{ " + var_name + " }}"
                    cell_pos = variable_list.index(var_name)

                    # Formula format  = =SUBSTITUTE("set deviceconfig system dns-setting servers primary {0}", "{0}", '0-Config Values'!B21)
                    form_line = f'=SUBSTITUTE("{line}", "{jinja_var}", \'values\'!B{cell_pos})'
                    worksheet_set.write(row, 0, form_line)

                # Check if line has 2 variables when requires nested SUBSTITUTEs
                elif len(var_set) == 2:
                    # Replace quote with 2xquotes to be excel friendly
                    line = line.replace('"', '""').strip()
                    var_name_0 = var_set[0]
                    jinja_var_0 = "{{ " + var_name_0 + " }}"
                    cell_pos_0 = variable_list.index(var_name_0)

                    var_name_1 = var_set[1]
                    jinja_var_1 = "{{ " + var_name_1 + " }}"
                    cell_pos_1 = variable_list.index(var_name_1)

                    # Inner is first substitute and all is nested substitute for excel
                    form_line_inner = f'SUBSTITUTE("{line}", "{jinja_var_0}", \'values\'!B{cell_pos_0})'
                    form_line_all = f'=SUBSTITUTE({form_line_inner}, "{jinja_var_1}", \'values\'!B{cell_pos_1})'
                    worksheet_set.write(row, 0, form_line_all)

                else:
                    # Replace quotes and also remove hidden quotes for standard non-formula cells
                    line = line.replace('"', '""').strip()
                    worksheet_set.write(row, 0, line)

                row += 1

            workbook.close()
            print(f"Workbook completed and saved to {out_file}")
