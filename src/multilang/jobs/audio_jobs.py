"""Audio work delegates to the versioned audio service facade."""


def generate_audio_job(facade, payload: dict, actor: str) -> dict:
    return facade.generate_audio(payload, actor)
