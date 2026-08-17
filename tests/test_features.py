import pandas as pd
from caqf_exp.features import build_horizon_labels


def test_horizon_label_before_event():
    df = pd.DataFrame({
        "run_id": ["r1"] * 5,
        "t_s": [0, 1, 2, 3, 4],
        "event_qos_termination": [0, 0, 0, 0, 1],
    })
    out = build_horizon_labels(df, [2])
    assert int(out.loc[out.t_s == 1, "survive_2s"].iloc[0]) == 1
    assert int(out.loc[out.t_s == 3, "survive_2s"].iloc[0]) == 0
