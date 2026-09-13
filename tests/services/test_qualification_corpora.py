import hashlib
import json
from datetime import UTC, datetime

import httpx
import pytest


def _transport(*, duplicate=False, wrong_revision=False):
    def handler(request):
        query = request.url.params
        if query.get("meta") == "siteinfo":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "general": {"lang": "en"},
                        "rightsinfo": {
                            "url": "https://creativecommons.org/licenses/by/4.0/",
                            "text": "Creative Commons Attribution 4.0",
                        },
                    }
                },
            )
        if query.get("list") == "allpages":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "allpages": [
                            {"pageid": 2, "ns": 0, "title": "Second"},
                            {"pageid": 1, "ns": 0, "title": "First"},
                        ]
                    },
                    "continue": {"apcontinue": "Third", "continue": "-||"},
                },
            )
        page = int(query.get("pageids", 1))
        if query.get("prop") == "revisions":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "pageid": page,
                                "ns": 0,
                                "title": f"Page {page}",
                                "revisions": [
                                    {
                                        "revid": page * 10,
                                        "timestamp": "2025-02-01T00:00:00Z",
                                        "slots": {
                                            "main": {
                                                "contentmodel": "wikitext",
                                                "content": f"Source {page}",
                                            }
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                },
            )
        revision = int(query["oldid"])
        suffix = "" if duplicate else f" Document {revision}."
        return httpx.Response(
            200,
            json={
                "parse": {
                    "pageid": revision // 10,
                    "revid": revision + int(wrong_revision),
                    "text": "<p>People learn words by reading complete documents." + suffix + "</p>"
                    "<script>malicious()</script><p>Another sentence for the reader.</p>",
                }
            },
        )

    return httpx.MockTransport(handler)


def test_acquisition_preserves_real_documents_and_hashes(tmp_path):
    from multilang.services.qualification_corpora import (
        acquire_wikimedia_documents,
        read_document_corpus,
    )

    with httpx.Client(transport=_transport()) as client:
        result = acquire_wikimedia_documents(
            "en", "wikinews", [2, 1], tmp_path / "out", client=client, sleep=lambda _: None
        )
    assert result.document_count == 2
    documents = read_document_corpus(tmp_path / "out/documents.jsonl", result.documents_sha256)
    assert [d.document_id for d in documents] == ["en.wikinews.org:1", "en.wikinews.org:2"]
    assert documents[0].source_url == "https://en.wikinews.org/w/index.php?oldid=10"
    assert documents[0].revision_id == "10"
    assert documents[0].text_register == "news"
    assert documents[0].variant == "unresolved"
    assert documents[0].license_id == "CC-BY-4.0"
    assert "malicious" not in documents[0].text
    assert documents[0].text_sha256 == hashlib.sha256(documents[0].text.encode()).hexdigest()
    assert result.production_eligible is False
    assert not documents[0].redistribution_approved
    assert len(list((tmp_path / "out/raw").glob("*.json"))) >= 3
    before = (tmp_path / "out/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="exists"):
        acquire_wikimedia_documents("en", "wikinews", [1], tmp_path / "out")
    assert (tmp_path / "out/manifest.json").read_bytes() == before


def test_selection_is_frozen_and_does_not_claim_representativeness():
    from multilang.services.qualification_corpora import discover_wikimedia_pages

    with httpx.Client(transport=_transport()) as client:
        result = discover_wikimedia_pages("en", "wikinews", limit=2, client=client)
    assert result.page_ids == (1, 2)
    assert result.selection_policy == "bounded-allpages-prefix-v1"
    assert result.representative is False
    assert len(result.response_sha256) == 64
    assert result.continuation_available


def test_duplicate_text_is_not_counted_as_distinct_usage(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    with httpx.Client(transport=_transport(duplicate=True)) as client:
        result = acquire_wikimedia_documents(
            "en", "wikinews", [1, 2], tmp_path / "out", client=client
        )
    assert result.document_count == 1
    assert len(result.exclusions) == 1
    assert result.exclusions[0].reason == "duplicate_text"


@pytest.mark.parametrize(
    "language,project",
    [("la", "wikipedia"), ("en.evil.test", "wikipedia"), ("en", "https://127.0.0.1")],
)
def test_untrusted_origin_never_reaches_network(language, project, tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    with httpx.Client(
        transport=httpx.MockTransport(lambda _: pytest.fail("network called"))
    ) as client:
        with pytest.raises(ValueError):
            acquire_wikimedia_documents(language, project, [1], tmp_path / "out", client=client)


@pytest.mark.parametrize(
    "response,code",
    [
        (
            httpx.Response(302, headers={"location": "http://127.0.0.1/private"}),
            "redirect_forbidden",
        ),
        (httpx.Response(403), "http_403"),
        (httpx.Response(200, content=b"x" * 500), "response_byte_limit"),
    ],
)
def test_unavailable_sources_are_recorded_without_fake_coverage(tmp_path, response, code):
    from multilang.services.qualification_corpora import (
        AcquisitionLimits,
        acquire_wikimedia_documents,
    )

    requests = []

    def handler(request):
        requests.append(str(request.url))
        return response

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        result = acquire_wikimedia_documents(
            "en",
            "wikipedia",
            [1],
            tmp_path / code,
            limits=AcquisitionLimits(max_response_bytes=128),
            client=client,
        )
    assert result.document_count == 0
    assert result.blockers[0].reason == code
    assert len(requests) == 1
    assert all(url.startswith("https://en.wikipedia.org/") for url in requests)


def test_wrong_revision_is_rejected(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    with httpx.Client(transport=_transport(wrong_revision=True)) as client:
        result = acquire_wikimedia_documents("en", "wikinews", [1], tmp_path / "out", client=client)
    assert result.document_count == 0
    assert result.blockers[0].reason == "revision_mismatch"


def test_reader_rejects_tampering_symlinks_and_false_approvals(tmp_path):
    from multilang.services.qualification_corpora import (
        acquire_wikimedia_documents,
        read_document_corpus,
    )

    with httpx.Client(transport=_transport()) as client:
        result = acquire_wikimedia_documents("en", "wikinews", [1], tmp_path / "out", client=client)
    path = tmp_path / "out/documents.jsonl"
    with pytest.raises(ValueError, match="checksum"):
        read_document_corpus(path, "0" * 64)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        read_document_corpus(link, result.documents_sha256)
    record = json.loads(path.read_text())
    record["redistribution_approved"] = True
    path.write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError):
        read_document_corpus(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_retry_after_is_respected_and_bounded(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    delays, requests = [], []

    def handler(request):
        requests.append(request)
        return httpx.Response(429, headers={"retry-after": "2"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = acquire_wikimedia_documents(
            "pt", "wikipedia", [1], tmp_path / "out", client=client, sleep=delays.append
        )
    assert len(requests) == 3
    assert delays == [2, 2]
    assert result.blockers[0].reason == "http_429"
    assert result.blockers[0].retry_after == "2"
    assert result.blockers[0].retry_not_before > datetime.now(UTC)


def test_license_is_bound_to_publication_period():
    from multilang.services.qualification_corpora import wikimedia_license

    rights = {"url": "https://creativecommons.org/licenses/by/4.0/", "text": "CC BY 4.0"}
    assert (
        wikimedia_license("en", "wikinews", datetime(2010, 1, 1, tzinfo=UTC), rights)[0]
        == "CC-BY-2.5"
    )
    assert (
        wikimedia_license("pt", "wikinews", datetime(2010, 1, 1, tzinfo=UTC), rights)[0]
        == "unresolved"
    )


def test_selection_cannot_claim_ids_absent_from_frozen_listing():
    from multilang.services.qualification_corpora import PageSelection, discover_wikimedia_pages

    with httpx.Client(transport=_transport()) as client:
        selection = discover_wikimedia_pages("en", "wikinews", limit=2, client=client)
    data = selection.model_dump(mode="json")
    data["page_ids"] = [999]
    with pytest.raises(ValueError, match="selection"):
        PageSelection.model_validate(data)


def test_compressed_response_and_malformed_rights_fail_closed(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    for name, response in (
        (
            "unexpected_content_encoding",
            httpx.Response(
                200, headers={"content-encoding": "br"}, stream=httpx.ByteStream(b"untrusted")
            ),
        ),
        ("invalid_rights_metadata", httpx.Response(200, json={"query": []})),
    ):
        with httpx.Client(transport=httpx.MockTransport(lambda _: response)) as client:
            result = acquire_wikimedia_documents(
                "en", "wikinews", [1], tmp_path / name, client=client
            )
        assert result.document_count == 0
        assert result.blockers[0].reason == name


def test_streamed_and_aggregate_byte_limits_are_enforced(tmp_path):
    from multilang.services.qualification_corpora import (
        AcquisitionLimits,
        acquire_wikimedia_documents,
    )

    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, stream=httpx.ByteStream(b"x" * 150))
        )
    ) as client:
        result = acquire_wikimedia_documents(
            "pt",
            "wikipedia",
            [1],
            tmp_path / "stream",
            client=client,
            limits=AcquisitionLimits(max_response_bytes=100),
        )
    assert result.blockers[0].reason == "response_byte_limit"
    with httpx.Client(transport=_transport()) as client:
        result = acquire_wikimedia_documents(
            "en",
            "wikinews",
            [1],
            tmp_path / "total",
            client=client,
            limits=AcquisitionLimits(max_total_bytes=100),
        )
    assert result.blockers[0].reason == "total_byte_limit"


def test_document_byte_limit_retains_reason_without_truncating(tmp_path):
    from multilang.services.qualification_corpora import (
        AcquisitionLimits,
        acquire_wikimedia_documents,
    )

    with httpx.Client(transport=_transport()) as client:
        result = acquire_wikimedia_documents(
            "en",
            "wikinews",
            [1],
            tmp_path / "out",
            client=client,
            limits=AcquisitionLimits(max_document_bytes=20),
        )
    assert result.document_count == 0
    assert result.blockers[0].reason == "document_byte_limit"


def test_excessive_retry_after_does_not_ignore_server_delay(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(503, headers={"retry-after": "600"}))
    ) as client:
        result = acquire_wikimedia_documents(
            "pt",
            "wikipedia",
            [1],
            tmp_path / "out",
            client=client,
            sleep=lambda _: pytest.fail("should defer"),
        )
    assert result.blockers[0].reason == "retry_deferred"


def test_all_22_routes_preserve_unresolved_variants(tmp_path):
    from multilang.domain.jobs import SupportedLanguage
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    languages = [language.value for language in SupportedLanguage if language.value != "la"]
    assert len(languages) == 22
    for language in languages:
        with httpx.Client(transport=_transport()) as client:
            result = acquire_wikimedia_documents(
                language, "wikipedia", [1], tmp_path / language, client=client
            )
        assert result.language.value == language
        assert result.production_eligible is False


def test_output_ancestor_symlink_is_rejected_before_request(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: pytest.fail("network called"))
    ) as client:
        with pytest.raises(ValueError, match="symlink"):
            acquire_wikimedia_documents(
                "en", "wikipedia", [1], tmp_path / "link/out", client=client
            )


def test_recent_new_document_selection_records_real_ids_and_policy():
    from multilang.services.qualification_corpora import discover_wikimedia_pages

    def handler(request):
        assert request.url.params["list"] == "recentchanges"
        assert request.url.params["rctype"] == "new"
        return httpx.Response(
            200,
            json={
                "query": {
                    "recentchanges": [
                        {"pageid": 52, "revid": 100, "ns": 0, "timestamp": "2026-09-01T00:00:00Z"},
                        {"pageid": 53, "revid": 101, "ns": 0, "timestamp": "2026-09-02T00:00:00Z"},
                    ]
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        selection = discover_wikimedia_pages(
            "pt", "wikinews", limit=2, strategy="recent-new-pages", client=client
        )
    assert selection.page_ids == (52, 53)
    assert selection.selection_policy == "bounded-recent-new-pages-v1"
    assert not selection.representative


def test_long_retry_records_deadline_and_stops_all_remaining_ids(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    called = []
    base = _transport().handler

    def handler(request):
        called.append(request)
        if request.url.params.get("pageids"):
            return httpx.Response(429, headers={"retry-after": "600"})
        return base(request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = acquire_wikimedia_documents(
            "en", "wikinews", [1, 2], tmp_path / "out", client=client
        )
    assert len(called) == 2
    assert result.blockers[0].retry_after == "600"
    assert result.blockers[0].retry_not_before > datetime.now(UTC)
    assert result.blockers[1].reason == "not_attempted_source_deferred"


def test_localized_license_deed_is_same_source_claim():
    from multilang.services.qualification_corpora import wikimedia_license

    rights = {"url": "https://creativecommons.org/licenses/by-sa/4.0/deed.pt"}
    assert wikimedia_license("pt", "wikipedia", datetime.now(UTC), rights)[0] == "CC-BY-SA-4.0"
    rights = {"url": "https://creativecommons.org.evil.test/licenses/by-sa/4.0/deed.pt"}
    assert wikimedia_license("pt", "wikipedia", datetime.now(UTC), rights)[0] == "unresolved"


def test_parse_requests_revision_id_explicitly(tmp_path):
    from multilang.services.qualification_corpora import acquire_wikimedia_documents

    base = _transport().handler

    def handler(request):
        if request.url.params.get("action") == "parse":
            assert "revid" in request.url.params["prop"].split("|")
        return base(request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = acquire_wikimedia_documents("en", "wikinews", [1], tmp_path / "out", client=client)
    assert result.document_count == 1
