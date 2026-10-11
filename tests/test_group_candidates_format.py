from scripts import rebuild_group_link_candidates as mod


def test_regeneration_preserves_notes_without_extra_eof_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, 'PAGES', tmp_path)
    page = tmp_path / 'brands/chanel.md'
    page.parent.mkdir()
    page.write_text('# Old\n\n'+mod.START+'\nold\n'+mod.END+'\n\nManual note\n\n')
    assert mod.update_page(page, 'Chanel', [('interviews.md', 'Interview', 'https://example.org/article')])
    text = page.read_text()
    assert text.endswith('Manual note\n')
    assert not text.endswith('\n\n')
    assert not mod.update_page(page, 'Chanel', [('interviews.md', 'Interview', 'https://example.org/article')])
