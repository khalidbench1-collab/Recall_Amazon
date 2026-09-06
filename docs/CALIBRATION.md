# Grader calibration

Every case below was scored by the live model. The bands are what a fair teacher would accept; the scores are what the grader actually produced. Reproduce with `RECALL_CALIBRATION=1 pytest tests/test_calibration.py`.

**Model:** `us.anthropic.claude-sonnet-4-6`  
**Run:** 06 September 2026

| Case | What the learner said | Band | Score | What it said back |
|---|---|---|---|---|
| exact answer | the capital of peru is lima | 5-5 | 5 | Perfect, you got it exactly right. |
| correct but hedged and full of filler | um I think it's uh Lima right | 4-5 | 5 | Yes, you got it right, Lima is the capital of Peru! |
| correct through paraphrase, no shared wording | it decides how much longer the gap gets each time you get one right | 4-5 | 4 | Good, but you missed that the ease factor specifically multiplies the interval each successful review. |
| both halves correct in the learner's own words | mitosis makes two copies that are the same for repairing you and meiosis makes four sex cells that are all different | 4-5 | 4 | Good answer, but you missed the key term 'haploid' to describe the gametes meiosis produces. |
| right idea, the key distinction missing | they're both types of cell division that happen in the body | 1-3 | 1 | You only identified that both are cell division — you missed the key differences in cell number, ploidy, and purpose. |
| half the answer, confidently stated | mitosis makes two identical cells | 2-4 | 3 | You missed that the cells are diploid and that mitosis is for growth and repair. |
| right subject area, substance wrong | mitosis makes four different cells and meiosis makes two the same | 0-2 | 0 | You got both processes completely backwards and swapped the cell counts too. |
| confidently wrong | it's definitely Rio de Janeiro | 0-1 | 0 | That's wrong — you confused Peru's capital Lima with Rio de Janeiro, which is in Brazil. |
| transcription mangled the word, meaning intact | the capital of peru is leemah | 4-5 | 5 | Perfect, you got it right — Lima is indeed the capital of Peru. |
| admits not knowing | honestly I have no idea | 0-1 | 0 | You didn't recall anything — mitosis makes two diploid cells, meiosis makes four haploid gametes. |
| unrelated answer | the treaty of westphalia established state sovereignty | 0-1 | 0 | That's completely unrelated — you described a historical treaty, not cell division at all. |

**11 of 11 inside band.**
