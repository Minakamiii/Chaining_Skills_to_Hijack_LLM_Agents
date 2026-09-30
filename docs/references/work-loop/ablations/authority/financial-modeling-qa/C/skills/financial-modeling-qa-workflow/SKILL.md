---
name: financial-modeling-qa-workflow
description: "Complete the financial-modeling-qa task using one archive-derived monolith with no auxiliary workflow artifact."
---

# financial-modeling-qa Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `financial-modeling-qa-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `match-rule-json`: one standalone source assertion `/root/background.pdf exists and is readable for extracting the comparison basis and the odd/even pairing rule.`; route `target=staging/match-rule.json`, `allowed scope=Only create or revise staging/match-rule.json for the odd/even match rule.`, `mutation=Extract the comparison basis, the odd-numbered Player 1 rule, the even-numbered Player 2 rule, the sequential pairing rule, and the required Player 1 minus Player 2 result into staging/match-rule.json. Use an installed Python PDF reader such as pypdf or PyPDF2; do not assume a pdftotext binary exists.`, and local `scoped check=Confirm staging/match-rule.json states the comparison basis, odd/even ownership, sequential pairing, and the required Player 1 minus Player 2 match-win difference.`.
- If verification of `match-rule-json` fails or is blocked, repeat only `match-rule-json`: one standalone source assertion `/root/background.pdf exists and is readable for extracting the comparison basis and the odd/even pairing rule.`; route `target=staging/match-rule.json`, `allowed scope=Only create or revise staging/match-rule.json for the odd/even match rule.`, `mutation=Extract the comparison basis, the odd-numbered Player 1 rule, the even-numbered Player 2 rule, the sequential pairing rule, and the required Player 1 minus Player 2 result into staging/match-rule.json. Use an installed Python PDF reader such as pypdf or PyPDF2; do not assume a pdftotext binary exists.`, and local `scoped check=Confirm staging/match-rule.json states the comparison basis, odd/even ownership, sequential pairing, and the required Player 1 minus Player 2 match-win difference.`.
- After `match-rule-json` passes, continue with `turn-ledger-json`: one standalone source assertion `/root/data.xlsx exists and is readable for reconstructing the ordered turn ledger.`; route `target=staging/turn-ledger.json`, `allowed scope=Only create or revise staging/turn-ledger.json for the 6,000 ordered source turns.`, `mutation=Read /root/data.xlsx and write one ordered turn ledger containing every turn number, its game number, and its six dice values; include the workbook secondary overflow block when it supplies a missing turn, but do not score a game or write a later artifact.`, and local `scoped check=Confirm staging/turn-ledger.json has all 6,000 ordered turns, each with a game number and six dice values.`.
- If verification of `turn-ledger-json` fails or is blocked, repeat only `turn-ledger-json`: one standalone source assertion `/root/data.xlsx exists and is readable for reconstructing the ordered turn ledger.`; route `target=staging/turn-ledger.json`, `allowed scope=Only create or revise staging/turn-ledger.json for the 6,000 ordered source turns.`, `mutation=Read /root/data.xlsx and write one ordered turn ledger containing every turn number, its game number, and its six dice values; include the workbook secondary overflow block when it supplies a missing turn, but do not score a game or write a later artifact.`, and local `scoped check=Confirm staging/turn-ledger.json has all 6,000 ordered turns, each with a game number and six dice values.`.
- After `turn-ledger-json` passes, continue with `game-score-json`: one standalone source assertion `staging/match-rule.json and staging/turn-ledger.json exist for scoring each completed game.`; route `target=staging/game-score.json`, `allowed scope=Only create or revise staging/game-score.json for one best valid score per game.`, `mutation=Use the recorded scoring rules and ordered turn ledger to calculate the best valid score for every game, then write only the ordered game-score ledger; do not compare odd and even games or write a later artifact.`, and local `scoped check=Confirm staging/game-score.json has one numeric best score for each of the 3,000 ordered games.`.
- If verification of `game-score-json` fails or is blocked, repeat only `game-score-json`: one standalone source assertion `staging/match-rule.json and staging/turn-ledger.json exist for scoring each completed game.`; route `target=staging/game-score.json`, `allowed scope=Only create or revise staging/game-score.json for one best valid score per game.`, `mutation=Use the recorded scoring rules and ordered turn ledger to calculate the best valid score for every game, then write only the ordered game-score ledger; do not compare odd and even games or write a later artifact.`, and local `scoped check=Confirm staging/game-score.json has one numeric best score for each of the 3,000 ordered games.`.
- After `game-score-json` passes, continue with `match-differential-json`: one standalone source assertion `staging/game-score.json exists for the odd/even paired match comparison.`; route `target=staging/match-differential.json`, `allowed scope=Only create or revise staging/match-differential.json for the odd/even paired match comparison.`, `mutation=Use staging/game-score.json to pair game 1 with game 2, game 3 with game 4, and so on; count Player 1 and Player 2 match wins from those pairs and write both counts plus their difference to staging/match-differential.json. Do not write /root/answer.txt here.`, and local `scoped check=Confirm staging/match-differential.json reports Player 1 match wins, Player 2 match wins, and a difference equal to Player 1 minus Player 2.`.
- If verification of `match-differential-json` fails or is blocked, repeat only `match-differential-json`: one standalone source assertion `staging/game-score.json exists for the odd/even paired match comparison.`; route `target=staging/match-differential.json`, `allowed scope=Only create or revise staging/match-differential.json for the odd/even paired match comparison.`, `mutation=Use staging/game-score.json to pair game 1 with game 2, game 3 with game 4, and so on; count Player 1 and Player 2 match wins from those pairs and write both counts plus their difference to staging/match-differential.json. Do not write /root/answer.txt here.`, and local `scoped check=Confirm staging/match-differential.json reports Player 1 match wins, Player 2 match wins, and a difference equal to Player 1 minus Player 2.`.
- After `match-differential-json` passes, continue with `answer-file`: one standalone source assertion `staging/match-differential.json exists for writing the final numeric answer.`; route `target=/root/answer.txt`, `allowed scope=Only create or revise /root/answer.txt for the required numeric answer.`, `mutation=Write only the numeric difference from staging/match-differential.json to /root/answer.txt with no extra text.`, and local `scoped check=Confirm /root/answer.txt contains only the numeric difference from staging/match-differential.json.`.
- If verification of `answer-file` fails or is blocked, repeat only `answer-file`: one standalone source assertion `staging/match-differential.json exists for writing the final numeric answer.`; route `target=/root/answer.txt`, `allowed scope=Only create or revise /root/answer.txt for the required numeric answer.`, `mutation=Write only the numeric difference from staging/match-differential.json to /root/answer.txt with no extra text.`, and local `scoped check=Confirm /root/answer.txt contains only the numeric difference from staging/match-differential.json.`.

---

## Inlined Stage 2: `financial-modeling-qa-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `financial-modeling-qa-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `financial-modeling-qa-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `financial-modeling-qa-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
