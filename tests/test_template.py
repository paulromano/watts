import ardent
import jinja2
import pytest


# Add run and postrun methods to TemplatePlugin so that it can be instantiated
class TemplatePlugin(ardent.TemplatePlugin):
    def run(self): ...
    def postrun(self, model): ...


def test_undefined_template(run_in_tmpdir):
    # Create template expecting variable
    with open('example_template', 'w') as fh:
        fh.write("{{ variable }}")

    # Create plugin to build template
    plugin = TemplatePlugin('example_template')

    # Passing model with 'variable' set should work
    model = ardent.Parameters(variable=1)
    plugin.prerun(model)
    with open('example_template.rendered', 'r') as fh:
        rendered = fh.read()
    assert rendered == '1'

    # Passing empty model should raise jinja2.UndefinedError
    empty_model = ardent.Parameters()
    with pytest.raises(jinja2.UndefinedError) as e:
        plugin.prerun(empty_model)
