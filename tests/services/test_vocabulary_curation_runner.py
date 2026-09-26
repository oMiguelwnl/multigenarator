"""Curation calls have a shared budget, cached responses and source-bound results."""

import hashlib
import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_ai_transport import AITransportLimits, MachineRunBudget


def _packet(tmp_path):
    packet={"language":"en","groups":[{"entry_id":"one","lemma":"cat","pos":"NOUN",
            "sense_candidates":[{"candidate_id":"sense","glosses":["a domestic feline"],"tags":[]}],
            "readings":[],"forms_for_review":[]}],"generation_status":"deferred_by_user"}
    packet['packet_sha256']=canonical_sha256(packet)
    path=tmp_path/'packet.json'
    path.write_text(json.dumps(packet))
    return path,hashlib.sha256(path.read_bytes()).hexdigest()


def _budget(max_calls=2):
    return MachineRunBudget(total_cost=Decimal('1'),max_calls=max_calls,input_cost_per_million=Decimal('1'),
                            output_cost_per_million=Decimal('1'),price_basis='test fixture')


class Transport:
    model='fixture/model'
    limits=AITransportLimits(max_output_tokens=300)

    def __init__(self, *, invalid=False):
        self.calls=0
        self.invalid=invalid

    def input_token_upper_bound(self,messages,schema):
        return 200

    def complete(self,messages,schema):
        self.calls += 1
        payload={'decisions':[]} if self.invalid else {'decisions':[{
            'i':0,'decision':'include','senses':[0],'display':'cat','forms':[],'reason':'general_use'}]}
        return SimpleNamespace(payload=payload,model_dump=lambda **kw:{'payload':payload,'response_model':self.model,
            'input_tokens':100,'output_tokens':60,'input_token_upper_bound':200})


def test_two_reviews_are_cached_and_bound_to_both_source_and_model(tmp_path):
    from multilang.services.vocabulary_curation_runner import review_selection_packet

    path,digest=_packet(tmp_path)
    transport=Transport()
    args=dict(packet=path,packet_sha256=digest,output=tmp_path/'run',transport=transport,budget=_budget())
    result=review_selection_packet(**args)
    assert result['decisions'][0]['status']=='machine_consensus'
    assert transport.calls==2
    assert review_selection_packet(**args)==result
    assert transport.calls==2
    transport.model='changed/model'
    with pytest.raises(ValueError,match='binding'):
        review_selection_packet(**args)


def test_shared_budget_stops_before_the_next_paid_call(tmp_path):
    from multilang.services.vocabulary_curation_runner import review_selection_packet

    path,digest=_packet(tmp_path)
    transport=Transport()
    with pytest.raises(ValueError,match='call_budget_exceeded'):
        review_selection_packet(packet=path,packet_sha256=digest,output=tmp_path/'run',transport=transport,budget=_budget(1))
    assert transport.calls==1
    ledger=json.loads((tmp_path/'run/budget-ledger.json').read_text())
    assert ledger['reserved_calls']==1


def test_invalid_response_consumes_reservation_without_automatic_retry(tmp_path):
    from multilang.services.vocabulary_curation_runner import review_selection_packet

    path,digest=_packet(tmp_path)
    transport=Transport(invalid=True)
    args=dict(packet=path,packet_sha256=digest,output=tmp_path/'run',transport=transport,budget=_budget())
    with pytest.raises(ValueError):
        review_selection_packet(**args)
    with pytest.raises(ValueError):
        review_selection_packet(**args)
    assert transport.calls==1
    assert json.loads((tmp_path/'run/budget-ledger.json').read_text())['reserved_calls']==1


def test_tampered_packet_never_calls_provider(tmp_path):
    from multilang.services.vocabulary_curation_runner import review_selection_packet

    path,digest=_packet(tmp_path)
    path.write_text('{}')
    transport=Transport()
    with pytest.raises(ValueError,match='checksum'):
        review_selection_packet(packet=path,packet_sha256=digest,output=tmp_path/'run',transport=transport,budget=_budget())
    assert transport.calls==0
