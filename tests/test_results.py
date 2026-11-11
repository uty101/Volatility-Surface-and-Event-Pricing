import base64
import re
from pathlib import Path

from volsurf.results import REPO, SECTIONS, build_results

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
# instruction 13 tests the page against the committed tables and charts, as PLAN 11.3 does the README (rule 13)
README = (ROOT / "README.md").read_text(encoding="utf-8")
N_TESTS = int(re.search(r"\) ([\d,]+) tests", README).group(1).replace(",", ""))


def _page() -> str:
    return build_results(OUT / "tables", OUT / "figures", N_TESTS)


def _embedded(path: Path, page: str) -> bool:
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}\"" in page


def test_every_readme_figure_is_embedded():
    page = _page()
    figures = re.findall(r"\]\((outputs/figures/[^)]+\.png)\)", README)
    assert len(figures) >= 7
    for path in figures:
        assert _embedded(ROOT / path, page)


def test_every_chart_is_embedded():
    page = _page()
    for path in sorted((OUT / "figures").glob("*.png")):
        assert _embedded(path, page)


def test_no_request_but_the_footer_link():
    page = _page()
    assert re.findall(r"https?://[^\"'<\s]*", page) == [REPO]
    assert re.search(rf'<footer><a href="{re.escape(REPO)}">[^<]*</a></footer>', page)
    assert not re.search(r"<(script|link|iframe)\b", page)
    assert not re.search(r"""src=["'](?!data:)""", page)


def test_two_builds_match_byte_for_byte():
    assert _page().encode("utf-8") == _page().encode("utf-8")


def test_committed_page_is_the_build():
    assert (OUT / "results.html").read_text(encoding="utf-8") == _page()


def test_sections_follow_the_readme():
    page = _page()
    headings = re.findall(r"<h2>([^<]+)</h2>", page)
    readme = [x.removeprefix("## ") for x in README.split("\n") if re.match(r"## \d\. ", x)]
    assert headings == [*[s.heading.replace("&", "&amp;") for s in SECTIONS], "Risk report"]
    assert [h.replace("&amp;", "&") for h in headings[:6]] == readme


def test_header_holds_the_window_and_the_test_count():
    page = _page()
    head = page[:page.index("<h2>")]
    assert re.search(r"Capture window:</strong> 2026-10-28 to \d{4}-\d{2}-\d{2}, \d+ days, 2026-11-02 missed", head)
    assert f"{N_TESTS:,} tests" in head


def test_risk_report_section():
    section = _page().split("<h2>Risk report</h2>")[1]
    assert section.count("<table") == 3  # book, shock grid, breaches
    assert re.search(r'href="reports/risk_\d{4}-\d{2}-\d{2}\.pdf"', section)
