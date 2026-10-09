from schemas import EvidenceItem
from tools import format_evidence, research_topic


def test_format_evidence():
    evidence = [
        EvidenceItem(
            title="Source One",
            url="https://example.com/one",
            snippet="Important information.",
        ),
        EvidenceItem(
            title="Source Two",
            url="https://example.com/two",
            snippet="More information.",
        ),
    ]

    result = format_evidence(evidence)

    assert "[Source 1]" in result
    assert "Source One" in result
    assert "https://example.com/one" in result
    assert "Important information." in result


def test_format_empty_evidence():
    result = format_evidence([])

    assert result == "No external research evidence is available."


def test_research_topic_without_queries():
    result = research_topic([])

    assert result == []


def test_research_topic_limits_queries(mocker):
    mock_search = mocker.patch("tools.web_research")

    mock_search.invoke.return_value = [
        {
            "title": "Test Source",
            "url": "https://example.com",
            "snippet": "Test evidence.",
        }
    ]

    queries = [
        "query one",
        "query two",
        "query three",
        "query four",
    ]

    result = research_topic(
        queries,
        max_queries=2,
    )

    assert mock_search.invoke.call_count == 2
    assert len(result) == 1
    assert result[0].title == "Test Source"