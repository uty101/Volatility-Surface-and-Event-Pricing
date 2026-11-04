from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from volsurf.answers import (
    ANSWER_COLUMNS,
    format_value,
    read_table,
    read_value,
    select_rows,
)

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
# PLAN 11.2 names these 2 tests on the committed outputs, and PLAN beats rule 7 (rule 13)
ANSWERS = read_table(TABLES / "answers.csv")
SMALL = pd.DataFrame({"day": ["2026-10-29", "2026-10-30", "2026-11-03"], "ticker": ["A", "B", "A"],
                      "x": ["1.5", "", "-2"], "y": ["1", "2", "3"], "status": ["ok", "fail", "too_few"]})


def _answers(question):
    return " ".join(ANSWERS.loc[ANSWERS["question"] == str(question), "answer"])


def test_every_question_answered():
    assert list(ANSWERS.columns) == ANSWER_COLUMNS
    assert sorted(ANSWERS["question"].unique()) == [str(q) for q in range(1, 7)]
    assert (ANSWERS["answer"] != "").all()


@pytest.mark.parametrize("i", range(len(ANSWERS)))
def test_sources_resolve(i):
    row = ANSWERS.iloc[i]
    table = read_table(TABLES / row["source_table"])
    assert len(select_rows(table, row["source_row"])) >= 1
    held = read_value(table, row["source_row"], row["source_column"])
    if row["value"] == "":
        assert np.isnan(held)
    elif isinstance(held, str):
        assert held == row["value"]
    else:
        assert float(row["value"]) == pytest.approx(held, rel=1e-9)


def test_question_3_framing_and_every_event_with_its_ratio():
    events = read_table(TABLES / "events.csv")
    done = events[events["ratio"] != ""]
    assert len(done) < 20  # the framing below holds below [events] min_n
    assert "cannot be told apart from 0 at this N" in _answers(3)
    for e in done.itertuples():
        assert f"{e.ticker} {e.timing} {e.event_date}" in _answers(3)
        assert f"ratio {float(e.ratio):.2f}" in _answers(3)


def test_question_4_gives_raw_and_deflated_with_the_trials():
    rows = ANSWERS[(ANSWERS["question"] == "4") & (ANSWERS["source_table"] == "strategy_stats.csv")]
    columns = set(rows.loc[rows["source_row"] == "strategy=timed_put", "source_column"])
    assert {"sharpe", "deflated_sharpe"} <= columns
    assert (ANSWERS["source_table"] == "spec_log.csv").any()
    assert "number of specifications tried" in _answers(4)


def test_question_5_mean_gap_only_with_the_proxy_sentence():
    rows = ANSWERS[ANSWERS["source_column"] == "mean_gap"]
    assert len(rows) == 1
    assert "the gap is the proxy, not a correlation risk premium" in rows["answer"].iloc[0]
    assert {"slope", "r2"} <= set(ANSWERS["source_column"])


def test_question_6_shares_and_the_error_sd_at_k_1():
    rows = ANSWERS[ANSWERS["question"] == "6"]
    assert set(rows["source_table"]) >= {"attribution_live.csv", "attribution_synthetic.csv", "hedging_frequency.csv"}
    k1 = rows[rows["source_row"].str.endswith("hedge_every_steps=1") & (rows["source_column"] == "error_sd")]
    assert len(k1) == 2
    assert "not comparable" in _answers(6)


def test_every_live_answer_states_its_n():
    assert "N = " in _answers(2) and "N = " in _answers(3) and "N = " in _answers(5) and "N = " in _answers(6)


def test_select_rows():
    assert list(select_rows(SMALL, "ticker=A")["day"]) == ["2026-10-29", "2026-11-03"]
    assert list(select_rows(SMALL, "status=ok|fail")["ticker"]) == ["A", "B"]
    assert list(select_rows(SMALL, "x!=;ticker=A")["y"]) == ["1", "3"]
    assert list(select_rows(SMALL, "x>0")["y"]) == ["1"]
    assert list(select_rows(SMALL, "day>=2026-10-30;day<=2026-10-30")["y"]) == ["2"]
    assert len(select_rows(SMALL, "all")) == 3


def test_read_value():
    assert read_value(SMALL, "day=2026-10-29", "x") == 1.5
    assert read_value(SMALL, "day=2026-10-29", "status") == "ok"
    assert np.isnan(read_value(SMALL, "day=2026-10-30", "x"))
    assert read_value(SMALL, "all", "count(*)") == 3
    assert read_value(SMALL, "all", "count(x)") == 2
    assert read_value(SMALL, "all", "sum(x)") == -0.5
    assert read_value(SMALL, "all", "max(y)") == 3
    assert read_value(SMALL, "ticker=A", "corr(x,y)") == pytest.approx(-1.0)


def test_read_value_needs_one_row():
    with pytest.raises(ValueError):
        read_value(SMALL, "ticker=A", "x")


def test_format_value():
    assert format_value(0.1234567890123) == "0.123456789"
    assert format_value("too_few_trials") == "too_few_trials"
    assert format_value(np.nan) == ""
