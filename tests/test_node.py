"""Tests for SeriesNode and SeriesSource."""

from macro_econ.series.node import SeriesNode, SeriesSource


class TestSeriesSource:
    def test_basic_creation(self):
        src = SeriesSource("fred", "UNRATE")
        assert src.source == "fred"
        assert src.series_id == "UNRATE"
        assert src.extra == {}

    def test_with_extra(self):
        src = SeriesSource("bea", "T20305", {"table": "T20305", "line_number": 3})
        assert src.extra["line_number"] == 3


class TestSeriesNode:
    def test_leaf_detection(self, sample_tree):
        assert not sample_tree.is_leaf
        a1 = sample_tree.find("A1")
        assert a1 is not None
        assert a1.is_leaf

    def test_parent_linkage(self, sample_tree):
        a1 = sample_tree.find("A1")
        assert a1 is not None
        assert a1.parent is not None
        assert a1.parent.code == "A"
        assert a1.parent.parent is not None
        assert a1.parent.parent.code == "ROOT"

    def test_level_assignment(self, sample_tree):
        assert sample_tree.level == 0
        a = sample_tree.find("A")
        assert a is not None and a.level == 1
        a1 = sample_tree.find("A1")
        assert a1 is not None and a1.level == 2
        b1a = sample_tree.find("B1a")
        assert b1a is not None and b1a.level == 3

    def test_find_existing(self, sample_tree):
        node = sample_tree.find("B1")
        assert node is not None
        assert node.name == "Sub-branch B1"

    def test_find_missing(self, sample_tree):
        assert sample_tree.find("NONEXISTENT") is None

    def test_find_root(self, sample_tree):
        assert sample_tree.find("ROOT") is sample_tree

    def test_walk(self, sample_tree):
        codes = [n.code for n in sample_tree.walk()]
        assert codes == ["ROOT", "A", "A1", "A2", "B", "B1", "B1a"]

    def test_leaves(self, sample_tree):
        leaf_codes = [n.code for n in sample_tree.leaves()]
        assert leaf_codes == ["A1", "A2", "B1a"]

    def test_path(self, sample_tree):
        b1a = sample_tree.find("B1a")
        assert b1a is not None
        assert b1a.path() == ["ROOT", "B", "B1", "B1a"]

    def test_path_root(self, sample_tree):
        assert sample_tree.path() == ["ROOT"]

    def test_get_source(self, sample_tree):
        a = sample_tree.find("A")
        assert a is not None
        fred_src = a.get_source("fred")
        assert fred_src is not None
        assert fred_src.series_id == "A_FRED"
        bea_src = a.get_source("bea")
        assert bea_src is not None
        assert bea_src.extra["table"] == "T10105"
        assert a.get_source("bls") is None

    def test_add_child(self, sample_tree):
        new_child = SeriesNode(name="New Leaf", code="NEW")
        a = sample_tree.find("A")
        assert a is not None
        a.add_child(new_child)
        assert new_child.parent is a
        assert new_child.level == 2
        assert sample_tree.find("NEW") is new_child

    def test_to_dict(self, sample_tree):
        d = sample_tree.to_dict()
        assert d["name"] == "Root"
        assert d["code"] == "ROOT"
        assert len(d["children"]) == 2
        assert d["children"][0]["code"] == "A"
        assert len(d["children"][0]["children"]) == 2
        # Leaf should not have children key
        a1_dict = d["children"][0]["children"][0]
        assert "children" not in a1_dict

    def test_print_tree(self, sample_tree):
        tree_str = sample_tree.print_tree()
        assert "Root [ROOT]" in tree_str
        assert "Leaf A1 [A1]" in tree_str
        assert "Leaf B1a [B1a]" in tree_str

    def test_str_representation(self, sample_tree):
        s = str(sample_tree)
        assert "Root [ROOT]" in s
        assert "fred:ROOT_SERIES" in s
