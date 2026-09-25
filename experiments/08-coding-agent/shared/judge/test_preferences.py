from taskboard.preferences import merge_preferences


def test_merge_preferences_is_recursive_and_non_mutating():
    defaults = {"ui": {"theme": "light", "density": "compact"}, "flags": ["a"]}
    overrides = {"ui": {"theme": "dark"}, "flags": ["b"]}

    result = merge_preferences(defaults, overrides)

    assert result == {"ui": {"theme": "dark", "density": "compact"}, "flags": ["b"]}
    result["ui"]["theme"] = "changed"
    result["flags"].append("c")
    assert defaults == {"ui": {"theme": "light", "density": "compact"}, "flags": ["a"]}
    assert overrides == {"ui": {"theme": "dark"}, "flags": ["b"]}
