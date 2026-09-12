"""Anki work delegates to the projection/export facade."""


def export_anki_job(facade, payload: dict, actor: str) -> dict:
    return facade.export_anki(payload, actor)
