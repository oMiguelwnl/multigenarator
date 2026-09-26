"""Import the Mandarin pilot into a disposable real Anki collection (offline)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from anki.collection import Collection, ImportAnkiPackageRequest


def verify(deck: Path, cache: Path, report: Path):
    deck, cache, report = deck.absolute(), cache.absolute(), report.absolute()
    for path in (deck, cache, report):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('verification paths cannot traverse symlinks')
    cache.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=cache) as directory:
        collection = Collection(str(Path(directory) / 'collection.anki2'))
        try:
            collection.import_anki_package(ImportAnkiPackageRequest(package_path=str(deck)))
            before = collection.db.all('select id, nid, ord from cards order by id')
            assert collection.note_count() == 36 and len(before) == 36
            note_ids = collection.find_notes('')
            names, media = set(), set()
            for note_id in note_ids:
                note = collection.get_note(note_id)
                names.add(tuple(note.keys()))
                assert len(note.fields) == 12
                assert note['Image'] == ''
                assert note['Pinyin'] and note['Traditional'] and note['Sentence Pinyin']
                for field in ('word_audio', 'sentence_audio'):
                    match = re.fullmatch(r'\[sound:([a-f0-9]{64}\.mp3)\]', note[field])
                    assert match, note[field]
                    filename = match[1]
                    content = (Path(collection.media.dir()) / filename).read_bytes()
                    assert content == (deck.parents[2] / 'examples/mandarin/qualified-pilot/media' / filename).read_bytes()
                    media.add(filename)
            for card_id, _, _ in before:
                card = collection.get_card(card_id)
                assert card.question() and '<ruby' in card.answer()
                assert 'mandarinTraditionalSection' in card.answer()
                assert '{{' not in card.answer()
            reviewed = collection.get_card(before[0][0])
            reviewed.start_timer()
            collection.sched.answerCard(reviewed, 3)
            scheduling = collection.db.all('select id, type, queue, due, ivl, reps, lapses from cards order by id')
            collection.import_anki_package(ImportAnkiPackageRequest(package_path=str(deck)))
            assert collection.db.all('select id, nid, ord from cards order by id') == before
            assert collection.db.all('select id, type, queue, due, ivl, reps, lapses from cards order by id') == scheduling
            assert collection.db.scalar('select count(*) from revlog') == 1
            result = {'anki_version': importlib.metadata.version('anki'), 'deck_sha256': hashlib.sha256(deck.read_bytes()).hexdigest(),
                'notes': collection.note_count(), 'cards': len(before), 'media_verified': len(media), 'field_names': [list(n) for n in names],
                'reimport_preserved_ids_and_scheduling': True, 'rendered_all_cards': True,
                'gui_clients_exercised': [], 'mobile_clients_exercised': [], 'passed': True}
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps(result, ensure_ascii=False))
        finally:
            collection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deck', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    verify(**vars(parser.parse_args()))
