from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month_num"] = out["month"].dt.month
    out["year"] = out["month"].dt.year
    out["t"] = (out["year"] - out["year"].min()) * 12 + out["month_num"]
    return out


def _add_lags(df: pd.DataFrame, group_cols: list[str], cols: list[str], lags: list[int]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        for L in lags:
            out[f"{c}_lag{L}"] = out.groupby(group_cols)[c].shift(L)
    return out


def fit_predict_next_months(
    panel: pd.DataFrame,
    horizon_months: int = 6,
    lags: list[int] | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Train simple district panel forecaster and predict next horizon.

    This uses ML with lagged features (works without long histories).
    """

    lags = lags or [1, 2, 3]
    df = panel.copy().sort_values(["state", "district", "month"]).reset_index(drop=True)
    df = _add_time_features(df)

    targets = ["enrol_total", "demo_total", "bio_total"]
    df = _add_lags(df, ["state", "district"], targets, lags)

    feature_cols = ["month_num", "year", "t"] + [f"{t}_lag{L}" for t in targets for L in lags]

    train = df.dropna(subset=feature_cols)

    metrics: dict[str, float] = {}
    preds_all = []

    for y in targets:
        X = train[feature_cols]
        yy = train[y]

        model = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.08, random_state=42)
        model.fit(X, yy)

        # in-sample MAE as a quick quality check
        yhat = model.predict(X)
        metrics[f"mae_{y}"] = float(mean_absolute_error(yy, yhat))

        # Build future frame iteratively (recursive)
        last = df.groupby(["state", "district"], as_index=False).tail(1).copy()
        future_rows = []

        for h in range(1, horizon_months + 1):
            fut = last.copy()
            fut["month"] = (fut["month"] + pd.offsets.MonthBegin(h)).dt.to_period("M").dt.to_timestamp()
            fut = _add_time_features(fut)

            # shift lag features using last known/predicted values
            for L in lags:
                col = f"{y}_lag{L}"
                # for recursive one-step, lag1 uses last[y]; lag2 uses last lag1 etc.
                if L == 1:
                    fut[col] = last[y].values
                else:
                    fut[col] = last[f"{y}_lag{L-1}"].values

            # For other targets, we keep their lag columns as last observed (simpler multi-target)
            for other in targets:
                if other == y:
                    continue
                for L in lags:
                    fut[f"{other}_lag{L}"] = last.get(f"{other}_lag{L}", np.nan)

            fut[f"pred_{y}"] = model.predict(fut[feature_cols])
            future_rows.append(fut[["state", "district", "month", f"pred_{y}"]])

            # update last for next iteration
            last[y] = fut[f"pred_{y}"].values
            last = _add_lags(_add_time_features(last), ["state", "district"], [y], lags)

        y_future = pd.concat(future_rows, ignore_index=True)
        preds_all.append(y_future)

    # merge forecasts
    forecast = preds_all[0]
    for part in preds_all[1:]:
        forecast = forecast.merge(part, on=["state", "district", "month"], how="outer")

    return forecast.sort_values(["state", "district", "month"]).reset_index(drop=True), metrics
