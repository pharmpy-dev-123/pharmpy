import shutil
import tempfile
from pathlib import Path

import pytest

from pharmpy.internals.fs.cwd import chdir
from pharmpy.model import Model
from pharmpy.tools import fit


@pytest.fixture(scope='session')
def start_model(testdata):
    tempdir = Path(tempfile.mkdtemp())
    with chdir(tempdir):
        shutil.copy2(testdata / 'nonmem' / 'models' / 'mox2.mod', tempdir)
        shutil.copy2(testdata / 'nonmem' / 'models' / 'mox_simulated_normal.csv', tempdir)
        model_start = Model.create_model('mox2.mod')
        model_start.datainfo = model_start.datainfo.derive(
            path=tempdir / 'mox_simulated_normal.csv'
        )
        fit(model_start)
    return model_start


@pytest.fixture(scope='session')
def model_count():
    def _model_count(rundir: Path):
        return sum(
            map(
                lambda path: 0 if path.name in ['.lock', '.datasets', 'input_model'] else 1,
                ((rundir / 'models').iterdir()),
            )
        )

    return _model_count
