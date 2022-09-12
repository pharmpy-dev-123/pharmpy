import importlib
import inspect
from datetime import datetime
from pathlib import Path

import pharmpy.results
import pharmpy.tools.modelfit
from pharmpy.model import Model
from pharmpy.modeling.common import copy_model, read_model_from_database
from pharmpy.tools.psn_helpers import create_results as psn_create_results
from pharmpy.utils import normalize_user_given_path
from pharmpy.workflows import execute_workflow, split_common_options
from pharmpy.workflows.model_database import LocalModelDirectoryDatabase, ModelDatabase
from pharmpy.workflows.tool_database import ToolDatabase


def fit(models, tool=None):
    """Fit models.

    Parameters
    ----------
    models : list
        List of models or one single model
    tool : str
        Estimation tool to use. None to use default

    Return
    ------
    Model
        Reference to same model

    Examples
    --------
    >>> from pharmpy.modeling import load_example_model
    >>> from pharmpy.tools import fit
    >>> model = load_example_model("pheno")
    >>> fit(model)      # doctest: +SKIP

    See also
    --------
    run_tool

    """
    if isinstance(models, Model):
        models = [models]
        single = True
    else:
        single = False
    kept = []
    # Do not fit model if already fit
    for model in models:
        try:
            db_model = read_model_from_database(model.name, database=model.database)
        except (KeyError, AttributeError):
            db_model = None
        if (
            db_model
            and db_model.modelfit_results is not None
            and db_model == model
            and model.has_same_dataset_as(db_model)
        ):
            model.modelfit_results = db_model.modelfit_results
        else:
            kept.append(model)
    if kept:
        run_tool('modelfit', kept, tool=tool)
    if single:
        return models[0]
    else:
        return models


def create_results(path, **kwargs):
    """Create/recalculate results object given path to run directory

    Parameters
    ----------
    path : str, Path
        Path to run directory
    kwargs
        Arguments to pass to tool specific create results function

    Returns
    -------
    Results
        Results object for tool

    Examples
    --------
    >>> from pharmpy.tools import create_results
    >>> res = create_results("frem_dir1")   # doctest: +SKIP

    See also
    --------
    read_results

    """
    path = normalize_user_given_path(path)
    res = psn_create_results(path, **kwargs)
    return res


def read_results(path):
    """Read results object from file

    Parameters
    ----------
    path : str, Path
        Path to results file

    Return
    ------
    Results
        Results object for tool

    Examples
    --------
    >>> from pharmpy.tools import read_results
    >>> res = read_resuts("results.json")     # doctest: +SKIP

    See also
    --------
    create_results

    """
    path = normalize_user_given_path(path)
    res = pharmpy.results.read_results(path)
    return res


def run_tool(name, *args, **kwargs):
    """Run tool workflow

    Parameters
    ----------
    name : str
        Name of tool to run
    args
        Arguments to pass to tool
    kwargs
        Arguments to pass to tool

    Return
    ------
    Results
        Results object for tool

    Examples
    --------
    >>> from pharmpy.modeling import *
    >>> model = load_example_model("pheno")
    >>> from pharmpy.tools import run_tool # doctest: +SKIP
    >>> res = run_tool("resmod", model)   # doctest: +SKIP

    """
    tool = importlib.import_module(f'pharmpy.tools.{name}')
    common_options, tool_options = split_common_options(kwargs)

    tool_params = inspect.signature(tool.create_workflow).parameters
    tool_metadata = _create_metadata_tool(name, tool_params, tool_options, args)

    wf = tool.create_workflow(*args, **tool_options)

    dispatcher, database = _get_run_setup(common_options, wf.name)
    setup_metadata = _create_metadata_common(common_options, dispatcher, database, wf.name)
    tool_metadata['common_options'] = setup_metadata
    database.store_metadata(tool_metadata)

    if name != 'modelfit':
        _store_input_models(list(args) + list(kwargs.items()), database)

    res = execute_workflow(wf, dispatcher=dispatcher, database=database)

    tool_metadata['stats']['end_time'] = _now()
    database.store_metadata(tool_metadata)

    return res


