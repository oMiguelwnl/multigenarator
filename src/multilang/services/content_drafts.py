"""Durable, namespace-bound original provider drafts for later contextual review."""

import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.content import ContentDraft, canonical_content_hash
from multilang.services.vocabulary_review import _plain_path, _read_bytes


class ContentDraftStore:
    def __init__(self, root: Path):
        self.root = _plain_path(root)

    def _path(self, identifier: str, namespace: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", identifier):
            raise ValueError("draft identifier must be a SHA-256")
        scope = canonical_content_hash({"namespace": namespace})
        return _plain_path(self.root / scope / (identifier + ".json"))

    def put(self, draft: ContentDraft) -> None:
        draft = ContentDraft.model_validate(draft.model_dump(mode="json"))
        content = draft.model_dump_json().encode("utf-8")
        if len(content) > 256 * 1024:
            raise ValueError("draft byte limit exceeded")
        target = self._path(draft.draft_sha256, draft.request.namespace)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with TemporaryDirectory(prefix=".draft-", dir=target.parent) as directory:
            temporary = Path(directory) / "draft.json"
            temporary.write_bytes(content)
            temporary.chmod(0o600)
            try:
                os.link(temporary, target)
            except FileExistsError:
                if _read_bytes(target, limit=256 * 1024) != content:
                    raise ValueError("stored original draft changed") from None

    def load(self, identifier: str, *, namespace: str) -> ContentDraft:
        target = self._path(identifier, namespace)
        draft = ContentDraft.model_validate_json(_read_bytes(target, limit=256 * 1024))
        if draft.draft_sha256 != identifier or draft.request.namespace != namespace:
            raise ValueError("stored draft identity or namespace mismatch")
        return draft
