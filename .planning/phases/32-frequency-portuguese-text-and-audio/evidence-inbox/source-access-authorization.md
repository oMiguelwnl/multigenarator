# Korean Source-Access Authorization

Decision: `authorize-bounded-retrieval`

This authority grants only one bounded retrieval from the selected official NIKL page. It does not grant transformation, redistribution, asset commit, provider use, Azure use, production database mutation, release, or publication authority.

```json
{
  "bindings": [
    {
      "byte_count": 1275,
      "path": "source-access-preflight.json",
      "sha256": "a5e977457f6781e436e043bd9236c0c06d939f7e7b09e660ae40ac556b3526c3"
    }
  ],
  "expected_kind": "source-access",
  "expectations": {
    "attachment_filename_rule": "response-derived-nfc-korean-learning-vocabulary-txt",
    "commercial_downstream_use": "not-authorized-by-this-checkpoint",
    "decision": "authorize-bounded-retrieval",
    "exact_bytes_terms_review": "pending-after-retrieval",
    "fixed_landing_url": "https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
    "intended_use": "retrieve-exact-source-for-rights-and-schema-evidence-only",
    "local_private_storage": "authorized-for-retrieval-evidence-only",
    "public_git_history": "not-authorized",
    "redistribution": "not-authorized",
    "source_decision_sha256": "077f18ee4a32dbac816d237b5d312926bd155297da4e681486353f149cf364dd",
    "source_title": "NIKL Korean learner vocabulary list"
  },
  "kind": "source-access",
  "powers": [
    "retrieve-source"
  ],
  "schema_version": "korean-checkpoint-authority-v1"
}
```
