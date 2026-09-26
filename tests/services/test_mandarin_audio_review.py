import base64
import json

import pytest

from multilang.settings import Settings


def test_blind_asr_does_not_send_reference_but_assessment_does():
    from multilang.services.mandarin_audio_review import AzureMandarinAnalysis

    captured = []

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, limit):
            return b'{"RecognitionStatus":"Success","NBest":[]}'

    def opener(request, timeout):
        assert timeout == 30
        captured.append(request)
        return Response()

    client = AzureMandarinAnalysis(
        Settings(_env_file=None, azure_speech_key='fixture', azure_speech_region='eastus'),
        opener=opener,
    )
    for mode in ('asr', 'pronunciation'):
        client(wav_bytes=b'RIFFfixture', mode=mode, reference_text='银行')
    assert 'language=zh-CN' in captured[0].full_url
    assert captured[0].data == b'RIFFfixture'
    assert 'pronunciation-assessment' not in {k.lower():v for k,v in captured[0].header_items()}
    header = {k.lower():v for k,v in captured[1].header_items()}['pronunciation-assessment']
    config = json.loads(base64.b64decode(header))
    assert config['ReferenceText'] == '银行'
    assert config['EnableProsodyAssessment'] is False
    assert config['Granularity'] == 'Phoneme'
    with pytest.raises(ValueError):
        client(wav_bytes=b'RIFFfixture', mode='unknown', reference_text='银行')
    assert len(captured) == 2


def test_certificate_failure_before_http_send_has_one_verified_retry():
    import ssl
    from urllib.error import URLError

    from multilang.services.mandarin_audio_review import AzureMandarinAnalysis

    attempts = []

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, limit):
            return b'{"RecognitionStatus":"Success"}'

    def opener(request, timeout):
        attempts.append(request)
        if len(attempts) == 1:
            raise URLError(ssl.SSLCertVerificationError('TLS handshake failed before HTTP send'))
        return Response()

    client = AzureMandarinAnalysis(
        Settings(_env_file=None, azure_speech_key='fixture', azure_speech_region='eastus'), opener=opener,
    )
    assert client(wav_bytes=b'RIFFfixture', mode='asr', reference_text='银行')['RecognitionStatus'] == 'Success'
    assert len(attempts) == 2


def test_unknown_delivery_outcome_is_never_retried():
    from urllib.error import URLError

    from multilang.services.mandarin_audio_review import AzureMandarinAnalysis

    attempts = []
    def opener(request, timeout):
        attempts.append(request)
        raise URLError('connection closed at unknown phase')

    client = AzureMandarinAnalysis(
        Settings(_env_file=None, azure_speech_key='fixture', azure_speech_region='eastus'), opener=opener,
    )
    with pytest.raises(URLError):
        client(wav_bytes=b'RIFFfixture', mode='asr', reference_text='银行')
    assert len(attempts) == 1
