"""Error segmentation and representative failure reports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def add_error_columns(
    frame: pd.DataFrame, actual_column: str = "actual", forecast_column: str = "forecast"
) -> pd.DataFrame:
    result = frame.copy()
    result["error"] = result[actual_column] - result[forecast_column]
    result["absolute_error"] = result["error"].abs()
    result["direction"] = result["error"].map(
        lambda value: "underforecast" if value > 0 else "overforecast" if value < 0 else "exact"
    )
    return result


def summarize_errors(frame: pd.DataFrame, output_path: str | Path | None = None) -> pd.DataFrame:
    result = add_error_columns(frame)
    groupings = [c for c in ["store_id", "cat_id", "event_flag", "demand_segment"] if c in result]
    summaries = []
    for column in groupings:
        grouped = (
            result.groupby(column, dropna=False)
            .agg(mae=("absolute_error", "mean"), bias=("error", "mean"), rows=("error", "size"))
            .reset_index()
        )
        grouped["dimension"] = column
        summaries.append(grouped.rename(columns={column: "value"}))
    output = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Forecast error analysis",
            "",
            "This report summarizes forecast residuals. The segments are descriptive and should not be read as causal explanations.",
            "",
        ]
        if output.empty:
            lines.append("No segmented error table is available yet.")
        else:
            lines.append("```text")
            lines.append(output.sort_values("mae", ascending=False).head(30).to_string(index=False))
            lines.extend(
                [
                    "```",
                    "",
                    "## Largest failures",
                    "",
                    "```text",
                    result.sort_values("absolute_error", ascending=False)
                    .head(20)
                    .to_string(index=False),
                    "```",
                ]
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output
