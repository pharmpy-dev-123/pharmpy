"""
=======================
Execution Run Directory
=======================

.. todo:: Create a derived class at :class:`pharmpy.api_nonmem.execute.run_directory`.

This module defines the :class:`.RunDirectory` class, which initialization creates a filesystem
directory that :class:`~pharmpy.tool.Tool` instances and :class:`~pharmpy.model.Model` methods can
utilize for input->output during evaluation, estimation & simulation tasks.

.. testcode::
    :pyversion: > 3.6

    from pharmpy.workflows import RunDirectory

Definitions
-----------
"""

import itertools
import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory


class RunDirectory:
    """Execution run directory.
    Will contain input/output files for a job and handle cleanup. Is generated by
    :class:`~.engine.Engine` class (and tools).

    Args:
        parent: Parent (directory). If None, a temporary directory is created.
        name: (Base) name of directory (when parent is not None). (This) class name if False.
        template: Template for directory naming. '%s' substitutes for 'name' and '%d' for an int.

    Raises:
        FileExistsError: Constructed name is occupied (and '%d' is missing from 'template').

    Temporary directories are removed entirely on garbage collection. Default 'template' is
    '%s_dir%d'. First number in range (1, ∞) with a unique filesystem path is used.

    .. note::
        Expects caller to set :attr:`model` to iniate a data structure + file copy (if file
        representation is not already in directory), and *then execute*. Example::

            # run dir "takes" copy of model
            pheno = pysn.Model('pheno_real.mod')
            run_dir = RunDirectory('some/working/dir/', 'example_tool')
            run_dir.model = pheno

            # 'pheno' at original location & 'run_dir.model' copy in dir tree (safe to execute)
            run_dir.model != pheno
            run_dir.model.path != pheno.path
            run_dir.model.execute.estimate()
    """

    cleanlevel = 0
    """The active clean *level* of this directory."""

    def __init__(self, parent=None, name=None, template='%s_dir%d'):
        if not name:
            name = self.__class__.__name__

        if parent is None:
            self._tempdir = TemporaryDirectory(prefix='%s.' % (name,) if name else None)
            path = Path(self._tempdir.name)
        else:
            head = Path(str(parent)).resolve()
            if re.search(r'(?<!%)%d', template):
                for num in itertools.count(1):
                    path = head / (template % (name, num))
                    if not path.exists():
                        break
            else:
                path = head / (template % name)
            path.mkdir(exist_ok=False)

        self.path = path
        self.template = template
        self._model = None
        self._jobs = list()

    @property
    def name(self):
        """The name of this directory."""
        return self.path.name

    @property
    def model(self):
        """The current, main model of the directory (i.e. the target of execution)."""
        return self._model

    @model.setter
    def model(self, model):
        path = self.path / Path(model.path).name
        if path.is_file():
            raise ValueError('Model already exists, at: %r' % str(path))
        self._model = model.copy(dest=path)

    def bind_job(self, job):
        self._jobs += [job]

    def clean_config(self, level, patterns, rm_dirs=False):
        """Configure a cleanlevel.

        Args:
            level: The cleanup level.
            patterns: List of path-globbing patterns (removal targets).
            rm_dirs: Also delete non-empty directories matching 'patterns'?

        Level 0 should be reserved as the no-op.
        """
        num_prev = len(self.cleanlevels)
        if num_prev <= level:
            self._cleanlevels += [list() for _ in range(1 + num_prev - level)]
        self._cleanlevels[level] = {'glob': list(patterns), 'rm_dirs': bool(rm_dirs)}

    @property
    def cleanlevels(self):
        """The active cleanlevel *definitions* of this directory."""
        try:
            levels = self._cleanlevels
        except AttributeError:
            levels = self._cleanlevels = [[]]
        return levels

    def cleanup(self, level=None):
        """Delete files/dirs up to clean level (is run after completion).

        Args:
            level: The clean level to target. If None, (class) default clean level is used.
        """

        log = logging.getLogger(__name__)
        for job in self._jobs:
            if not job.done:
                log.warning('Job still running (%r): blocking cleanup of %r!', job, self)
                job.wait()

        if level is None:
            level = self.cleanlevel
        levels = self.cleanlevels[:(1+level)]
        for child in self.path.iterdir():
            clean = dict()
            for level in levels:
                if not level:
                    continue
                if any(child.match(glob) for glob in level['glob']):
                    clean = level
                    break
            if not clean:
                continue

            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir() and clean['rm_dirs']:
                for rchild in child.iterdir():
                    rchild.unlink()
                try:
                    rchild.rmdir()
                except OSError:
                    pass

    def __repr__(self):
        args = ['%r' % str(self.path.parent), '%r' % str(self.name)]
        if self.template != '%s_dir%d':
            args += ['%r' % self.template]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

    def __str__(self):
        return str(self.path)

    def __del__(self):
        if self.path.exists():
            self.cleanup()
