"""Import work delegates to the validated dataset facade."""


def import_dataset_job(facade, payload: dict, actor: str) -> dict:
    return facade.import_dataset(payload, actor)
