import pytest

from pharmpy.deps import sympy
from pharmpy.modeling.covariate_effect import CovariateEffect, _choose_param_inits


def S(x: str):
    return sympy.Symbol(x)


@pytest.mark.parametrize(
    'cov_eff,symbol,expression',
    [
        (
            CovariateEffect.exponential(),
            S('CLWGT'),
            sympy.exp(S('COVEFF1') * (S('WGT') - S('WGT_MEDIAN'))),
        ),
        (CovariateEffect.power(), S('CLWGT'), (S('WGT') / S('WGT_MEDIAN')) ** S('COVEFF1')),
        (CovariateEffect.linear(), S('CLWGT'), 1 + S('COVEFF1') * (S('WGT') - S('WGT_MEDIAN'))),
    ],
)
def test_apply(cov_eff, symbol, expression):
    cov_eff.apply(
        parameter='CL',
        covariate='WGT',
        thetas={'theta': 'COVEFF1'},
        statistics={'mean': 1, 'median': 1, 'std': 1},
    )

    assert cov_eff.template.symbol == symbol
    assert cov_eff.template.expression == expression


@pytest.mark.parametrize(
    'cov_eff, init, lower, upper', [('exp', 0.001, -0.8696, 0.8696), ('pow', 0.001, -100, 100000)]
)
def test_choose_param_inits(pheno_path, load_model_for_test, cov_eff, init, lower, upper):
    model = load_model_for_test(pheno_path)

    inits = _choose_param_inits(cov_eff, model, 'WGT')

    assert inits['init'] == init
    assert inits['lower'] == lower
    assert inits['upper'] == upper
