"""Ranking work delegates to the deterministic ranking facade."""


def calculate_ranking_job(facade, payload: dict, actor: str) -> dict:
    return facade.calculate_ranking(payload, actor)
