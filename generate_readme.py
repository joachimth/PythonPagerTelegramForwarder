import yaml
from jinja2 import Environment, FileSystemLoader

# Load data from YAML file
with open("appdefs.yml", 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)

# Configure Jinja and ready the template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('readme_templateV01.md')

# Process the template to produce our final text.
output_text = template.render(cfg)

# Write to README.md
with open("README.md", "w") as fh:
    fh.write(output_text)
