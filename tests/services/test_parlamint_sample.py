"""The ParlaMint sample is a bounded diagnostic source, not deck content."""

import hashlib
import importlib
import importlib.util
import io
import json
import tarfile

import pytest


def prepare_sample(*args, **kwargs):
    name = "multilang.services.parlamint_sample"
    assert importlib.util.find_spec(name) is not None, "ParlaMint sample preparation is missing"
    return importlib.import_module(name).prepare_sample(*args, **kwargs)


def archive(tmp_path, members):
    path = tmp_path / "sample.tar.gz"
    with tarfile.open(path, "w:gz") as stream:
        for name, content in members:
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            stream.addfile(info, io.BytesIO(data))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_prepares_only_the_selected_language_and_pins_every_member(tmp_path):
    pt = "# newdoc id = pt-1\n# sent_id = pt-1.s1\n1\tOlá\tolá\tINTJ\t_\t_\t0\troot\t_\t_\n\n"
    path, digest = archive(
        tmp_path,
        [
            ("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu", pt),
            ("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2022.conllu", pt.replace("pt-1", "pt-2")),
            ("ParlaMint-4.0/Samples/ParlaMint-GB/ParlaMint-GB_2022.conllu", pt),
        ],
    )
    out = tmp_path / "result"
    result = prepare_sample(path, digest, out, languages={"PT": "pt"}, expected_members=2)
    assert result["status"] == "diagnostic_formal_speech_only"
    assert list(result["languages"]) == ["pt"]
    assert len(result["languages"]["pt"]["members"]) == 2
    target = out / "corpora/pt.conllu"
    assert hashlib.sha256(target.read_bytes()).hexdigest() == result["languages"]["pt"]["sha256"]
    assert target.read_text().count("# newdoc id") == 2
    assert json.loads((out / "manifest.json").read_text()) == result
    assert result["coverage_90_percent_verified"] is False
    assert result["production_eligible"] is False


def test_rejects_archive_mutation_without_publishing(tmp_path):
    path, _ = archive(
        tmp_path,
        [("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu", "x")],
    )
    out = tmp_path / "result"
    with pytest.raises(ValueError, match="checksum"):
        prepare_sample(path, "0" * 64, out, languages={"PT": "pt"}, expected_members=1)
    assert not out.exists()


def test_rejects_archive_traversal_and_duplicate_members(tmp_path):
    normal = "ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu"
    valid = "# newdoc id = pt-1\n# sent_id = pt-1.s1\n1\tOlá\tolá\tINTJ\t_\t_\t0\troot\t_\t_\n\n"
    for names in ([normal, "../escape.conllu"], [normal, normal]):
        path, digest = archive(tmp_path, [(name, valid) for name in names])
        out = tmp_path / "result"
        with pytest.raises(ValueError, match="unsafe|duplicate"):
            prepare_sample(path, digest, out, languages={"PT": "pt"}, expected_members=1)
        assert not out.exists()


def test_rejects_oversized_selected_member_before_output(tmp_path):
    path, digest = archive(
        tmp_path,
        [("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu", "a" * 101)],
    )
    out = tmp_path / "result"
    with pytest.raises(ValueError, match="size limit"):
        prepare_sample(
            path, digest, out, languages={"PT": "pt"}, expected_members=1,
            max_member_bytes=100,
        )
    assert not out.exists()


def test_unselected_documentation_symlink_is_ignored_but_selected_one_is_rejected(tmp_path):
    normal = "ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu"
    valid = "# newdoc id = pt-1\n# sent_id = pt-1.s1\n1\tOlá\tolá\tINTJ\t_\t_\t0\troot\t_\t_\n\n"
    path = tmp_path / "links.tar.gz"

    def build(link_name):
        with tarfile.open(path, "w:gz") as stream:
            data = valid.encode()
            member = tarfile.TarInfo(normal)
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
            link = tarfile.TarInfo(link_name)
            link.type = tarfile.SYMTYPE
            link.linkname = "../../escape"
            stream.addfile(link)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    digest = build("ParlaMint-4.0/TEI/Stylesheets")
    out = tmp_path / "safe"
    prepare_sample(path, digest, out, languages={"PT": "pt"}, expected_members=1)
    assert (out / "corpora/pt.conllu").is_file()

    digest = build("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2022.conllu")
    with pytest.raises(ValueError, match="unsafe"):
        prepare_sample(path, digest, tmp_path / "blocked", languages={"PT": "pt"}, expected_members=1)


def test_unselected_members_still_count_against_expansion_limit(tmp_path):
    valid = "# newdoc id = pt-1\n# sent_id = pt-1.s1\n1\tOlá\tolá\tINTJ\t_\t_\t0\troot\t_\t_\n\n"
    path, digest = archive(
        tmp_path,
        [
            ("ParlaMint-4.0/Samples/ParlaMint-PT/ParlaMint-PT_2017.conllu", valid),
            ("ParlaMint-4.0/Documentation/large.txt", "x" * 101),
        ],
    )
    out = tmp_path / "result"
    with pytest.raises(ValueError, match="expanded size limit"):
        prepare_sample(
            path, digest, out, languages={"PT": "pt"}, expected_members=1,
            max_archive_expanded_bytes=150,
        )
    assert not out.exists()
