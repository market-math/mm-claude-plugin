---
name: plan-with-review
description: Reviews claude code plan files
argument-hint: [auto [cap]]
---

# Plan with Review

Two modes:
- **Default** (`/plan-with-review`): user-gated. Each round, show the staff engineer's review and let
  the user decide what to apply and whether to run another pass.
- **Auto** (`/plan-with-review auto [n]`): autonomous review loop. Claude applies the points it judges
  valid, keeps running passes until the review converges, then presents the result and asks once before
  finalizing. Trigger only when the user includes the literal token `auto`. An optional integer `n`
  (>= 2) overrides the pass cap (default 6); reject an invalid `n` (`0`, negative, non-integer, or the
  degenerate `1`) by falling back to the default 6 and saying so in one line.

## Reviewer continuity (memory)

Run the reviewer as **one continued agent across passes**, not a fresh subagent each time:

- **First pass:** spawn `staff-engineer` with the Agent tool as an **unnamed, foreground subagent**:
  do not pass a `name`, and do not set `run_in_background`. Its review returns as the tool result, and
  that result includes an `agentId` for continuation; keep that `agentId`. Do **not** spawn it as a
  named or backgrounded teammate: on Claude Code v2.1.195 that path can leak write tools to the
  read-only reviewer, and because the reviewer has no `SendMessage` tool it cannot deliver its review
  back at all (the lead just gets a "finished" ping with no text). The plugin's `PreToolUse` hook is a
  backstop for the leak; the unnamed-subagent path, where the `Read, Grep, Glob` allowlist is reliably
  enforced, avoids both problems outright.
- **Later passes:** continue that same agent with `SendMessage` to its `agentId`,
  sending the revised plan per *Continuation framing*. It resumes from its transcript with full memory,
  so it de-dups its own concerns and reports, each pass, which prior items are **RESOLVED**, still
  **OPEN**, or **NEW**. That report is its normal returned output (it does not need `SendMessage` in its
  own tools, and no team session is required).

Continuation is **same-session only** (the `agentId` is not durable across sessions), which is exactly
the scope one review loop needs.

**Fallback (no memory).** If continuation is unavailable on a run (the Agent tool is not permitted, or
`SendMessage` to the `agentId` errors), drop to the original design: a **fresh** reviewer each pass plus
**Claude-side de-dup**, with convergence computed from your own pass-to-pass tracking instead of the
reviewer's self-report. Every safety property below is defined for both paths. Caveat: fallback de-dup
can miss a *reworded* re-raise of a dismissed Critical, so prefer the memory path where available.

## Default workflow

1. Draft the implementation plan and present it to the user.
2. Delegate the plan to `staff-engineer` (first pass: *Prompt-framing rules*; later passes: continue the
   same reviewer per *Continuation framing*, or a fresh reviewer in fallback mode).
