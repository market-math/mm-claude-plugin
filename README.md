Send claude's initial plan through a critical review. You might be surprised with how many issues this finds with initial plans.
Try it with 5-10 initial plans and see how many issues it finds.

## Installation
Within claude code:
```
/plugin marketplace add market-math/mm-claude-plugin
/plugin install plan-review
```
Then close and restart the claude session.
## Usage
- `/plan-with-review`: draft a plan, run the staff engineer review, then show the review and wait for your reply on which items to apply and whether to run another pass.
- `/plan-with-review auto [n]`: Claude runs the review loop autonomously with a persistent reviewer. It applies the points it judges valid and in-scope, keeps running passes until the reviewer reports nothing new or unresolved (or the pass cap, default 6, is hit), then presents the result and asks once before finalizing. Pass an integer `n` (>= 2) to override the cap, e.g. `/plan-with-review auto 8`.
