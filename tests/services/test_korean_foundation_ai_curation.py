from importlib.util import find_spec


def test_ai_curation_contract_module_exists() -> None:
    assert find_spec("multilang.services.korean_foundation_ai_curation") is not None
