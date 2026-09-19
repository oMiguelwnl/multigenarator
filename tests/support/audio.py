"""Small, decodable silent MP3 fixture built without an encoder or network access."""

# Twelve MPEG-1 Layer III frames: 44.1 kHz, mono, 128 kbps, 13,824 PCM frames.
SILENT_MP3 = (bytes.fromhex("fffb90c4") + bytes(413)) * 12
SILENT_MP3_DURATION_MS = 313
