"""Core data structures for hierarchical economic series trees."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, Optional


@dataclass
class SeriesSource:
    """Identifies a data series in a specific API.

    Attributes:
        source: API provider ("fred", "bea", or "bls").
        series_id: Primary identifier (FRED mnemonic, BEA table name, BLS series ID).
        extra: Source-specific parameters.
            BEA:  {"table": "T20305", "frequency": "M", "line_number": 1}
            BLS:  {"item_code": "SA0", "seasonal": "S"}
            FRED: {} (series_id alone is sufficient)
    """

    source: str
    series_id: str
    extra: dict = field(default_factory=dict)


@dataclass
class SeriesNode:
    """A node in a hierarchical series tree.

    Attributes:
        name: Human-readable name (e.g., "Personal Consumption Expenditures").
        code: Short unique identifier within the tree (e.g., "PCE").
        sources: List of API sources where this series can be fetched.
        children: Child nodes in the hierarchy.
        description: Optional longer description.
        level: Depth in the tree (0 = root).
        parent: Reference to parent node (set automatically).
    """

    name: str
    code: str
    sources: list[SeriesSource] = field(default_factory=list)
    children: list[SeriesNode] = field(default_factory=list)
    description: str = ""
    level: int = 0
    parent: Optional[SeriesNode] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for child in self.children:
            child.parent = self
            child.level = self.level + 1
            child.__post_init__()

    def add_child(self, child: SeriesNode) -> None:
        """Add a child node with correct parent/level linkage."""
        child.parent = self
        child.level = self.level + 1
        child.__post_init__()
        self.children.append(child)

    @property
    def is_leaf(self) -> bool:
        """True if this node has no children."""
        return len(self.children) == 0

    def leaves(self) -> list[SeriesNode]:
        """Return all leaf nodes under this node (recursive)."""
        if self.is_leaf:
            return [self]
        result: list[SeriesNode] = []
        for child in self.children:
            result.extend(child.leaves())
        return result

    def find(self, code: str) -> Optional[SeriesNode]:
        """Depth-first search for a node by code."""
        if self.code == code:
            return self
        for child in self.children:
            found = child.find(code)
            if found is not None:
                return found
        return None

    def walk(self) -> Generator[SeriesNode, None, None]:
        """Pre-order traversal yielding all nodes."""
        yield self
        for child in self.children:
            yield from child.walk()

    def path(self) -> list[str]:
        """Return list of codes from root to this node."""
        codes: list[str] = []
        node: Optional[SeriesNode] = self
        while node is not None:
            codes.append(node.code)
            node = node.parent
        return list(reversed(codes))

    def get_source(self, source_name: str) -> Optional[SeriesSource]:
        """Return the SeriesSource for a given API, or None."""
        for src in self.sources:
            if src.source == source_name:
                return src
        return None

    def to_dict(self) -> dict:
        """Serialize to nested dict for JSON export or widget rendering."""
        d: dict = {
            "name": self.name,
            "code": self.code,
            "level": self.level,
            "description": self.description,
            "sources": [
                {"source": s.source, "series_id": s.series_id, "extra": s.extra}
                for s in self.sources
            ],
        }
        if self.children:
            d["children"] = [child.to_dict() for child in self.children]
        return d

    def __str__(self) -> str:
        indent = "  " * self.level
        src_str = ", ".join(f"{s.source}:{s.series_id}" for s in self.sources)
        line = f"{indent}{self.name} [{self.code}]"
        if src_str:
            line += f" ({src_str})"
        return line

    def print_tree(self) -> str:
        """Return a formatted string showing the full tree."""
        lines = [str(node) for node in self.walk()]
        return "\n".join(lines)
