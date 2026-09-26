"""Collect Azure ASR/assessment evidence for exact verified Mandarin pilot bytes.

No LLM is called. In-flight markers prevent automatic retries of unknown outcomes.
The scores are provider observations, not native-speaker or tonal certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.korean_grammar_audio import _wav_and_signal
from multilang.services.mandarin_audio_review import AzureMandarinAnalysis
from multilang.services.mandarin_pilot import _input, _verified_media
from multilang.services.qualification_machine_runner import (
    _locked,
    json_bytes,
    persist_artifact,
    read_json,
    verify_artifact,
)
from multilang.services.vocabulary_review import _plain_path
from multilang.settings import Settings


def text_key(text):
    return ''.join(c for c in unicodedata.normalize('NFC', text)
                   if not c.isspace() and not unicodedata.category(c).startswith('P'))


def analyze(root: Path, mode: str, output: Path):
    root, output = _plain_path(root), _plain_path(output)
    data = _input(root)
    client = AzureMandarinAnalysis(Settings())
    reports = []
    with _locked(output / mode):
        for request in data['requests']:
            identifier = request['id']
            if canonical_sha256(request['asset']) != identifier:
                raise ValueError('audio request drift')
            path = _verified_media(root, request)
            raw = path.read_bytes()
            wav, signal = _wav_and_signal(raw, max_audio_seconds=30)
            signal['validator'] = 'pcm16-mono-signal-v1'
            reference = request['asset']['display_text']
            binding = {'mode': mode, 'locale': 'zh-CN', 'audio_sha256': hashlib.sha256(raw).hexdigest(),
                       'wav_sha256': hashlib.sha256(wav).hexdigest(), 'reference': reference,
                       'request_id': identifier}
            digest = canonical_sha256(binding)
            call, result = output / mode / 'calls' / identifier, output / mode / 'results' / identifier
            if result.exists():
                manifest = verify_artifact(result, kind='mandarin-acoustic-result')
                if manifest['binding_sha256'] != digest:
                    raise ValueError('acoustic result binding drift')
                observation = read_json(result / 'observation.json')
            else:
                if call.exists():
                    raise ValueError('acoustic call outcome is unknown; inspect before retry')
                persist_artifact(call, kind='mandarin-acoustic-request', binding=digest,
                                 files={'request.json': json_bytes(binding)})
                response = client(wav_bytes=wav, mode=mode, reference_text=reference)
                best = (response.get('NBest') or [{}])[0]
                transcript = best.get('Display') or response.get('DisplayText', '')
                assessment = best.get('PronunciationAssessment', best)
                observation = {**binding, 'note_guid': request['note_guid'], 'kind': request['kind'],
                    'signal': signal, 'status': response.get('RecognitionStatus'), 'transcript': transcript,
                    'transcript_matches': text_key(transcript) == text_key(reference),
                    'scores': {k: assessment[k] for k in ('AccuracyScore', 'FluencyScore', 'CompletenessScore', 'PronScore') if k in assessment},
                    'response': response, 'independent_human_review': False, 'production_eligible': False}
                persist_artifact(result, kind='mandarin-acoustic-result', binding=digest,
                                 files={'observation.json': json_bytes(observation)})
            reports.append(observation)
            print(f'{mode}: {len(reports)}/{len(data["requests"])}', flush=True)
        summary = {'mode': mode, 'items': reports, 'count': len(reports),
            'signal_integrity_passed': sum(x['signal']['integrity_passed'] for x in reports),
            'transcript_matches': sum(x['transcript_matches'] for x in reports),
            'total_audio_seconds': sum(x['signal']['duration_ms'] for x in reports) / 1000,
            'same_provider_as_synthesis': True, 'independent_human_review': False,
            'tonal_certification': False, 'production_eligible': False}
        (output / mode / 'summary.json').write_bytes(json_bytes(summary))
        print(json.dumps({k:v for k,v in summary.items() if k != 'items'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['asr', 'pronunciation'], required=True)
    parser.add_argument('--allow-provider-calls', action='store_true')
    args = vars(parser.parse_args())
    if not args.pop('allow_provider_calls'):
        parser.error('Azure audio analysis requires --allow-provider-calls')
    analyze(**args)
