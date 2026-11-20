import pytest
from lifecycle.config import ConfigError, load, parse


def test_defaults_when_the_file_is_empty(tmp_path):
    (tmp_path / ".lifecycle.toml").write_text("", encoding="utf-8")
    config = load(tmp_path)
    assert (config.integration, config.protected, config.guides) == (
        "develop",
        "master",
        "docs/guides",
    )
    assert config.board_owner is None and config.gate == ()


def test_found_from_a_subdirectory(tmp_path):
    (tmp_path / ".lifecycle.toml").write_text('[guides]\npath = "guides"\n', encoding="utf-8")
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert load(tmp_path / "a" / "b").guides_dir == tmp_path.resolve() / "guides"


def test_a_typo_fails_loudly(tmp_path):
    with pytest.raises(ConfigError, match="protcted"):
        parse({"branches": {"protcted": "main"}}, tmp_path)


def test_a_lens_reads_its_paths_and_references(tmp_path):
    config = parse(
        {"review": {"lenses": {"person-facing": {"paths": ["apps/web/"], "read": ["docs/ux.md"]}}}},
        tmp_path,
    )
    assert config.lenses["person-facing"].paths == ("apps/web/",)
    assert config.as_dict()["review"]["lenses"]["person-facing"]["read"] == ["docs/ux.md"]


def test_a_board_needs_owner_and_number(tmp_path):
    with pytest.raises(ConfigError, match="owner and number"):
        parse({"board": {"owner": "orwir"}}, tmp_path)


def test_commands_must_be_strings(tmp_path):
    with pytest.raises(ConfigError, match="list of strings"):
        parse({"gate": {"commands": "pytest"}}, tmp_path)


def test_no_file_is_no_config(tmp_path):
    assert load(tmp_path) is None


def test_a_misspelt_lens_fails_loudly(tmp_path):
    with pytest.raises(ConfigError, match="person-facin"):
        parse({"review": {"lenses": {"person-facin": {"paths": ["x/"]}}}}, tmp_path)
