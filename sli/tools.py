import yaml
import os
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
