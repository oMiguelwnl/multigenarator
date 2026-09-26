"""Bounded Azure acoustic observations for the Mandarin pilot, without an LLM."""
from __future__ import annotations

import base64
import json
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen


class AzureMandarinAnalysis:
    """One request per call; ASR receives no reference text or phrase hints."""

    def __init__(self, settings, *, opener=urlopen):
        if settings.azure_speech_region != 'eastus' or not settings.azure_speech_key:
            raise ValueError('Mandarin pilot analysis requires the configured East US resource')
        self._key = settings.azure_speech_key
        self._opener = opener

    def __call__(self, *, wav_bytes: bytes, mode: str, reference_text: str) -> dict:
        if not 1 <= len(wav_bytes) <= 960044 or not 1 <= len(reference_text) <= 512:
            raise ValueError('Mandarin analysis input exceeds bounds')
        headers = {'Ocp-Apim-Subscription-Key': self._key, 'Accept': 'application/json',
                   'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000'}
        if mode == 'pronunciation':
            parameters = {'ReferenceText': reference_text, 'GradingSystem': 'HundredMark',
                'Granularity': 'Phoneme', 'Dimension': 'Comprehensive',
                'EnableMiscue': True, 'EnableProsodyAssessment': False}
            headers['Pronunciation-Assessment'] = base64.b64encode(json.dumps(parameters).encode()).decode('ascii')
        elif mode != 'asr':
            raise ValueError('Unknown Mandarin analysis mode')
        request = Request(
            'https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/'
            'cognitiveservices/v1?language=zh-CN&format=detailed&profanity=raw',
            data=wav_bytes, headers=headers, method='POST',
        )
        try:
            response = self._opener(request, timeout=30)
        except URLError as exc:
            if not isinstance(exc.reason, ssl.SSLCertVerificationError):
                raise
            # TLS failed before sending the HTTP request. A single new connection
            # still verifies certificates normally; never retry unknown delivery.
            response = self._opener(request, timeout=30)
        with response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError('Mandarin analysis response exceeds bounds')
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError('Mandarin analysis response must be an object')
        return result