def _store_input_models(args, database):
    input_models = _get_input_models(args)

    if len(input_models) == 1:
        _create_input_model(input_models[0], database)
    else:
        for i, model in enumerate(input_models, 1):
            _create_input_model(model, database, number=i)


def _get_input_models(args):
    input_models = []
    for arg in args:
        if isinstance(arg, Model):
            input_models.append(arg)
        else:
            arg_as_list = [a for a in arg if isinstance(a, Model)]
            input_models.extend(arg_as_list)
    return input_models


def _create_input_model(model, tool_db, number=None):
    input_name = 'input_model'
    if number is not None:
        input_name += str(number)
    model_copy = copy_model(model, input_name)
    with tool_db.model_database.transaction(model_copy) as txn:
        txn.store_model()
        txn.store_modelfit_results()


def _now():
    return datetime.now().astimezone().isoformat()


def _create_metadata_tool(tool_name, tool_params, tool_options, args):
    # FIXME: add config file dump, estimation tool etc.
    tool_metadata = {
        'pharmpy_version': pharmpy.__version__,
        'tool_name': tool_name,
        'stats': {'start_time': _now()},
        'tool_options': dict(),
    }

    for i, p in enumerate(tool_params.values()):
        # Positional args
        if p.default == p.empty:
            try:
                name, value = p.name, args[i]
            except IndexError:
                try:
                    name, value = p.name, tool_options[p.name]
                except KeyError:
                    raise ValueError(f'{tool_name}: \'{p.name}\' was not set')
        # Named args
        else:
            if p.name in tool_options.keys():
                name, value = p.name, tool_options[p.name]
            else:
                name, value = p.name, p.default
        if isinstance(value, Model):
            value = str(value)  # FIXME: better model representation
        tool_metadata['tool_options'][name] = value

    return tool_metadata


def _create_metadata_common(common_options, dispatcher, database, toolname):
    setup_metadata = dict()
    setup_metadata['dispatcher'] = dispatcher.__name__
    # FIXME: naming of workflows/tools should be consistent (db and input name of tool)
    setup_metadata['database'] = {
        'class': type(database).__name__,
        'toolname': toolname,
        'path': str(database.path),
    }
    for key, value in common_options.items():
        if key not in setup_metadata.keys():
            if isinstance(value, Path):
                value = str(value)
            setup_metadata[str(key)] = value

    return setup_metadata


def _get_run_setup(common_options, toolname):
    try:
        dispatcher = common_options['dispatcher']
    except KeyError:
        from pharmpy.workflows import default_dispatcher

        dispatcher = default_dispatcher

    try:
        database = common_options['database']
    except KeyError:
        from pharmpy.workflows import default_tool_database

        if 'path' in common_options.keys():
            path = common_options['path']
        else:
            path = None
        database = default_tool_database(
            toolname=toolname, path=path, exist_ok=common_options.get('resume', False)
        )  # TODO: database -> tool_database

    return dispatcher, database


def retrieve_models(source, names=None):
    """Retrieve models after a tool runs

    Any models created and run by the tool can be
    retrieved.

    Parameters
    ----------
    source : str, Path, Results, ToolDatabase, ModelDatabase
        Source where to find models. Can be a path (as str or Path), a results object, or a
        ToolDatabase/ModelDatabase
    names : list
        List of names of the models to retrieve or None for all

    Return
    ------
    list
        List of retrieved model objects
    """
    if isinstance(source, Path) or isinstance(source, str):
        path = Path(source)
        # FIXME: Should be using metadata to know how to init databases
        db = LocalModelDirectoryDatabase(path / 'models')
    elif isinstance(source, pharmpy.results.Results):
        if hasattr(source, 'tool_database'):
            db = source.tool_database.model_database
        else:
            raise ValueError(
                f'Results type \'{source.__class__.__name__}\' does not serialize tool database'
            )
    elif isinstance(source, ToolDatabase):
        db = source.model_database
    elif isinstance(source, ModelDatabase):
        db = source
    else:
        raise NotImplementedError(f'Not implemented for type \'{type(source)}\'')
    if names is None:
        names = db.list_models()
    models = [db.retrieve_model(name) for name in names]
    return models


def retrieve_final_model(res):
    return retrieve_models(res, names=[res.final_model_name])[0]
