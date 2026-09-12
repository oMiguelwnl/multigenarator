import json
from hashlib import sha256

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from test_native_application import import_payload, qualified_profile

from multilang.db.base import Base
from multilang.domain.datasets import DatasetManifest
from multilang.native_runtime import build_native_facade
from multilang.repositories.native_repository import NativeRepository
from multilang.settings import Settings


def test_source_refresh_keeps_semantic_ids_and_old_dataset_revisions():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            repo = NativeRepository(session)
            repo.put_profile(qualified_profile())
            facade = build_native_facade(session, Settings(_env_file=None, roadmap_4_enabled=True))
            first = facade.import_dataset(import_payload(), actor="linguist")
            session.commit()
            before = repo.dataset_identities(first["dataset_id"])
            old_forms = repo.dataset_forms(first["dataset_id"])
            second_payload = import_payload()
            second_payload["source"]["version"] = "2"
            second_payload["data"] = json.dumps(json.loads(second_payload["data"]), indent=2)
            second_payload["source"]["sha256"] = sha256(second_payload["data"].encode()).hexdigest()
            second_payload["version"] = "fixture-2"
            second = facade.import_dataset(second_payload, actor="linguist")
            session.commit()
            after = repo.dataset_identities(second["dataset_id"])
            assert [identity.lexical_identity_id for identity in before] == [
                identity.lexical_identity_id for identity in after
            ]
            assert all(
                identity.source_version == "1"
                for identity in repo.dataset_identities(first["dataset_id"])
            )
            assert all(identity.source_version == "2" for identity in after)
            assert repo.dataset_forms(first["dataset_id"]) == old_forms
            assert (
                repo.dataset_forms(second["dataset_id"])[0].surface_form_id
                == old_forms[0].surface_form_id
            )
            reviewed = DatasetManifest.model_validate(
                repo.get_dataset(first["dataset_id"])
            ).model_copy(update={"version": "reviewed-original"})
            repo.clone_dataset_version(
                first["dataset_id"], reviewed, actor="reviewer", reason="independent_review"
            )
            assert repo.dataset_identities(reviewed.dataset_id) == before
            assert repo.dataset_forms(reviewed.dataset_id) == old_forms
            before_replay = [repo.get_identity(identity.lexical_identity_id) for identity in after]
            assert (
                facade.import_dataset(import_payload(), actor="linguist")["dataset_id"]
                == first["dataset_id"]
            )
            assert [
                repo.get_identity(identity.lexical_identity_id) for identity in after
            ] == before_replay
    finally:
        engine.dispose()
