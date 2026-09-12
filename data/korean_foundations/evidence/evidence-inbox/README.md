# Phase 31 Korean Foundation Evidence Inbox

This directory is a fixed, local, direct-placement boundary. It is not evidence
by itself. Do not place files here until the Plan 31 human evidence checkpoint.

The exact layout is:

```text
evidence-index.json
proposed-curation.json
proposed-media.json
curriculum-review.json
audio-playback-review.json
rights.json
reviewers/korean-orthography.json
reviewers/korean-phonetics.json
reviewers/portuguese.json
reviewers/independent-native-speaker.json
media/<exact basenames declared by proposed-media.json>
validation-receipt.json
```

`validation-receipt.json` is generated only after the confirmed index and every
declared source, reviewer, rights, media, and active-prestate binding pass. The
README and generated receipt are excluded from the evidence-bundle hash.

Multilang has no importer, upload, URL, archive, APKG, or source-root option for
this boundary. Place unpacked regular files directly at the exact paths above;
links, reparse points, archives, extra files, and undeclared media are rejected.