3. Present the review (see *Presenting the review*) and wait for the user's free-form reply.
4. Parse the reply (see *Parsing the user's reply*) and produce a revised plan that reflects only the
   items the user accepted, with any per-item overrides they specified.
5. Ask the user, in a single question, whether to run another review pass on the revised plan. Use the
   *Convergence check* to set the recommended answer: recommend **finalize** when the review has
   converged relative to the user's choices; otherwise recommend **another pass**. On another pass,
   return to step 2 with the revised plan. On finalize, stop.

If the staff engineer's first review contains no items in any of the four sections, skip steps 3-5 and
present the original plan as final.

## Auto workflow

When `auto` appears as an argument, run the loop yourself with no per-item or per-pass prompting, except
the single checkpoint at the end.

1. Draft the implementation plan.
2. Delegate the current plan to `staff-engineer` (first pass per *Prompt-framing rules*; later passes
   continue the same reviewer per *Continuation framing*, or fresh + de-dup in fallback). Print a
   one-line progress note per pass (pass #, items raised, converged?).
3. Evaluate the review with judgement (see *Evaluating the review*) and produce a revised plan. Append a
   *Pass ledger* entry.
4. Run the *Convergence check*. If the plan has not converged and the pass cap is not reached, return to
   step 2 with the revised plan. Otherwise continue to step 5.
   - **Escalation override:** if a **Critical** remains unresolved only because you dismissed it and the
     reviewer keeps reporting it OPEN (memory mode), or your own tracking shows the same Critical
     re-raised across passes after a dismissal (fallback mode), do **not** auto-converge. Go to step 5
     and surface the disagreement plainly.
5. Present the final plan, a concise pass-by-pass summary (from the *Pass ledger*), and a recommendation:
   - If converged: recommend finalizing.
   - If the cap was reached with items still open: say so and recommend caution / manual review instead.
   Then ask the user ONCE: finalize, or run one more pass. On finalize, proceed to plan approval
   (`ExitPlanMode`). On one more pass, return to step 2, then ask again.

If the staff engineer's first review contains no items in any of the four sections, skip the loop and
present the original plan as final.

## Evaluating the review (judgement)

Used by Auto mode, and by Default mode when the user delegates judgement ("use your judgement").

The `staff-engineer` agent verifies its claims against the codebase before writing them, so do **not**
blanket re-verify every point; that is redundant and slow.

- **Apply** points that are correct and in-scope (the default for most items; trust the reviewer's
  verification).
- **Skip** false positives, incorrect, or out-of-scope points; record a one-line reason for each.
- **Independently confirm before acting on OR dismissing** any load-bearing item: any **Critical** issue
  (confirming before you *skip* it matters as much as before you *apply* it, since a wrongly dismissed
  Critical is the worst failure mode), any claim the reviewer flagged **unverified**, and anything you
  genuinely doubt. Use a quick targeted check (read the file, run a read-only query), not a full
  re-review.
- **Answer Questions** directly; confirm empirically when the answer is a fact about the codebase.

## Convergence check

The plan has **converged** when the latest pass shows **no NEW** and **no still-OPEN** Critical Issues or
Significant Concerns. Questions and Minor Suggestions never block convergence on their own (lingering
nits cannot stall the loop). The first pass is never converged. A **disputed open Critical** (one that
is open only because you dismissed it) does not count as converged; escalate it per the Auto-workflow
override.

- In **memory mode**, the NEW/OPEN signal is the reviewer's RESOLVED/OPEN/NEW self-report.
- In **fallback mode**, it is your own pass-to-pass de-dup of fresh reviews.

A hard pass cap (default **6**, override via `auto <n>`, `n` >= 2) bounds total cost and guards against
unbounded looping / API spend. If the loop hits the cap while items remain open, stop and report
"cap reached without convergence, review manually" rather than recommending finalize.

**Default mode** computes the same signal but relative to what the *user applied/declined*: an item the
user has chosen to decline is resolved-by-user-decision and does not drive an "another pass"
recommendation.

## Cost & interruption (Auto mode)

Each pass runs the reviewer, which reads the codebase, so passes have real token and time cost. The pass
cap bounds total spend; the user can interrupt at any time; and the per-pass progress note (step 2) lets
the user watch and bail. There is no per-pass prompt; that is the point of Auto mode.

## Prompt-framing rules

When delegating the plan to the `staff-engineer` subagent on the **first** pass:

- Send ONLY the raw plan text as the prompt. Start directly with the plan title or first heading.
- Do NOT include framing about who wrote the plan, why it was written, or any conversational context.
- Do NOT add review instructions in the prompt; the agent definition already contains them.
- Do NOT include preamble, apologies, or meta-commentary about the review process.

The reviewer should encounter the plan as an anonymous document, not as something you are asking them to
approve.

## Continuation framing

For **later** passes that continue the same reviewer (memory mode):

- Send the revised raw plan plus a **neutral, factual diff of what changed** since its last review.
- Do NOT tell it which of its points were or were not applied, do NOT justify non-application, and do NOT
  editorialize, argue, or ask it to approve or to stop raising anything. It judges for itself whether
  each prior concern is now resolved; that independence is the point.
- Preserve authorship anonymity (no author identity). The reviewer may know it is re-reviewing an
  evolving document; that is inherent to iterative review and acceptable.
- **Memory replaces re-reading only for unchanged context.** Any new or changed claim about the codebase
  that the revision introduces must still be verified against the files; the reviewer must not
  rubber-stamp new assertions from memory.

## Presenting the review

Show the staff engineer's verbatim output (all four sections: Critical Issues, Significant Concerns,
Questions, Minor Suggestions) exactly as returned. Then a horizontal rule (`---`). Then a flat numbered
action list covering every concrete item across all four sections, one per line:

```
1. [Critical] <one-sentence summary>
2. [Significant] <one-sentence summary>
3. [Question] answer: <the question, condensed>
4. [Minor] <one-sentence summary>
```

End with this exact prompt to the user:

> Reply with which items to apply (e.g. "apply 1, 3, 5; skip 2; for 4 do X instead"), or `all` / `none` / `use your judgement`.

## Parsing the user's reply

Accept any of:
- `all`: apply every item.
- `none`: apply nothing; revised plan equals the original draft. State explicitly that no changes were
  applied.
- A list or range of item numbers (`1, 3, 5` or `1-3`): apply only those.
- Free-form per-item overrides (`apply 1 and 3, skip 2, for 4 do X instead`): apply the listed items,
  honoring overrides.
- `use your judgement` (or similar delegation): decide which items to apply per *Evaluating the
  review*, apply them, and report your per-item dispositions.

Only ask a follow-up clarifying question if the reply is genuinely ambiguous. Otherwise proceed directly
to producing the revised plan.

## Pass ledger

In Auto mode, keep a compact inline table across passes so the convergence comparison stays reliable:

| Pass | Items raised | Applied | Skipped (reason) | New substantive? |
|------|--------------|---------|------------------|------------------|

In memory mode the reviewer's RESOLVED/OPEN/NEW report carries the open-items list; in fallback mode you
maintain the open list from this ledger.
