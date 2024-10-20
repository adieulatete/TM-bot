from jinja2 import Environment, FileSystemLoader

from . import config

# Setting up Jinja2
template_loader = FileSystemLoader(searchpath=config.TEMPLATES_DIR)
env = Environment(loader=template_loader)

def render_message(template_name, **kwargs):
    """Render a message using a Jinja2 template."""
    template = env.get_template("messages.j2")
    macro = getattr(template.module, template_name)
    return macro(**kwargs) 
