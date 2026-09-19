"""Conservative IPA syntax admission; pronunciation accuracy needs provenance."""

import unicodedata


def is_usable_ipa(value: object) -> bool:
    """Accept a bounded, delimited transcription, never infer its correctness.

    Plain spelling, markup and other reading systems are not IPA. Japanese,
    Chinese and Korean reading contracts must use their own validators.
    """
    if not isinstance(value, str) or not 3 <= len(value) <= 512:
        return False
    if any(unicodedata.category(char).startswith("C") for char in value):
        return False
    text = value.strip()
    if len(text) < 3 or (text[0], text[-1]) not in {("/", "/"), ("[", "]")}:
        return False
    has_letter = False
    for character in unicodedata.normalize("NFD", text[1:-1]):
        code = ord(character)
        if (
            "a" <= character <= "z"
            or 0x0250 <= code <= 0x02AF
            or 0x1D00 <= code <= 0x1D7F
            or character in "æçðøħŋœǀǁǂǃβθχφϕ"
        ):
            has_letter = True
        elif not (
            0x02B0 <= code <= 0x02FF
            or 0x0300 <= code <= 0x036F
            or 0x1D80 <= code <= 0x1DBF
            or character in " .|‖‿↗↘"
        ):
            return False
    return has_letter
