#
# -*- coding: utf-8-*-
# Herumgebastel
#

import json
from string import Template

with open('current.json', 'r') as f:
    data = json.load(f)

# 1. building pure Text Output

text_msg = list()
text_data_template = Template("$result, $time, $message")
for url, details in data.items():
    line = url + " | " + text_data_template.substitute(details)
    text_msg.append(line)

text_out_msg = "\n".join(text_msg)

print(text_out_msg)

# 2. building HTML output
html_data_line = Template('<tr><td><a href="$url" target="_blank">$url</a></td>$details</tr>')
html_data_template_ok = Template('<td style="text-align: center; color: #4CAF50; font-weight: bold;">$result</td><td>$time</td><td>$message</td>')
html_data_template_fail = Template('<td style="text-align: center; color: #FF0000; font-weight: bold;">$result</td><td>$time</td><td>$message</td>')

html_lines = list()
for url, details in data.items():
    if details['result'] == 'SUCCESS':
        html_details = html_data_template_ok.substitute(details)
    else:
        html_details = html_data_template_fail.substitute(details)
    line_data = {'url': url, 'details': html_details}
    html_lines.append(html_data_line.substitute(line_data))

html_inner = '\n'.join(html_lines)
html_outer = '''
<!DOCTYPE html>
<html>
<head>
  <title>process status</title>
  <style>
    body {{
    font-family: Verdana, Sans-Serif;
    font-size: small;
  }}
    table {{
      border-collapse: collapse;
   }}
    table, th, td {{
      border: 1px solid black;
      margin: 5px;
      padding-left: 5px;
      padding-right: 5px;
    }}
    tr:nth-child(even) {{background-color: #f2f2f2;}}
    tr:hover {{background-color: #e1e1e1;}}
    th {{
      background-color: #4CAF50;
      color: white;
  }}
  </style>
</head>
<body>
  <h3>ISC PMON process monitoring</h3>
  <table>
    <thead>
      <tr>
        <th>URL</th><th>Status</th><th>Time</th><th>Message</th>
      </tr>
      {0}
    </thead>
  </table>
  <p style="text-align: center; font-size: xx-small;">
    &copy; 2018 ISC Clemenz &amp; Weinbrecht GmbH
  </p>
</body>
</html>
'''.strip().format(html_inner)

with open('out.html', 'w') as h:
    h.write(html_outer)



