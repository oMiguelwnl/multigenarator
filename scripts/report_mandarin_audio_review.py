"""Summarize completed Mandarin acoustic evidence offline, including missing calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.korean_grammar_audio import _wav_and_signal
from multilang.services.mandarin_pilot import _input, _verified_media
from multilang.services.qualification_machine_runner import json_bytes, read_json, verify_artifact
from multilang.services.vocabulary_review import _plain_path


def summarize(root: Path, output: Path):
    root, output = _plain_path(root), _plain_path(output)
    data = _input(root)
    requests = {q['id']: q for q in data['requests']}
    signal = []
    for q in requests.values():
        _, info = _wav_and_signal(_verified_media(root, q).read_bytes(), max_audio_seconds=30)
        info['validator'] = 'pcm16-mono-signal-v1'
        signal.append({'request_id': q['id'], **info})
    modes = {}
    for mode in ('asr', 'pronunciation'):
        rows = []
        incomplete = []
        for identifier, q in requests.items():
            path = output / mode / 'results' / identifier
            if not path.exists():
                incomplete.append({'request_id': identifier, 'reference': q['asset']['display_text'],
                    'call_recorded': (output / mode / 'calls' / identifier).exists()})
                continue
            manifest = verify_artifact(path, kind='mandarin-acoustic-result')
            result = read_json(path / 'observation.json')
            binding = {key: result[key] for key in ('mode', 'locale', 'audio_sha256', 'wav_sha256', 'reference', 'request_id')}
            if manifest['binding_sha256'] != canonical_sha256(binding):
                raise ValueError('acoustic result binding drift')
            item = {key: result[key] for key in ('request_id', 'kind', 'reference', 'status', 'transcript', 'transcript_matches', 'scores')}
            item['context_id'] = q['asset']['item_key']
            if mode == 'pronunciation':
                best = (result['response'].get('NBest') or [{}])[0]
                phonemes = [p['Phoneme'] for w in best.get('Words', []) for p in w.get('Phonemes', [])]
                ssml = ElementTree.fromstring(q['asset']['normalized_input']['ssml_text'])
                expected = [s.strip() for element in ssml.iter('phoneme') for s in element.attrib['ph'].split('-')]
                item['assessment_reference_phonemes'] = phonemes
                item['reviewed_spoken_phonemes'] = expected
                item['phonemic_reference_matches_spoken_target'] = [p.replace(' ', '') for p in phonemes] == [p.replace(' ', '') for p in expected]
                item['provider_score_flag'] = (result['scores'].get('AccuracyScore', 0) < 90
                    or result['scores'].get('CompletenessScore', 0) < 100)
            rows.append(item)
        modes[mode] = {'completed': len(rows), 'missing': incomplete, 'items': rows,
            'sentence_matches': sum(r['kind'] == 'sentence' and r['transcript_matches'] for r in rows),
            'sentences_observed': sum(r['kind'] == 'sentence' for r in rows),
            'word_matches': sum(r['kind'] == 'word' and r['transcript_matches'] for r in rows),
            'words_observed': sum(r['kind'] == 'word' for r in rows)}
    report = {'schema': 'mandarin-pilot-acoustic-review-1', 'signal': signal,
        'signal_passed': sum(s['integrity_passed'] for s in signal),
        'total_audio_seconds': sum(s['duration_ms'] for s in signal) / 1000, 'modes': modes,
        'acoustic_review_complete': all(v['completed'] == len(requests) for v in modes.values()),
        'independent_human_review': False, 'tonal_certification': False, 'production_eligible': False,
        'limitations': [
            'ASR transcribes sounds and can choose a different homophone for isolated characters.',
            'Assessment infers pronunciation from characters and may pick a different polyphonic reading.',
            'Assessment reference labels are not independent decoded phonemes; a match does not prove the tone was spoken correctly.',
            'Synthesis and acoustic observations use the same provider; no native-speaker listening has occurred.',
        ]}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'review.json').write_bytes(json_bytes(report))
    print(json.dumps({'signal_passed':report['signal_passed'], 'total_audio_seconds':report['total_audio_seconds'],
        'modes':{k:{kk:vv for kk,vv in v.items() if kk not in ('items','missing')} for k,v in modes.items()},
        'provider_score_flags':sum(r['provider_score_flag'] for r in modes['pronunciation']['items'])}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    summarize(**vars(parser.parse_args()))
