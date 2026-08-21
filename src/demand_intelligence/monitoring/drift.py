"""Feature drift via PSI and two-sample KS tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def population_stability_index(reference, current, bins: int = 10) -> float:
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    ref_share = np.clip(ref_counts / max(1, ref_counts.sum()), 1e-6, None)
    cur_share = np.clip(cur_counts / max(1, cur_counts.sum()), 1e-6, None)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


def drift_report(
    reference: pd.DataFrame, current: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    rows = []
    for column in columns:
        if column not in reference or column not in current:
            continue
        ref = pd.to_numeric(reference[column], errors="coerce").dropna()
        cur = pd.to_numeric(current[column], errors="coerce").dropna()
        if ref.empty or cur.empty:
            continue
        statistic, pvalue = ks_2samp(ref, cur)
        rows.append(
            {
                "feature": column,
                "psi": population_stability_index(ref, cur),
                "ks_statistic": float(statistic),
                "ks_pvalue": float(pvalue),
                "drift_flag": bool(pvalue < 0.05),
            }
        )
    return pd.DataFrame(rows)
