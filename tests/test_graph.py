from pipeline import blog_graph


def test_graph_contains_expected_nodes():
    graph = blog_graph.get_graph()

    expected_nodes = {
        "research_decision",
        "research",
        "plan",
        "write",
        "review",
        "revise",
        "finalize",
    }

    actual_nodes = set(graph.nodes.keys())

    assert expected_nodes.issubset(actual_nodes)


def test_graph_has_research_branch():
    graph = blog_graph.get_graph()

    edges = [
        (edge.source, edge.target)
        for edge in graph.edges
    ]

    assert ("research_decision", "research") in edges
    assert ("research_decision", "plan") in edges


def test_graph_has_revision_loop():
    graph = blog_graph.get_graph()

    edges = [
        (edge.source, edge.target)
        for edge in graph.edges
    ]

    assert ("review", "revise") in edges
    assert ("revise", "review") in edges


def test_graph_has_finalize_path():
    graph = blog_graph.get_graph()

    edges = [
        (edge.source, edge.target)
        for edge in graph.edges
    ]

    assert ("review", "finalize") in edges


def test_graph_has_expected_linear_flow():
    graph = blog_graph.get_graph()

    edges = [
        (edge.source, edge.target)
        for edge in graph.edges
    ]

    assert ("plan", "write") in edges
    assert ("write", "review") in edges
    assert ("finalize", "__end__") in edges