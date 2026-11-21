import pytest
from lifecycle import METHOD
from lifecycle.config import DEFAULT_TEMPLATES, ConfigError, load, parse


def test_defaults_when_the_file_is_empty(tmp_path):
    (tmp_path / ".lifecycle.toml").write_text("", encoding="utf-8")
    config = load(tmp_path)
    assert (config.integration, config.guides) == ("main", "docs/guides")
    assert config.board_owner is None and config.gate == () and config.release_workflow is None


def test_the_retired_protected_branch_is_read_and_ignored(tmp_path):
    config = parse({"branches": {"integration": "main", "protected": "master"}}, tmp_path)
    assert config.as_dict()["branches"] == {"integration": "main"}


def test_the_release_workflow_is_named_by_its_file(tmp_path):
    config = parse({"release": {"workflow": "release.yml"}}, tmp_path)
    assert config.release_workflow == "release.yml"
    assert config.as_dict()["release"] == {"workflow": "release.yml"}
    with pytest.raises(ConfigError, match="'file'"):
        parse({"release": {"file": "release.yml"}}, tmp_path)


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


def test_templates_default_to_a_projects_five(tmp_path):
    config = parse({}, tmp_path)
    assert config.templates == DEFAULT_TEMPLATES and not config.templates_named
    assert config.as_dict()["templates"]["agents_template.md"] == "AGENTS.md"


def test_named_templates_replace_the_defaults(tmp_path):
    (tmp_path / ".lifecycle.toml").write_text(
        '[templates]\n"idea_gauntlet.md" = "AGENTS.md"\n', encoding="utf-8"
    )
    config = load(tmp_path)
    assert config.templates == {"idea_gauntlet.md": "AGENTS.md"} and config.templates_named


def test_an_empty_templates_table_fails_loudly(tmp_path):
    with pytest.raises(ConfigError, match="omit the table"):
        parse({"templates": {}}, tmp_path)


def test_an_unquoted_template_name_says_to_quote_it(tmp_path):
    (tmp_path / ".lifecycle.toml").write_text(
        '[templates]\nidea_gauntlet.md = "AGENTS.md"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="quote each file name"):
        load(tmp_path)


@pytest.mark.parametrize("target", ["", "  ", 3, ["AGENTS.md"]])
def test_a_template_names_the_file_it_ports_into(tmp_path, target):
    with pytest.raises(ConfigError, match="the file it ports into"):
        parse({"templates": {"agents_template.md": target}}, tmp_path)


def test_each_default_template_is_in_the_kits_method():
    assert all((METHOD / name).is_file() for name in DEFAULT_TEMPLATES)


def test_templates_must_be_a_table(tmp_path):
    with pytest.raises(ConfigError, match="must be a table"):
        parse({"templates": "AGENTS.md"}, tmp_path)
