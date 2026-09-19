# Korean grammar course v1

Original Korean examples and Portuguese explanations for G0–G13. G0 is guided
orientation, explicitly authorized by the project owner; the strict sequence
starts in G1. The complete inventory has 108 lessons (8 guided, 100 strict).

- `cards-g0-g6.json`, `cards-g7-g13.json`: lesson content and dependencies.
- `lexical-support.json`: 57 lexical entries and 29 construction-owned uses,
  with lemma/POS/sense choices and explicit introduction points.
- `grammar-observations.json`: semantic observations of each example and spoken
  sample, distinct from the dependency closure. Not an approval receipt.
- `bootstrap-lessons.json`: 57 source-bound lexical labels with original
  Portuguese definitions and disambiguating contexts, before guided G0.
- `lexical-source-rows.tsv`: 75 exact selected rows from the approved NIKL
  source, decoded from CP949 to UTF-8. Row ordering and publisher homograph
  numbers are retained. No frequency reranking or source definition rewriting.
- `attribution.txt`: attribution from the existing approved source bundle.
- `text-review-summary.json`: historical hashes and scope of the initial three
  AI editorial passes, superseded by the production corrections. It does not
  substitute for current morphology, review or audio gates.
- `production-review-summary.json`: current content, review, audio and delivery
  hashes for the completed local grammar package; references the full local
  production receipts and states the exact automated verification scope.

The source is NIKL **한국어 학습용 어휘 목록**, published 2003-06-04, revised
2019-05-30. The existing source manifest records `approved-redistribution`;
this work reuses that decision, not a new model-generated rights claim.
Full source SHA-256:
`3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064`.
Selected UTF-8 rows SHA-256:
`93e3cee8c4edbb4db999df0da3760b68f3ad0eaa8193f37a539b6a87a0bff807`.
Each row identity is SHA-256 of the decoded original line without its newline.
Publisher homograph numbers are not assumed to be sense IDs in other dictionaries.

Curriculum references: [Sejong](https://www.iksi.or.kr/lms/main/curriculum.do)
and [NIKL Korean Basic Dictionary](https://krdict.korean.go.kr/eng/mainAction).
Examples and Portuguese definitions are original, not copied dictionary text.
Specific checks used [되다](https://krdict.korean.go.kr/eng/dicSearch/SearchView?ParaWordNo=89858&nation=eng&nationCode=6)
(sense 13, work out), [쉽다](https://krdict.korean.go.kr/eng/dicSearch/SearchView?ParaWordNo=66314&nation=eng),
[열리다](https://krdict.korean.go.kr/eng/dicSearch/SearchView?ParaWordNo=74352),
[앉히다](https://krdict.korean.go.kr/eng/dicSearch/SearchView?ParaWordNo=16014&nation=eng),
and NIKL guidance on [돼요](https://www.korean.go.kr/front/mcfaq/mcfaqView.do?mcfaq_seq=6761&mn_id=&pageIndex=1)
and [reported questions](https://korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=216&pageIndex=1&qna_seq=315958).

The 2026-09-19 local grammar delivery contains 165 cards: 57 lexical bootstrap,
8 guided G0 and 100 strict G1–G13, with 159 distinct Azure SunHiNeural MP3s
covering 330 audio fields. Three independent AI review contexts accepted all
165 final subjects. Audio status is `automated_integrity_passed`, without a
human-listening or comprehensive phonetic-certification claim.

The final APKG passed actual Anki 26.8.1 backend import/reimport, 660 rendered
side/viewport checks and playback of all 159 media files in headless Chromium.
Native desktop GUI and mobile-app acceptance remain outside this local result.
See `docs/korean-grammar-course.md` for the package, receipts, preparation and
evidence contracts. Authoring previews still require their own release evidence.
