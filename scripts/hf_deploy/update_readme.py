with open('README.md', 'r') as f:
    content = f.read()

yaml_frontmatter = """---
title: Garda JKN BPJS
emoji: ⚕️
colorFrom: green
colorTo: blue
sdk: streamlit
app_file: app.py
pinned: false
---
"""

if not content.startswith('---'):
    with open('README.md', 'w') as f:
        f.write(yaml_frontmatter + content)
