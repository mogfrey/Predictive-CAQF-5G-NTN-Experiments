from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import columns_for_family


@dataclass
class FoldResult:
    predictor: str
    horizon_s: int
    heldout_pass: str
    n: int
    brier: float
    precision: float
    recall: float


def _model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)),
    ])


def leave_one_pass_out(df: pd.DataFrame, family: str, horizons_s: Iterable[int], p_continue: float = 0.90) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "pass_id" not in df.columns:
        raise ValueError("pass_id is required for whole-pass holdout")
    predictions = []
    folds: list[FoldResult] = []
    for heldout in sorted(x for x in df["pass_id"].dropna().unique() if x):
        train = df[df["pass_id"] != heldout]
        test = df[df["pass_id"] == heldout]
        if set(train["pass_id"].dropna()) & set(test["pass_id"].dropna()):
            raise RuntimeError("pass leakage detected")
        features = columns_for_family(train, family)
        if not features:
            raise ValueError(f"No usable features for family {family}")
        for h in horizons_s:
            label = f"survive_{h}s"
            eligible = f"eligible_{h}s"
            tr = train[train[eligible].fillna(False) & train[label].notna()]
            te = test[test[eligible].fillna(False) & test[label].notna()]
            if tr.empty or te.empty or tr[label].nunique() < 2:
                continue
            model = _model()
            model.fit(tr[features], tr[label].astype(int))
            prob = model.predict_proba(te[features])[:, 1]
            pred = (prob >= p_continue).astype(int)
            y = te[label].astype(int).to_numpy()
            rec = te[["run_id", "pass_id", "t_s"]].copy()
            rec["predictor_family"] = family
            rec["horizon_s"] = h
            rec["p_survive"] = prob
            rec["continue_decision"] = pred
            rec["truth_survive"] = y
            predictions.append(rec)
            folds.append(FoldResult(
                predictor=family,
                horizon_s=h,
                heldout_pass=str(heldout),
                n=len(te),
                brier=float(brier_score_loss(y, prob)),
                precision=float(precision_score(y, pred, zero_division=0)),
                recall=float(recall_score(y, pred, zero_division=0)),
            ))
    pred_df = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    fold_df = pd.DataFrame([x.__dict__ for x in folds])
    return pred_df, fold_df
