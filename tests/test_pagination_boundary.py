import pytest
from source_transport import SourceError

from scripts import auto_collect_magazine_rss as magazine


def test_hll_requires_explicit_final_pagination_for_empty_container():
    body=b'<div class="atc_list"><ul></ul></div><a data-page="5">5</a><a class="btn_next disabled" data-page="0">next</a>'
    assert magazine.parse_hll(body,page=6) == []
    with pytest.raises(SourceError):
        magazine.parse_hll(body,page=1)
    with pytest.raises(SourceError):
        magazine.parse_hll(body.replace(b'btn_next disabled',b'btn_next'),page=6)


def test_wp_missing_posts_are_terminal_only_beyond_verified_count(monkeypatch):
    monkeypatch.setattr(magazine,'request',lambda *a,**kw:b'{"count_posts":"12"}')
    feed={'name':'GQ','url':'https://www.gqkorea.co.kr/wp-admin/admin-ajax.php','mode':'wp_search'}
    rows,report=magazine.collect_feed({**feed,'page':2},'고윤정')
    assert rows==[] and report['status']=='success'
    assert magazine.collect_feed(feed,'고윤정')[1]['status']=='failed'


def test_archive_404_requires_a_valid_current_feed(monkeypatch):
    feed={'name':'RSS','url':'https://example.org/feed','mode':'rss','page':2}
    def fetch(url):
        if 'paged=' in url:raise SourceError('HTTP 404','http')
        return b'<rss><channel/></rss>'
    monkeypatch.setattr(magazine,'fetch',fetch)
    rows,report=magazine.collect_feed(feed,'고윤정')
    assert rows==[] and report['boundary_status']=='pagination_unavailable'
    assert 'unconfirmed' in report['warnings'][0]
    monkeypatch.setattr(magazine,'fetch',lambda url: (_ for _ in ()).throw(SourceError('HTTP 404','http')))
    assert magazine.collect_feed(feed,'고윤정')[1]['status']=='failed'
