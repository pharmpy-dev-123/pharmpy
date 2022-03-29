from typing import Callable, Dict, List, Union

import numpy as np
import pandas as pd

from pharmpy.model import Model
from pharmpy.modeling.ml import predict_influential_individuals, predict_outliers


def summarize_individuals(models: List[Model]) -> Union[pd.DataFrame, None]:
    """Creates a summary dataframe keyed by model-individual pairs for an input
    list of models.

    Parameters
    ----------
    models : List[Model]
        Input models

    Return
    ------
    pd.DataFrame | None
        The summary as a dataframe

    Examples
    --------
    >>> from pharmpy.modeling import *
    >>> model = load_example_model("pheno")
    >>> fit(model)
    <Pharmpy model object pheno>
    >>> results = run_tool(
    ...     'modelsearch',
    ...     model=model,
    ...     mfl='ABSORPTION(ZO);PERIPHERALS([1, 2])',
    ...     algorithm='reduced_stepwise'
    ... ) # doctest: +SKIP
    >>> summarize_individuals([results.start_model, *results.models]) # doctest: +SKIP

    """

    modelsDict = {model.name: model for model in models}

    df = pd.concat(
        map(
            lambda model: groupedByIDAddColumnsOneModel(modelsDict, model),
            models,
        ),
        keys=[model.name for model in models],
        names=['model'],
        axis=0,
        verify_integrity=True,
    )

    return df


def parent_model_name(model: Model) -> str:
    return model.parent_model


def model_name(model: Model) -> str:
    return model.name


def outliers_fda_func(df: pd.DataFrame) -> float:
    # NOTE this returns a float because we will potentially concat this
    # with NaNs
    return float((abs(df) > 5).sum())


def outliers_fda(model: Model) -> Union[pd.Series, float]:
    residuals = model.modelfit_results.residuals
    if residuals is None:
        return np.nan
    else:
        groupedByID = residuals.groupby('ID')
        return groupedByID['CWRES'].agg(outliers_fda_func)


def _predicted(
    predict: Callable[[Model], pd.DataFrame], model: Model, column: str
) -> Union[pd.Series, float]:
    try:
        predicted = predict(model)
    except TypeError:
        # TODO remove this check as a TypeError should not be thrown by a
        # predictor, but None should be returned instead
        return np.nan
    if predicted is None:
        return np.nan
    return predicted[column]


def predicted_residual(model: Model) -> Union[pd.Series, float]:
    return _predicted(predict_outliers, model, 'residual')


def predicted_dofv(model: Model) -> Union[pd.Series, float]:
    return _predicted(predict_influential_individuals, model, 'dofv')


def ofv(model: Model) -> pd.Series:
    return model.modelfit_results.individual_ofv


def dofv(parent_model: Union[Model, None], candidate_model: Model) -> Union[pd.Series, float]:
    return np.nan if parent_model is None else ofv(parent_model) - ofv(candidate_model)


def groupedByIDAddColumnsOneModel(modelsDict: Dict[str, Model], model: Model) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(
        {
            'parent_model': parent_model_name(model),
            'outliers_fda': outliers_fda(model),
            'ofv': ofv(model),
            'dofv': dofv(modelsDict.get(model.parent_model), model),
            'predicted_dofv': predicted_dofv(model),
            'predicted_residual': predicted_residual(model),
        },
        orient='columns',
    )
    df.reset_index(inplace=True)
    df.set_index(['ID'], inplace=True)
    return df
