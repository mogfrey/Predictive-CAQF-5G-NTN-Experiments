import pandas as pd
from caqf_exp.collectors import first_persistent_failure


def test_persistent_failure():
    s = pd.Series([True, False, False, True])
    assert first_persistent_failure(s, 2) == 1
