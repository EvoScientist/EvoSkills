# Rebuttal Tactics

Detailed tactical guidance for writing rebuttals. These 18 rules cover structure, content, tone, and advanced tactics. See SKILL.md for the overall strategy (diagnosis, champion strategy, counterintuitive principles).

## Structure Rules

**1. Address biggest concerns first, not in reviewer order.**
The AC reads your rebuttal quickly. Put the most important answers at the top, not buried under minor issues. The first thing the AC reads should be your strongest response.

**2. Consolidate shared concerns into a "Common Response" section.**
If two reviewers both question the baselines, write one strong response instead of two weaker ones. This saves word count and signals you understand the pattern across reviews.

**3. Quote the concern concisely, then answer directly.**
Lead with the answer. Put supporting details after. Reviewers skim — front-load the conclusion, not the reasoning.

**4. Use resolution-oriented headers.**
Write "Clarifying statistical significance" not "Is the improvement significant?" Problem-oriented headers make your rebuttal feel defensive. Resolution-oriented headers signal confidence.

## Content Rules

**5. Do, don't promise.**
Provide the experiment, explanation, or revised text inline. "We will add in the revision" is the weakest possible response. If you ran a new experiment, show the table now. Actions speak louder than promises.

**6. If it's already in the paper, cite the exact location AND restate it.**
Never say "as discussed in Section 3.2" and leave it at that. The AC likely won't re-read Section 3.2 during the discussion phase. Quote or summarize the relevant content in the rebuttal itself.

**7. Use data over argumentation.**
One new experiment table beats three paragraphs of explanation. Reviewers trust numbers, not rhetoric. If you can run a quick experiment during the rebuttal period, do it.

**8. Stay self-contained.**
The AC may not re-read your paper during the discussion. Reintroduce acronyms, method names, and key setup details in the rebuttal. Don't assume familiarity.

**9. Address the underlying intent, not just the literal question.**
"Why didn't you compare with Method X?" often means "I'm not convinced your method is competitive." Answering the literal question (adding Method X) without addressing competitiveness misses the point. Solve the real concern.

**10. Never introduce new problems.**
Every new claim in a rebuttal is a new attack surface. If you mention a new capability, a reviewer may ask "where's the evidence?" Keep the scope tight — defend what's in the paper, don't expand it.

## Tone Rules

**11. Start with genuine positives.**
A sentence like "We appreciate R2's recognition that our approach handles X well" reminds the AC of your paper's strengths before you dive into defense. This is strategic, not just polite.

**12. Write "We agree" not "We acknowledge."**
"Acknowledge" sounds reluctant, as if you're conceding under pressure. "Agree" sounds collaborative and confident. Small word choices shape perception.

**13. Write "revised version" not "final version."**
"Final version" implies the paper is already accepted. "Revised version" respects the process and sounds professional.

**14. Be transparent about constraints.**
If you cannot run a requested experiment due to compute budget or venue page limits, say so honestly. Honesty builds trust; silence looks evasive. Most reviewers understand resource constraints.

**15. Thank reviewers for constructive additions.**
When a reviewer catches typos or suggests useful citations, a quick "Thank you — added" costs nothing and builds goodwill. Reviewers are more receptive to your arguments when they feel respected.

## Advanced Tactics

**16. Flag unreasonable reviews professionally.**
If a reviewer's concern contradicts the other reviewers, reference this factually: "We note that R1 and R3 both found the experimental evaluation comprehensive, which seems to address R2's concern about evaluation scope." Never attack the reviewer — let the contradiction speak for itself.

**17. Peer-check your critical responses.**
Have a colleague verify your 1-2 most important answers. A fresh pair of eyes catches logical gaps, unclear phrasing, and missing evidence. The rebuttal period is short, but peer review of your rebuttal is worth the time.

**18. Save all reviews permanently.**
Patterns across submissions reveal your blind spots. If three different papers get "limited novelty" feedback, the issue is likely in how you frame contributions, not in the contributions themselves. Build a personal review archive.

---

## Word Count Optimization

For venues with strict word limits (e.g., 500-1000 words), every word must earn its place:

- **Tables count as fewer words than equivalent prose** — present new results as compact tables instead of narrating them
- **Link to supplementary material** — "See Appendix A in the revised paper for the full ablation" saves word budget for critical responses
- **Merge related concerns** to avoid repeating context — if R1 and R3 both question robustness, address them together in one response
- **Cut boilerplate to one line** — "We thank all reviewers for their feedback" is sufficient; no need for a full paragraph of gratitude
- **Use bullet points instead of paragraphs** — they're denser and easier to scan
- **Prioritize ruthlessly** — if you can only address 5 of 15 concerns well, pick the 5 that move scores. A shallow response to all 15 is worse than a thorough response to 5

---

## Revision Diff Strategy

When preparing the revised paper alongside the rebuttal:

- **Highlight all changes** using a diff color (blue text is conventional) so reviewers can quickly find modifications
- **Number your changes** and reference them in the rebuttal ("See Change 3 in the revised paper, highlighted in blue")
- **Don't change things reviewers didn't ask about** — unsolicited changes during revision raise suspicion and create new attack surfaces
- **Match every rebuttal promise to a visible change** — if you said "we revised Section 3.2," the revision must show it clearly
