"""Exact pronunciation versioning around AudioSynthesisService's existing adapters."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from multilang.domain.audio import (
    AudioAssetRecord,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.audio_version import AudioVersion, PronunciationSignature
from multilang.services.audio_synthesis import AudioSynthesisService


def audio_artifact_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reusable_audio_version(
    signature: PronunciationSignature, version: AudioVersion, *, namespace: str = "core"
) -> bool:
    if (
        signature != version.signature
        or namespace != version.namespace
        or version.review_status == "rejected"
    ):
        return False
    path = Path(version.storage_path)
    return (
        path.is_file()
        and not path.is_symlink()
        and path.stat().st_size == version.byte_size
        and audio_artifact_hash(path) == version.artifact_sha256
    )


def validate_pronunciation_ssml(signature: PronunciationSignature) -> None:
    """Only bounded synthesis markup can reach an existing provider adapter."""
    if "<!" in signature.ssml or "<?" in signature.ssml:
        raise ValueError("SSML declarations and entities are prohibited")
    try:
        root = ElementTree.fromstring(signature.ssml)
    except ElementTree.ParseError as exc:
        raise ValueError("SSML must be well formed") from exc
    tags = {
        "speak": {"version", "{http://www.w3.org/XML/1998/namespace}lang"},
        "voice": {"name"},
        "prosody": {"rate", "pitch", "volume", "duration"},
        "phoneme": {"alphabet", "ph"},
        "break": {"time", "strength"},
    }
    elements = list(root.iter())
    if len(elements) > 256 or root.tag.rsplit("}", 1)[-1] != "speak":
        raise ValueError("SSML structure limit or root mismatch")
    children = list(root)
    if (
        root.get("{http://www.w3.org/XML/1998/namespace}lang") != signature.locale
        or len(children) != 1
        or children[0].tag.rsplit("}", 1)[-1] != "voice"
        or (root.text or "").strip()
        or (children[0].tail or "").strip()
        or sum(element.tag.rsplit("}", 1)[-1] == "voice" for element in elements) != 1
        or sum(element.tag.rsplit("}", 1)[-1] == "speak" for element in elements) != 1
    ):
        raise ValueError(
            "SSML requires one explicit voice and locale enclosing all spoken text"
        )
    for element in elements:
        name = element.tag.rsplit("}", 1)[-1]
        if name not in tags or set(element.attrib) - tags[name]:
            raise ValueError("SSML contains unapproved elements or attributes")
        if name == "voice" and element.get("name") != signature.voice_id:
            raise ValueError("SSML voice differs from pronunciation signature")
        xml_locale = element.get("{http://www.w3.org/XML/1998/namespace}lang")
        if xml_locale is not None and xml_locale != signature.locale:
            raise ValueError("SSML locale differs from pronunciation signature")
        if element.tag.startswith("{") and not element.tag.startswith(
            "{http://www.w3.org/2001/10/synthesis}"
        ):
            raise ValueError("SSML unapproved namespace")
    if "".join(root.itertext()).strip() != signature.normalized_text:
        raise ValueError("SSML spoken text differs from pronunciation signature")


class NativeAudioService:
    def __init__(
        self,
        *,
        synthesis_service: AudioSynthesisService,
        storage_dir: Path,
        provider_model_version: str,
    ) -> None:
        self.synthesis_service = synthesis_service
        self.storage_dir = Path(storage_dir).resolve()
        self.provider_model_version = provider_model_version

    def generate(
        self,
        signature: PronunciationSignature,
        *,
        job_id: str,
        item_key: str,
        namespace: str = "core",
        cached_version: AudioVersion | None = None,
    ) -> AudioVersion:
        signature = PronunciationSignature.model_validate(
            signature.model_dump(mode="json")
        )
        validate_pronunciation_ssml(signature)
        provider = AudioProvider(
            getattr(self.synthesis_service.adapter, "provider", AudioProvider.AZURE)
        )
        if (
            signature.provider != provider
            or signature.provider_model_version != self.provider_model_version
        ):
            raise ValueError(
                "pronunciation provider/model version does not match configured adapter"
            )
        if signature.audio_format != self.synthesis_service._audio_format():
            raise ValueError(
                "pronunciation audio format does not match configured adapter"
            )
        if cached_version is not None:
            path = Path(cached_version.storage_path).resolve()
            if path.is_relative_to(self.storage_dir) and reusable_audio_version(
                signature, cached_version, namespace=namespace
            ):
                return cached_version
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        namespace_hash = sha256(namespace.encode()).hexdigest()
        destination_dir = self.storage_dir / "versions" / namespace_hash
        destination_dir.mkdir(parents=True, exist_ok=True)
        # A temporary synthesis cannot overwrite a previous immutable version.
        with TemporaryDirectory(
            prefix="native-audio-", dir=self.storage_dir
        ) as temp_dir:
            temporary_path = Path(temp_dir) / "audio.mp3"
            normalized = NormalizedTtsInput(
                display_text=signature.display_text,
                tts_text=signature.normalized_text,
                ssml_text=signature.ssml,
                synthesis_request_sha256=signature.signature_sha256,
            )
            prepared = AudioAssetRecord(
                job_id=job_id,
                item_key=item_key,
                asset_kind=signature.asset_kind,
                display_text=signature.display_text,
                normalized_input=normalized,
                provenance=AudioProvenance(
                    provider=signature.provider,
                    voice_id=signature.voice_id,
                    locale=signature.locale,
                    format=signature.audio_format,
                    text_hash=normalized.text_hash,
                    ssml_hash=normalized.ssml_hash,
                    storage_path=str(temporary_path),
                    byte_size=0,
                    status=AudioSynthesisStatus.PENDING,
                ),
            )
            materialized = self.synthesis_service.synthesize_prepared_asset(prepared)
            actual = materialized.provenance
            if (
                actual.status != AudioSynthesisStatus.SYNTHESIZED
                or actual.fallback_used
                or actual.provider != signature.provider
                or actual.voice_id != signature.voice_id
                or actual.locale != signature.locale
                or actual.format != signature.audio_format
                or Path(actual.storage_path) != temporary_path
                or temporary_path.is_symlink()
            ):
                raise ValueError(
                    "synthesized audio does not match exact pronunciation contract"
                )
            size = temporary_path.stat().st_size
            if size != actual.byte_size or size <= 0:
                raise ValueError("audio byte integrity mismatch")
            artifact_hash = audio_artifact_hash(temporary_path)
            destination = (
                destination_dir / f"{signature.signature_sha256}-{artifact_hash}.mp3"
            )
            if destination.is_symlink():
                raise ValueError("immutable audio destination integrity conflict")
            if (
                not destination.exists()
                or audio_artifact_hash(destination) != artifact_hash
            ):
                # Restoring verified bytes at a content-addressed path repairs
                # corruption; it never changes the bytes named by that version.
                temporary_path.replace(destination)
        return AudioVersion(
            signature=signature,
            storage_path=str(destination),
            artifact_sha256=artifact_hash,
            byte_size=size,
            namespace=namespace,
        )
