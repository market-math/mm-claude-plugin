---
name: plan-with-review
description: Reviews claude code plan files
---

# Plan with Review

Two modes:
- **Default** (`/plan-with-review`) — user-gated. Show the staff engineer's review and wait for the user to decide what to apply.
- **Auto** (`/plan-with-review auto`) — incorporate the review automatically with no user gate. Use only when the user includes the literal token `auto` in the invocation.

## Default workflow

1. Draft the implementation plan and present it to the user.
2. Delegate the plan to the `staff-engineer` subagent (see *Prompt-framing rules* below).
3. Present the review (see *Presenting the review* below) and wait for the user's free-form reply.
4. Parse the reply (see *Parsing the user's reply*) and produce a revised plan that reflects only the items the user accepted, with any per-item overrides they specified.
5. Ask the user — single yes/no question — whether to run another review pass on the revised plan. On yes, return to step 2 with the revised plan. On no, stop.

If the staff engineer's review contains no items in any of the four sections, skip steps 3–5 and present the original plan as final.

## Auto mode

When `auto` appears as an argument, run steps 1–2, then automatically incorporate every actionable item from the review and present the revised plan. Do not ask the user anything. This matches the prior behavior of this skill.

## Prompt-framing rules

When delegating the plan to the `staff-engineer` subagent:

- Send ONLY the raw plan text as the prompt. Start directly with the plan title or first heading.
- Do NOT include framing about who wrote the plan, why it was written, or any conversational context.
- Do NOT add review instructions in the prompt — the agent definition already contains them.
- Do NOT include preamble, apologies, or meta-commentary about the review process.

The reviewer should encounter the plan as an anonymous document, not as something you are asking them to approve.

## Presenting the review

Show the staff engineer's verbatim output (all four sections: Critical Issues, Significant Concerns, Questions, Minor Suggestions) exactly as returned. Then a horizontal rule (`---`). Then a flat numbered action list covering every concrete item across all four sections, one per line:

```
1. [Critical] <one-sentence summary>
2. [Significant] <one-sentence summary>
3. [Question] answer: <the question, condensed>
4. [Minor] <one-sentence summary>
```

End with this exact prompt to the user:

> Reply with which items to apply (e.g. "apply 1, 3, 5; skip 2; for 4 do X instead"), or `all` / `none`.

## Parsing the user's reply

Accept any of:
- `all` — apply every item.
- `none` — apply nothing; revised plan equals the original draft. State explicitly that no changes were applied.
- A list or range of item numbers (`1, 3, 5` or `1-3`) — apply only those.
- Free-form per-item overrides (`apply 1 and 3, skip 2, for 4 do X instead`) — apply the listed items, honoring overrides.

Only ask a follow-up clarifying question if the reply is genuinely ambiguous. Otherwise proceed directly to producing the revised plan.
