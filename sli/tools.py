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
    desc = var.get('description', name)
    if not name:
        raise ValueError(f'Input variable missing name')
    ret_dict = {}

    if type_hint == 'checkbox':
        cbx_list = var.get('cbx_list', [])
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

        # Add input to ret_dict
        ret_dict[name] = input_list

    elif type_hint=='dropdown':
        print(f"\n{desc}")
        i = 1
        for val in var['dd_list']:
            print(f"   {i}. {var['dd_list'][i-1]['key']}")
            i += 1
        valid_response = False
        while not valid_response:
            response = input("Please enter line number of selection: ")
            if response.isdigit() and not '.' in response:
                response_index =  int(response) - 1
                if response_index < 0 or response_index > len(var['dd_list']):
                    print(f"Please input a number between 1 and {len(var['dd_list'])}")
                else:
                    value = var['dd_list'][response_index]['value']
                    ret_dict[name] = value
                    valid_response = True
            else:
                print("Please input a number")

    elif type_hint=='list':
        valid_response = False
        while not valid_response:
            response = input(f"{desc} (comma seperated list): ")
            rl = [x.strip() for x in response.split(',') if len(x)]
            print("You entered:")
            if len(rl):
                for item in rl:
                    print(f"  - {item}")
            else:
                print("[]")

            #if input_yes_no("Are these values correct?", True):
            ret_dict[name] = rl
            valid_response = True


    elif type_hint=='text':
        ret_dict[name] = input(f"{var.get('description', name)}: ")

    elif type_hint=='hidden':
        ret_dict[name] = var.get('default')

    else:
        raise ValueError(f'Unsupported input variable type of {type_hint} in var {name}')

    return ret_dict

def expandedHomePath(directory):
    """Returns a local OS formatted directory string"""
    return expanduser("~") + os.path.sep + os.path.sep.join(directory.strip().split('/'))