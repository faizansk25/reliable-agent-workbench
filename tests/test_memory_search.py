from core import LongTermMemory, ShortTermMemory
from tools import search_documents


def test_short_term_memory_is_bounded():
    memory = ShortTermMemory(max_size=2)
    memory.add("user", "first")
    memory.add("assistant", "second")
    memory.add("user", "third")
    assert [item["content"] for item in memory.get_context()] == ["second", "third"]


def test_long_term_memory_deduplicates_and_recalls(tmp_path):
    path = tmp_path / "memory.json"
    memory = LongTermMemory(path)
    memory.store("Python supports type hints", "language")
    memory.store("Python supports type hints", "language")
    restored = LongTermMemory(path)
    assert len(restored.facts) == 1
    assert restored.recall("Python hints")[0]["category"] == "language"


def test_local_search_is_real_and_deterministic():
    results = search_documents(
        "agent reliability",
        {"A": "agent checkpoint reliability", "B": "cooking recipes", "C": "agent prompts"},
    )
    assert [item["title"] for item in results] == ["A", "C"]
    assert results[0]["score"] == 2
