# Arithmetic teaching and practice history

The parent dashboard links to each child's questions and answers by day. Choose a
date or follow the previous/next practice-day links. Each problem set shows the
stored question, literal answer, expected answer, correctness, and response time.
New teaching activities also show each independent or prompted step. Dates use the
recorded Eastern practice day, including sessions spanning midnight. Old answers
remain visible; assistance was not recorded historically and is not inferred.
Possible duplicate submissions are flagged and retained in the historical totals.

## Teaching progression

`learning.py` supplies deterministic, versioned activities for 2.NBT.B.5–7,
3.NBT.A.2, and 4.NBT.B.4. Other skills retain their existing question flows.
The shared engine separates the idea being learned, number size, and amount of
support. New topic families can add components without redesigning persistence.

The progression checks decomposition, matching place values, combining parts,
regrouping ones, regrouping tens, and multiple regroupings. Subtraction separately
checks matching parts, exchanging in each place, and exchanging across zeros.
Several-addend addition has its own component. Larger arithmetic also shows how
place-value parts line up in written columns.

For example, a child may first identify the hundreds part in 823, then match it
with another hundreds part, then combine matching parts. Regrouping starts with
one exchange on smaller numbers before problems with several exchanges. Each
screen asks for one answer. Worked examples, remembered work, and smaller checks
appear automatically when needed; no help button or parent intervention is required.

- Existing results choose an entry check, never certify unaided knowledge. Strong
  performance starts with a whole-problem check (appropriate for Samuel). Weaker
  history starts with ingredient checks. Response time alone does not trigger help.
- A missed check opens instruction. Two clean guided examples fade the prompts;
  two clean faded examples move to independent practice.
- Three independent correct examples permit moving on. Confirmation requires
  evidence on at least two days. Repeated seeds cannot create additional evidence.
  Confirmed components get spaced review; repeated independent errors reopen teaching.
- A set introduces at most one new guided component. The daily goal budgets actual
  responses, including retries, rather than multiplying twelve problems into dozens
  of steps. An activity already started finishes its bounded sequence; persistent
  difficulty ends in a revisit instead of an endless loop.
- Only the first unaided whole-problem answer updates existing mastery statistics.
  Guided completion is separate. Supported arithmetic does not award speed bonuses.

This is authored instruction, not a runtime AI tutor. Initial teaching coverage is
the arithmetic standards above; fractions, measurement, and other topics do not yet
have component-specific teaching sequences.

## Storage and migration

`0002_learning.sql` adds four tables:

| Table | Purpose |
| --- | --- |
| `learning_state` | Component/band support stage, evidence, and review date |
| `learning_session` | Daily response budget and introduced component |
| `practice_activity` | Immutable versioned prompts/answers and resumable progress |
| `step_response` | Exact input, displayed question, correctness, support, time, and day |

Revision claims and atomic batches commit the response, progress, budget, and
assessment together. Duplicate or stale submissions cannot earn extra credit.
The migration retains all old attempts, scores, levels, and earned mastery. It only
closes superseded duplicate open sessions before adding a unique active-session
index. It does not reconstruct, delete, or relabel historical attempts.

Local SQLite startup applies each SQL migration once. D1 migrations must be applied
with Wrangler before deploying this version, even with teaching disabled: parent
history and session handling use the new schema.

To rehearse against a downloaded SQLite snapshot without modifying it:

```powershell
uv run python tools/check_learning_migration.py backups/SOURCE.db backups/NEW-preview.db
```

The tool backs up the source to a new destination, migrates the copy, verifies all
legacy learner/attempt/mastery values and session fields (except retired-session
end timestamps), checks SQLite integrity, and verifies a second migration is a no-op.
Never use the stale repository database or local D1 as production input.

## Rollout procedure

1. Export a fresh remote D1 backup and rehearse on a copy.
2. Apply `npx wrangler d1 migrations apply mathkids --remote`.
3. Deploy with `MATHKIDS_TEACHING` still `"0"` to expose history first.
4. Enable `MATHKIDS_TEACHING: "1"` in Wrangler vars and deploy when ready to start
   arithmetic teaching. Local uvicorn uses the environment variable of the same name.
5. Review the first sets through parent history before extending teaching to more topics.

Turning the flag back to `"0"` and redeploying returns to the ordinary question
flow; incompatible active sets are closed when accessed. Keep the additive tables:
all collected questions, answers, and learning evidence remain available. Do not
reverse the migration or restore an older database over new practice records.

Validation against the September 9 snapshot preserved 375 attempts, two learners,
and 18 mastery rows exactly. Two superseded open sessions were retired on the copy.
On September 9, the fresh pre-deployment backup passed the same rehearsal and
production migration 0002 was applied. Wrangler configuration now enables teaching.
The pre-deployment export is retained locally under
`backups/mathkids-predeploy-20260909-learning.sql`.
