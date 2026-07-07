# Generation Report

job_id=1b268cfa-e1a7-4091-9351-5de4b7982b69
language=da
source_type=frequency
job_status=partial
card_count=2
export_status=partial
export_path=danish-test-deck\1b268cfa-e1a7-4091-9351-5de4b7982b69.apkg
export_sha256=c031440c11259d415ac323e8bae3682db18df68dc99df7001652777407bb81fb

## Counts

text_total=5
accepted=2
review_required=3
failed=3
level_counts={'1': 2, '2': 0, '3': 0}
duplicate_lemma_keys=0
duplicate_words=0
invalid_translations=0
audio_fallback_count=0

## Gate

gate_passed=True
gate_partial=True
failed_gates=[]
warning_gates=['incomplete_frequency_deck', 'review_required_text']
blocking_issues=[]
warnings=['frequency deck has 2/3000 cards, total missing 2998 cards, level_1 missing 998 cards, level_2 missing 1000 cards, level_3 missing 1000 cards', 'review_required text records: 3']

## Provider Calls

provider_call=provider:elevenlabs operation:audio_sentence status:failure calls:2 retries:0 latency_ms_total:0 avg:0.0 p95:0 tokens:0 cost:0.0 fallbacks:0 circuit_blocks:0
provider_call=provider:elevenlabs operation:audio_word status:failure calls:2 retries:0 latency_ms_total:1743 avg:871.5 p95:0 tokens:0 cost:0.0 fallbacks:0 circuit_blocks:0
provider_call=provider:google_translate operation:audio_sentence status:success calls:2 retries:0 latency_ms_total:742 avg:371.0 p95:270 tokens:0 cost:0.0 fallbacks:0 circuit_blocks:0
provider_call=provider:google_translate operation:audio_word status:success calls:2 retries:0 latency_ms_total:725 avg:362.5 p95:362 tokens:0 cost:0.0 fallbacks:0 circuit_blocks:0
