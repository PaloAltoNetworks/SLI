import os
from os.path import expanduser
from panforge import Report
from getpass import getpass
import socket
from jinja2 import Environment
import jmespath


def get_var(var, args, context):
    """Get a var by searching args and the context, else ask the user"""
    args = {x.split('=')[0]: x.split('=')[1] for x in args if '=' in x}
    if var['name'] in args:
        # First order of preference is to use a CLI provided parameter
        context[var['name']] = args[var['name']]
    else:
        # If input has not yet been supplied, get it from the user
        context.update(get_variable_input(var, context))


def render_template(template_text, context):
    """Render a template loaded from a string with an appropriate environment"""
    env = Environment(extensions=['jinja2_ansible_filters.AnsibleCoreFiltersExtension'])
    return env.from_string(template_text).render(context)


def render_expression(expression, context):
    """Shortcut to render an expression, adding {{}} brackets to a template"""
    return render_template("{{" + str(expression) + "}}", context)


def is_ip(ip):
    """
    Return True if either an IPv4 or IPV6 address
    """
    for family in socket.AF_INET, socket.AF_INET6:
        try:
            socket.inet_pton(family, ip)
            return True
        except Exception:
            pass
    return False


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
        f.write(report_html)
    print(f'Report written to {out_file}')


def input_yes_no(prompt, ret_value, ret_false=None, default=None):
    """
    Simple wrapper for asking user yes no questions until an acceptable answer
    is received, returns ret_value if yes, ret_false if no
    """
    default_str = " (y/n): "
    if isinstance(default, str):
        default_yes = True if default.lower() in ("y", "yes") else False
        default_str = f" (y/n default: {'yes' if default_yes else 'no'}): "
    while True:
        user_input = input(prompt + default_str)
        if not len(user_input) and default is not None:
            return ret_value if default_yes else ret_false
        if user_input.lower() in ('y', 'yes'):
            return ret_value
        if user_input.lower() in ('n', 'no'):
            return ret_false
        print('Please input either y or n')


def check_default_empty(default):
    """Helper function to validate if a default parameter is empty based on type"""
    if isinstance(default, str) or isinstance(default, list):
        return len(default) == 0
    elif isinstance(default, int):
        return False
    elif isinstance(default, dict):
        return len(default.keys()) == 0


def get_variable_input(var, context):
    """
    Get input from user in reference to var, being a skillet variable object
    """
    type_hint = var.get('type_hint')
    name = var.get('name')
    desc = var.get('description', name)

    # First get a default from the context, otherwise use the skillet definition
    default = context.get(name, "")
    default_is_empty = check_default_empty(default)

    if default_is_empty:
        default = var.get("default", "")
        default_is_empty = check_default_empty(default)

    default_str = f"({default})" if not default_is_empty else ""
    if not name:
        raise ValueError('Input variable missing name')

    ret_dict = {}

    # Check for a toggle hint and return if not applicable
    if 'toggle_hint' in var:
        if not var['toggle_hint']['value'] == context.get(var['toggle_hint'].get('source')):
            return ret_dict

    if type_hint == 'checkbox':

        if 'source' in var:
            raw_dd_list = context.get(var["source"], [])
            if not isinstance(raw_dd_list, list):
                raw_dd_list = [raw_dd_list]

            cbx_list = [{"key": x, "value": x} for x in raw_dd_list]

        else:
            cbx_list = var.get('cbx_list', [])

        print(f"\n{desc}\n{'-'*len(desc)}\n")

        # Get inputs from user until user confirms they are ok
        confirmed = False
        input_list = []
        while not confirmed:
            input_list.clear()
            for cbx in cbx_list:
                default_result = None
                if isinstance(default, list):
                    default_result = "y" if cbx["value"] in default else "n"
                input_value = input_yes_no(cbx['key'], cbx['value'], default=default_result)
                if input_value:
                    input_list.append(input_value)

            # Display all inputs
            check = []
            for cbx in cbx_list:
                check.append({'name': cbx['key'], 'value': 'Yes' if cbx['value'] in input_list else 'No'})
            print('')
            print_table(check, {'Input': 'name', 'Value': 'value'})
            print('')
            if input_yes_no('Are These answers ok?', True):
                confirmed = True

        # Add input to ret_dict
        ret_dict[name] = input_list

    elif type_hint == 'dropdown':
        print(f"\n{desc}")

        if 'source' in var:
            raw_dd_list = context.get(var["source"], [])
            if not isinstance(raw_dd_list, list):
                raw_dd_list = [raw_dd_list]

            dd_list = [{"key": x, "value": x} for x in raw_dd_list]
        else:
            dd_list = var.get('dd_list', [])

        for i in range(0, len(dd_list)):
            print(f"   {i + 1}. {dd_list[i]['key']}")

        valid_response = False
        while not valid_response:
            default_key = ""
            if not default_is_empty:
                default_dd = [x for x in dd_list if x['value'] == default]
                if not len(default_dd):
                    # If there is a default from the context and it's not an option, clear the default
                    default = ""
                else:
                    default_dd = default_dd[0]
                    default_key = f"({default_dd['key']})"
            response = input(f"Please enter line number of selection {default_key}: ")
            if not len(response) and not default_is_empty:
                # Assume default
                response = default_dd["value"]
                valid_response = True
            elif response.isdigit() and '.' not in response:
                response_index = int(response) - 1
                if response_index < 0 or response_index >= len(dd_list):
                    print(f"Please input a number between 1 and {len(dd_list)}")
                else:
                    value = dd_list[response_index]['value']
                    ret_dict[name] = value
                    valid_response = True
            else:
                print("Please input a number")

    elif type_hint == 'list':
        valid_response = False
        if isinstance(default, list):
            if not default_is_empty:
                print("\nDefault list")
                for item in default:
                    print(f"  - {item}")
        while not valid_response:
            response = input(f"{desc} (comma seperated list, blank to accept default): ")
            if len(response):
                rl = [x.strip() for x in response.split(',') if len(x)]
            else:
                rl = default
                valid_response = True
                continue
            print("You entered:")
            if len(rl):
                for item in rl:
                    print(f"  - {item}")
            else:
                print("[]")

            if input_yes_no("Are these values correct?", True):
                ret_dict[name] = rl
                valid_response = True

    elif type_hint == 'ip_address':
        valid_response = False
        while not valid_response:
            response = input(f"{var.get('description', name)} {default_str}: ")
            if not len(response):
                response = default
            if is_ip(response):
                valid_response = True
            else:
                print("Invalid IP address.")
        ret_dict[name] = response

    elif type_hint == 'password':
        valid_response = False
        while not valid_response:
            password = getpass(f"{var.get('description', name)}: ")
            confirm = getpass(f"Confirm - {var.get('description', name)}: ")
            if password == confirm:
                valid_response = True
            else:
                print("Password and confirm do not match!")
        ret_dict[name] = password

    elif type_hint == 'text':

        response = input(f"{var.get('description', name)} {default_str}: ")
        if not len(response) and not default_is_empty:
            ret_dict[name] = default
        else:
            ret_dict[name] = response

    elif type_hint == 'hidden':
        ret_dict[name] = default

    elif type_hint == 'fqdn_or_ip':
        response = input(f"{var.get('description', name)} {default_str}: ")
        if not len(response) and not default_is_empty:
            ret_dict[name] = default
        else:
            ret_dict[name] = response

    else:
        raise ValueError(f'Unsupported input variable type of {type_hint} in var {name}')

    return ret_dict


def expandedHomePath(directory):
    """Returns a local OS formatted directory string"""
    return expanduser("~") + os.path.sep + os.path.sep.join(directory.strip().split('/'))
