# SPDX-FileCopyrightText: 2022 UChicago Argonne, LLC
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from pathlib import Path
import shutil
from typing import Optional

from .database import Database
from .fileutils import cd_tmpdir
from .parameters import Parameters
from .results import Results
from .template import TemplateModelBuilder


class Plugin(ABC):
    """Class defining the Plugin interface"""

    @abstractmethod
    def prerun(self, params):
        ...

    @abstractmethod
    def run(self):
        ...

    @abstractmethod
    def postrun(self, params) -> Results:
        ...

    @staticmethod
    def _get_unique_dir(path: Path, name: str) -> Path:
        if not (path / name).exists():
            return path / name

        # Try adding number as suffix
        i = 1
        while True:
            unique_name = f"{name}_{i}"
            if not (path / unique_name).exists():
                return path / unique_name
            i += 1

    def workflow(self, params: Parameters, name='Workflow') -> Results:
        """Run the complete workflow for the plugin

        Parameters
        ----------
        params
            Parameters used in generating inputs
        name
            Unique name for workflow

        Returns
        -------
        Results from running workflow
        """
        db = Database()

        with cd_tmpdir():
            # Run workflow in temporary directory
            self.prerun(params)
            self.run()
            result = self.postrun(params)

            # Create new directory for results and move files there
            workflow_path = self._get_unique_dir(db.path, name)
            workflow_path.mkdir()
            try:
                result.move_files(workflow_path)
            except Exception:
                # If error occurred, make sure we remove results directory so it
                # doesn't pollute database
                shutil.rmtree(workflow_path)
                raise

        # Add result to database
        db.add_result(result)

        return result


class TemplatePlugin(Plugin):
    """Plugin that relies on generating a template file

    Parameters
    ----------
    template_file
        Path to template file
    """
    def  __init__(self, template_file: str):
        self.model_builder = TemplateModelBuilder(template_file)

    def prerun(self, params: Parameters, filename: Optional[str] = None):
        """Render the template based on model parameters

        Parameters
        ----------
        params
            Parameters used to render template
        filename
            Keyword arguments passed to the
        """
        # Render the template
        self.model_builder(params, filename=filename)
