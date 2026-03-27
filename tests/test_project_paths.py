from scripts.project_paths import repo_root, wiki_base


def test_wiki_base_points_to_project_root():
    base = wiki_base()
    assert base.name == "Goyoonjung-Wiki"
    assert (base / "scripts").is_dir()


def test_repo_root_contains_wiki_project():
    root = repo_root()
    assert (root / "20_Projects" / "Goyoonjung-Wiki").resolve() == wiki_base()
