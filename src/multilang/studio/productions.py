"""Durable launch receipts for the single-computer Studio and its CLI worker."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.settings import Settings

Kind = Literal["frequency", "word-list", "highlights", "foundations", "phonetics", "grammar", "latin"]
GENERIC = {"frequency", "word-list", "highlights"}
PHONETICS = {"ru": "export-russian-phonemes", "pl": "export-polish-phonemes", "el": "export-greek-phonemes"}
MAX_SOURCE_BYTES = 5_000_000


def catalog() -> dict[str, list[str]]:
    rows = {language.value: ["word-list", "highlights"] for language in SupportedLanguage}
    for language, kinds in rows.items():
        if language not in {"la", "ko"}:
            kinds.insert(0, "frequency")
        if language in PHONETICS or language == "ko":
            kinds.append("phonetics")
        if language in {"ja", "ko"}:
            kinds.append("foundations")
    rows["la"].append("latin")
    return rows


class ProductionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    language: SupportedLanguage
    supportLanguage: Literal["pt", "en", "es"]
    kind: Kind
    level: int | None = Field(default=None, ge=1, le=3)
    highlightInput: Literal["text", "vocabulary"] = "text"
    sourceExtension: Literal["txt", "html", "htm"] | None = None
    sourceText: str | None = Field(default=None, max_length=MAX_SOURCE_BYTES)

    @model_validator(mode="after")
    def valid_combination(self):
        if not self.name.strip() or any(ord(char) < 32 for char in self.name):
            raise ValueError("invalid name")
        if self.kind not in catalog()[self.language.value]:
            raise ValueError("unsupported material")
        if self.supportLanguage != "pt" and (self.language == "ko" or self.kind not in GENERIC):
            raise ValueError("unsupported support language")
        if self.level is not None and self.kind != "frequency":
            raise ValueError("level requires frequency")
        if self.highlightInput == "vocabulary" and (self.kind != "highlights" or self.language == "ko"):
            raise ValueError("unsupported highlight mode")
        if self.kind == "highlights" and self.highlightInput == "text" and self.language in {"zh", "la"}:
            raise ValueError("no passage extractor for this language")
        if self.kind in {"word-list", "highlights"}:
            if not self.sourceText or not self.sourceText.strip() or self.sourceExtension is None:
                raise ValueError("source required")
            if len(self.sourceText.encode("utf-8")) > MAX_SOURCE_BYTES or "\0" in self.sourceText:
                raise ValueError("invalid source")
            if self.kind == "word-list" and self.sourceExtension != "txt":
                raise ValueError("word lists require txt")
        elif self.sourceText is not None or self.sourceExtension is not None:
            raise ValueError("unexpected source")
        return self


class RepairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID


class Production(BaseModel):
    id: UUID
    name: str
    language: str
    supportLanguage: str
    kind: Kind
    status: Literal["queued", "running", "completed", "failed"]
    stage: str
    message: str
    createdAt: datetime
    updatedAt: datetime
    jobId: UUID | None = None
    canDownload: bool = False


class _Receipt(Production):
    fingerprint: str
    repairIds: list[UUID] = Field(default_factory=list)


class ProductionService:
    def __init__(self, root: Path, *, run_command: Callable | None = None):
        self.root = root.resolve()
        self.state = self.root / ".multilang/studio/productions"
        self.state.mkdir(parents=True, exist_ok=True)
        self.exports = self.root / Settings(_env_file=self.root / ".env").export_output_dir / "studio"
        self._lock = RLock()
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="studio-production")
        self._run_command = run_command or self._cli
        lease = self._try_lease()
        if lease:
            with lease:
                for receipt in self.list():
                    if receipt.status in {"queued", "running"}:
                        self._set(receipt, status="failed", message=(
                            "O Estúdio foi interrompido. Confira o trabalho anterior antes de repetir."
                        ))
                    self._clear_sources(receipt.id)

    def _try_lease(self):
        # A second localhost port can point to the same worktree. OS ownership ends on exit.
        handle = (self.state / "execution.lock").open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return None
        return handle

    def _read(self, id: UUID) -> _Receipt:
        try:
            return self._load(self.state / str(id) / "receipt.json")
        except FileNotFoundError:
            raise HTTPException(404, "Produção não encontrada.") from None

    def _load(self, path: Path) -> _Receipt:
        row = _Receipt.model_validate_json(path.read_bytes())
        if row.canDownload:
            try:
                self._package(row)
            except HTTPException:
                row.canDownload = False
                row.message = "O arquivo do pacote Anki está indisponível."
        return row

    def _save(self, row: _Receipt) -> None:
        folder = self.state / str(row.id)
        folder.mkdir(exist_ok=True)
        temporary = folder / f"{uuid4()}.tmp"
        try:
            temporary.write_text(row.model_dump_json(), encoding="utf-8")
            temporary.replace(folder / "receipt.json")
        finally:
            temporary.unlink(missing_ok=True)

    def _set(self, row: _Receipt, **changes) -> None:
        for key, value in changes.items():
            setattr(row, key, value)
        row.updatedAt = datetime.now(UTC)
        self._save(row)

    def list(self) -> list[_Receipt]:
        rows = [self._load(p) for p in self.state.glob("*/receipt.json")]
        return sorted(rows, key=lambda row: row.createdAt, reverse=True)

    def get(self, id: UUID) -> _Receipt:
        return self._read(id)

    def start(self, req: ProductionRequest) -> _Receipt:
        fingerprint = hashlib.sha256(req.model_dump_json().encode()).hexdigest()

        def previous_request() -> _Receipt | None:
            if not (self.state / str(req.id) / "receipt.json").exists():
                return None
            existing = self._read(req.id)
            if existing.fingerprint != fingerprint:
                raise HTTPException(409, "Este identificador já pertence a outra configuração.")
            return existing

        with self._lock:
            if existing := previous_request():
                return existing
            lease = self._try_lease()
            if lease is None:
                raise HTTPException(409, "Aguarde o término da produção em andamento.")
            try:
                if existing := previous_request():
                    lease.close()
                    return existing
                now = datetime.now(UTC)
                row = _Receipt(id=req.id, name=req.name.strip(), language=req.language.value,
                               supportLanguage=req.supportLanguage, kind=req.kind, status="queued",
                               stage="Fila", message="Aguardando execução.", createdAt=now,
                               updatedAt=now, fingerprint=fingerprint)
                self._save(row)
                self._pool.submit(self._execute, row.model_copy(), req, lease)
                return row
            except BaseException:
                lease.close()
                raise

    def repair(self, id: UUID, attempt: UUID) -> _Receipt:
        with self._lock:
            row = self._read(id)
            if attempt in row.repairIds:
                return row
            if row.status != "failed" or not row.jobId:
                raise HTTPException(409, "A produção não possui um trabalho corrigível.")
            lease = self._try_lease()
            if lease is None:
                raise HTTPException(409, "Aguarde o término da produção em andamento.")
            try:
                # Another process may have updated this receipt before the lease was acquired.
                row = self._read(id)
                if attempt in row.repairIds:
                    lease.close()
                    return row
                if row.status != "failed":
                    raise HTTPException(409, "A situação da produção mudou. Atualize a página.")
                row.repairIds.append(attempt)
                self._set(row, status="queued", stage="Fila", message="Aguardando correção.")
                self._pool.submit(self._execute, row.model_copy(), None, lease)
                return row
            except BaseException:
                lease.close()
                raise

    def _cli(self, args: list[str], observe: Callable[[str], None]) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(self.root / "src"), env.get("PYTHONPATH"))))
        env.update(PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                   MULTILANG_STUDIO_CONNECTIONS_ENABLED="1")
        with subprocess.Popen([sys.executable, "-m", "multilang.cli", *args], cwd=self.root,
                              env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, encoding="utf-8", errors="replace") as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                observe(line.rstrip())
            if proc.wait():
                raise RuntimeError("CLI failed")

    def _clear_sources(self, id: UUID) -> None:
        for extension in ("txt", "html", "htm"):
            (self.state / str(id) / f"source.{extension}").unlink(missing_ok=True)

    def _execute(self, row: _Receipt, req: ProductionRequest | None, lease) -> None:
        output = self.exports / str(row.id)
        failure = "Confira a conexão com o banco, os provedores e os dados do idioma."
        with lease:
            try:
                output.mkdir(parents=True, exist_ok=True)

                def observe(line: str) -> None:
                    if row.jobId is None and line.startswith("job_id="):
                        self._set(row, jobId=UUID(line.removeprefix("job_id=")))
                    if line.startswith("stage=generate_text ") and row.stage != "Texto e áudio":
                        self._set(row, stage="Texto e áudio", message="Processando os itens do trabalho.")

                if req is None:
                    self._set(row, status="running", stage="Correção", message="Corrigindo itens pendentes.")
                    self._run_command(["repair-text", "--job-id", str(row.jobId)], observe)
                    self._set(row, stage="Áudio", message="Sintetizando áudios ausentes.")
                    self._run_command(["synthesize-audio", "--job-id", str(row.jobId), "--missing-only"], observe)
                elif req.kind in GENERIC:
                    self._set(row, status="running", stage="Vocabulário", message="Preparando a fonte.")
                    args = ["generate", "--language", req.language.value, "--source", req.kind,
                            "--support-language", req.supportLanguage]
                    if req.level is not None:
                        args += ["--level", str(req.level)]
                    if req.kind == "highlights":
                        args += ["--highlight-input", req.highlightInput]
                    try:
                        if req.sourceText is not None:
                            path = self.state / str(row.id) / f"source.{req.sourceExtension}"
                            path.write_bytes(req.sourceText.encode("utf-8"))
                            args += ["--input-file", str(path)]
                        self._run_command(args, observe)
                    finally:
                        if req.sourceText is not None:
                            self._clear_sources(row.id)
                    if not row.jobId:
                        raise ValueError("CLI did not identify the generated job")

                self._set(row, status="running", stage="Exportação", message="Validando o pacote Anki.")
                failure = "Confira as pendências do conteúdo, do áudio e do inventário desta modalidade."
                if row.kind in GENERIC:
                    args = ["export", "--job-id", str(row.jobId), "--format", "apkg",
                            "--output-dir", str(output), "--deck-name", row.name]
                    if req is None:
                        args.append("--refresh-snapshots")
                else:
                    args = self._special_export(row, output)
                summary: dict[str, str] = {}

                def observe_export(line: str) -> None:
                    key, sep, value = line.partition("=")
                    if sep and key in {"artifact_path", "card_count", "export_status"}:
                        summary[key] = value

                self._run_command(args, observe_export)
                package = self._package(row)
                if int(summary.get("card_count", 0)) <= 0 or summary.get("export_status") == "partial":
                    raise ValueError("incomplete export")
                if args[0] == "korean-foundations":
                    if summary.get("export_status") != "written":
                        raise ValueError("foundation export unconfirmed")
                elif self.root / summary.get("artifact_path", "") != package:
                    raise ValueError("unexpected artifact path")
                self._set(row, status="completed", stage="Resultado", canDownload=True,
                          message="Pacote Anki disponível para revisão.")
            except Exception:
                self._set(row, status="failed", canDownload=False, message=failure)

    @staticmethod
    def _special_export(row: Production, output: Path) -> list[str]:
        if row.kind == "latin":
            return ["export-latin-mvp", "--format", "apkg", "--output-dir", str(output),
                    "--deck-name", row.name]
        if row.language == "ko":
            family = "hangul" if row.kind == "foundations" else "pronunciation"
            return ["korean-foundations", "export", "--family", family, "--format", "apkg",
                    "--output", str(output / "deck.apkg")]
        command = "export-kana" if row.kind == "foundations" else PHONETICS[row.language]
        return [command, "--output-path", str(output / "deck.apkg"), "--deck-name", row.name]

    def _package(self, row: Production) -> Path:
        folder = self.exports / str(row.id)
        name = f"{row.jobId}.apkg" if row.kind in GENERIC else (
            "latin-mvp-50.apkg" if row.kind == "latin" else "deck.apkg"
        )
        path = folder / name
        if path.resolve() != self.exports.resolve() / str(row.id) / name or not path.is_file():
            raise HTTPException(404, "Pacote Anki indisponível.")
        return path

    def resolve_package(self, id: UUID) -> Path:
        row = self.get(id)
        if row.status != "completed":
            raise HTTPException(409, "A produção ainda não possui um pacote concluído.")
        return self._package(row)

    def close(self) -> None:
        self._pool.shutdown(wait=True)


def production_router(jobs: ProductionService) -> APIRouter:
    router = APIRouter(prefix="/studio-api/productions")

    @router.get("/catalog")
    def get_catalog():
        return catalog()

    @router.get("", response_model=list[Production])
    def list_productions():
        return jobs.list()

    @router.post("", status_code=202, response_model=Production)
    def start(payload: ProductionRequest):
        return jobs.start(payload)

    @router.get("/{id}", response_model=Production)
    def detail(id: UUID):
        return jobs.get(id)

    @router.post("/{id}/repair", status_code=202, response_model=Production)
    def repair(id: UUID, payload: RepairRequest):
        return jobs.repair(id, payload.id)

    return router
