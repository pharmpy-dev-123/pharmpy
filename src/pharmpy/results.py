from __future__ import annotations

import importlib
import json
import lzma
import re
from contextlib import closing
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Optional, Union

from pharmpy.deps import altair as alt
from pharmpy.deps import pandas as pd
from pharmpy.internals.immutable import Immutable
from pharmpy.model import Model, Results
from pharmpy.workflows import Log


def mfr(model: Model) -> ModelfitResults:
    res = model.modelfit_results
    assert isinstance(res, ModelfitResults)
    return res


class ResultsJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        # NOTE this hook will be called for every dict produced by the
        # base JSONDecoder. It will not be called on int, float, str, or list.
        module = None
        cls = None

        if '__module__' in obj:
            module = obj['__module__']
            del obj['__module__']

        if '__class__' in obj:
            cls = obj['__class__']
            del obj['__class__']

        # NOTE handling cls not None and module is None is kept for backwards
        # compatibility

        if cls is None and module is not None:
            raise ValueError('Cannot specify module without specifying class')

        if module is None or module.startswith('pandas.'):
            if cls == 'DataFrame':
                return pd.read_json(json.dumps(obj), orient='table', precise_float=True)
            elif cls == 'Series':
                name = None
                if '__name__' in obj:
                    name = obj['__name__']
                    del obj['__name__']
                series = pd.read_json(
                    json.dumps(obj), typ='series', orient='table', precise_float=True
                )
                if name is not None:
                    series.name = name
                return series

        if module is None or module.startswith('altair.'):
            if cls == 'vega-lite':
                return alt.Chart.from_dict(obj)

        if cls is not None and cls.endswith('Results'):
            if module is None:
                # NOTE kept for backwards compatibility: we guess the module
                # path based on the class name.
                tool_name = cls[:-7].lower()  # NOTE trim "Results" suffix
                tool_module = importlib.import_module(f'pharmpy.tools.{tool_name}')
                results_class = tool_module.results_class
            else:
                tool_module = importlib.import_module(module)
                results_class = getattr(tool_module, cls)

            return results_class.from_dict(obj)

        from pharmpy.workflows import LocalDirectoryToolDatabase, Log

        if cls is not None and cls == 'LocalDirectoryToolDatabase':
            return LocalDirectoryToolDatabase.from_dict(obj)

        if cls == 'PosixPath':
            return Path(obj)
        if cls == 'Log':
            return Log.from_dict(obj)

        return obj


def _is_likely_to_be_json(source: str):
    # NOTE Heuristic to determine if path or buffer: first non-space character
    # is '{'.
    match = re.match(r'\s*([^\s])', source)
    return match is not None and match.group(1) == '{'


def read_results(path_or_str: Union[str, Path]):
    if isinstance(path_or_str, str) and _is_likely_to_be_json(path_or_str):
        manager = closing(StringIO(path_or_str))
    else:
        path = Path(path_or_str)
        if path.is_dir():
            path /= 'results.json'

        if path.name.endswith('.xz'):
            manager = lzma.open(path, 'r', encoding='utf-8')
        else:
            manager = open(path, 'r')

    with manager as readable:
        return json.load(readable, cls=ResultsJSONDecoder)


@dataclass
class ModelfitResults(Results, Immutable):
    """Base class for results from a modelfit operation

    Attributes
    ----------
    name : str
        Name of model
    description : str
        Description of model
    correlation_matrix : pd.DataFrame
        Correlation matrix of the population parameter estimates
    covariance_matrix : pd.DataFrame
        Covariance matrix of the population parameter estimates
    information_matrix : pd.DataFrame
        Fischer information matrix of the population parameter estimates
    evaluation_ofv : float
        The objective function value as if the model was evaluated. Currently
        workfs for classical estimation methods by taking the OFV of the first
        iteration.
    individual_ofv : pd.Series
        OFV for each individual
    individual_estimates : pd.DataFrame
        Estimates for etas
    individual_estimates_covariance : pd.Series
        Estimated covariance between etas
    parameter_estimates : pd.Series
        Population parameter estimates
    parameter_estimates_iterations : pd.DataFrame
        All recorded iterations for parameter estimates
    parameter_estimates_sdcorr : pd.Series
        Population parameter estimates with variability parameters as standard deviations and
        correlations
    residuals: pd.DataFrame
        Table of various residuals
    predictions: pd.DataFrame
        Table of various predictions
    estimation_runtime : float
        Runtime for one estimation step
    runtime_total : float
        Total runtime of estimation
    standard_errors : pd.Series
        Standard errors of the population parameter estimates
    standard_errors_sdcorr : pd.Series
        Standard errors of the population parameter estimates on standard deviation and correlation
        scale
    relative_standard_errors : pd.Series
        Relative standard errors of the population parameter estimates
    termination_cause : str
        The cause of premature termination. One of 'maxevals_exceeded' and 'rounding_errors'
    function_evaluations : int
        Number of function evaluations
    evaluation : pd.Series
        A bool for each estimation step. True if this was a model evaluation and False otherwise
    """

    name: Optional[str] = None
    description: Optional[str] = None
    ofv: Optional[float] = None
    ofv_iterations: Optional[pd.Series] = None
    parameter_estimates: Optional[pd.Series] = None
    parameter_estimates_sdcorr: Optional[pd.Series] = None
    parameter_estimates_iterations: Optional[pd.DataFrame] = None
    covariance_matrix: Optional[pd.DataFrame] = None
    correlation_matrix: Optional[pd.DataFrame] = None
    information_matrix: Optional[pd.DataFrame] = None
    standard_errors: Optional[pd.Series] = None
    standard_errors_sdcorr: Optional[pd.Series] = None
    relative_standard_errors: Optional[pd.Series] = None
    minimization_successful: Optional[bool] = None
    minimization_successful_iterations: Optional[pd.DataFrame] = None
    estimation_runtime: Optional[float] = None
    estimation_runtime_iterations: Optional[pd.DataFrame] = None
    individual_ofv: Optional[pd.Series] = None
    individual_estimates: Optional[pd.DataFrame] = None
    individual_estimates_covariance: Optional[pd.DataFrame] = None
    residuals: Optional[pd.DataFrame] = None
    predictions: Optional[pd.DataFrame] = None
    runtime_total: Optional[float] = None
    termination_cause: Optional[str] = None
    termination_cause_iterations: Optional[pd.Series] = None
    function_evaluations: Optional[float] = None
    function_evaluations_iterations: Optional[pd.Series] = None
    significant_digits: Optional[float] = None
    significant_digits_iterations: Optional[pd.Series] = None
    log_likelihood: Optional[float] = None
    log: Optional[Log] = None
    evaluation: Optional[pd.Series] = None
