---
name: plan-with-review
description: Reviews claude code plan files
---

# Plan with Review
When creating an implementation plan for any non-trivial task:
1. Draft the plan and present it
2. Immediately delegate to the `staff-engineer` subagent to review the plan
3. Incorporate the staff engineer's feedback and present the revised plan

Do NOT wait for user input between steps. The entire process should be automatic.

## Prompt-Framing Rules for Step 2

When delegating the plan to the `staff-engineer` subagent:

- Send ONLY the raw plan text as the prompt. Start directly with the plan title or first heading.
- Do NOT include framing about who wrote the plan, why it was written, or any conversational context (e.g., "Here's the plan I drafted...", "Please review this plan that I created...")
- Do NOT add review instructions in the prompt — the agent definition already contains them
- Do NOT include preamble, apologies, or meta-commentary about the review process

The reviewer should encounter the plan as an anonymous document, not as something you are asking them to approve.
