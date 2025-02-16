import pytest

from pharmpy.deps import sympy
from pharmpy.modeling.eta_transformations import EtaTransformation


def S(x: str):
    return sympy.Symbol(x)


@pytest.mark.parametrize(
    'eta_trans,symbol,expression',
    [
        (
            EtaTransformation.boxcox(2),
            S('ETAB(2)'),
            ((sympy.exp(S('ETA(2)')) ** S('BOXCOX2') - 1) / S('BOXCOX2')),
        ),
    ],
)
def test_apply(eta_trans, symbol, expression):
    etas = {'eta1': S('ETA(1)'), 'eta2': S('ETA(2)'), 'etab1': S('ETAB(1)'), 'etab2': S('ETAB(2)')}

    thetas = {'theta1': 'BOXCOX1', 'theta2': 'BOXCOX2'}

    eta_trans.apply(etas, thetas)
    assert eta_trans.assignments[1].symbol == symbol
    assert eta_trans.assignments[1].expression == expression
