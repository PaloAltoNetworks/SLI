import yaml
import os
from os.path import expanduser
from panforge import Report

def print_table(objs, defs):
    """
    Print a formatted table with left justified columns
    """

    def get_cell(text, max):
        if text is None:
            return " " * max
        return f"  {text + ' ' * (max - len(text))}  "

    # Calculate max width of each column
    cols = {k: {"width": len(k)} for k in defs}
    for o in objs:
        for k in defs:
            if "." in defs[k]:
                text = jmespath.search(defs[k], o)
            else:
                text = o[defs[k]]
            if text is None:
                continue
            if len(text) > cols[k]["width"]:
                cols[k]["width"] = len(text)
    # Print headers
    header = "".join([get_cell(x, cols[x]["width"]) for x in cols])
    print(header)
    print("-" * len(header))

    # Print data
    for o in objs:
        row = ""
        for k in defs:
            if "." in defs[k]:
                text = jmespath.search(defs[k], o)
            else:
                text = o[defs[k]]
            row += get_cell(text, cols[k]["width"])
        print(row)

def load_config_file(fileName):
    """
    Attempt to load configuration file, return empty dict if not specified
    """
    if not fileName:
        return {}
    if not os.path.exists(fileName):
        print('Specified configuration file not found.')
        exit(1)
    with open(fileName, 'r') as f:
        return yaml.safe_load(f)

def generate_report(out_file, data, report_dir, header=None):
    """
    Generate a panforge report at 'out_file' from source 'data' using 'report_dir'
    as the root reporting directory for panforge
    """
    if not os.path.exists(report_dir):
        print(f'Could not generate report, source directory {report_dir} not present')
        return
    report = Report(report_dir)
    if header:
        report.load_header(header)
    report.load_data(data)
    report_html = report.render_html()
    with open(out_file, 'w') as f:
        f.write(report.html)
    print(f'Report written to {out_file}')

def input_yes_no(prompt, ret_value, ret_false=None):
    """
    Simple wrapper for asking user yes no questions until an acceptable answer
    is received, returns ret_value if yes, ret_false if no
    """
    while True:
        user_input = input(prompt + ' (y/n): ')
        if user_input.lower() in ('y', 'yes'):
            return ret_value
        if user_input.lower() in ('n', 'no'):
            return ret_false
        print('Please input either y or n')

def get_variable_input(var):
    """
    Get input from user in reference to var, being a skillet variable object
    """
    type_hint = var.get('type_hint')
    name = var.get('name')
    description = var.get('description')
    if not name:
        raise ValueError(f'Input variable missing name')
    ret_dict = {}

    if type_hint == 'checkbox':
        cbx_list = var.get('cbx_list', [])
        desc = description if description else name
        print(f"\n{desc}\n{'-'*len(desc)}\n")

        # Get inputs from user until user confirms they are ok
        confirmed = False
        input_list = []
        while not confirmed:
            input_list.clear()
            for cbx in cbx_list:
                input_value = input_yes_no(cbx['key'], cbx['value'])
                if input_value:
                    input_list.append(input_value)

            # Display all inputs
            check = []
            for cbx in cbx_list:
                check.append({'name':cbx['key'], 'value': 'Yes' if cbx['value'] in input_list else 'No'})
            print('')
            print_table(check, {'Input': 'name', 'Value': 'value'})
            print('')
            if input_yes_no('Are These answers ok?', True):
                confirmed = True

        # Put inputs inside ret_dict and return
        ret_dict[name] = input_list

        return ret_dict

    raise ValueError(f'Unsupported input variable type of {type_hint} in var {name}')

def expandedHomePath(directory):
    """Returns a local OS formatted directory string"""
    return expanduser("~") + os.path.sep + os.path.sep.join(directory.strip().split('/'))