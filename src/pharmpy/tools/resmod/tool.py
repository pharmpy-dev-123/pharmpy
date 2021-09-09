import sympy

import pharmpy.model
import pharmpy.tools
from pharmpy import Parameter, Parameters, RandomVariable, RandomVariables
from pharmpy.modeling import set_iiv_on_ruv, set_power_on_ruv
from pharmpy.statements import Assignment, ModelStatements
from pharmpy.tools.modelfit import create_multiple_fit_workflow
from pharmpy.tools.workflows import Task, Workflow


class Resmod(pharmpy.tools.Tool):
    def __init__(self, model):
        self.model = model
        super().__init__()
        self.model.database = self.database.model_database  # FIXME: Changes the user model object

    def run(self):
        wf = self.create_workflow()
        res = self.dispatcher.run(wf, self.database)
        # res.to_json(path=self.database.path / 'results.json')
        # res.to_csv(path=self.database.path / 'results.csv')
        return res

    def create_workflow(self):
        self.model.database = (
            self.database.model_database
        )  # FIXME: Not right! Changes the user model object
        wf = Workflow()

        task_base_model = Task('create_base_model', _create_base_model, self.model)
        wf.add_task(task_base_model)

        task_iiv = Task('create_iiv_on_ruv_model', _create_iiv_on_ruv_model, self.model)
        wf.add_task(task_iiv)
        # task_power = Task('create_power_model', _create_power_model, self.model)

        fit_wf = create_multiple_fit_workflow(n=2)
        wf.insert_workflow(fit_wf, predecessors=[task_base_model, task_iiv])

        task_results = Task('results', post_process)
        wf.add_task(task_results, predecessors=fit_wf.output_tasks)
        return wf


def post_process(*models):
    return models[0]


def _create_base_model(input_model):
    base_model = pharmpy.model.Model()
    theta = Parameter('theta', 0.1)
    omega = Parameter('omega', 0.01, lower=0)
    sigma = Parameter('sigma', 1, lower=0)
    params = Parameters([theta, omega, sigma])
    base_model.parameters = params

    eta = RandomVariable.normal('eta', 'iiv', 0, omega.symbol)
    sigma = RandomVariable.normal('epsilon', 'ruv', 0, sigma.symbol)
    rvs = RandomVariables([eta, sigma])
    base_model.random_variables = rvs

    y = Assignment('Y', theta.symbol + eta.symbol + sigma.symbol)
    stats = ModelStatements([y])
    base_model.statements = stats

    base_model.dependent_variable = y.symbol
    base_model.name = "base"
    base_model.dataset = _create_dataset(input_model)
    base_model.database = input_model.database
    return base_model


def _create_iiv_on_ruv_model(input_model):
    base_model = _create_base_model(input_model)  # FIXME: could be done only once in the workflow
    model = base_model.copy()
    model.database = base_model.database  # FIXME: Should be unnecessary
    set_iiv_on_ruv(model)
    model.name = 'iiv_on_ruv'
    return model


def _create_power_model(input_model):
    base_model = _create_base_model(input_model)  # FIXME: could be done only once in the workflow
    model = base_model.copy()
    model.individual_prediction_symbol = sympy.Symbol('CIPREDI')  # FIXME: Not model agnostic
    set_power_on_ruv(model)
    model.name = 'power'
    return model


def _create_dataset(input_model):
    residuals = input_model.modelfit_results.residuals
    df = residuals['CWRES'].reset_index().rename(columns={'CWRES': 'DV'})
    return df
