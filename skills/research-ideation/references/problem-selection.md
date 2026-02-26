# Problem Selection

The most important decision in research is choosing WHAT to work on. A great solution to an unimportant or already-solved problem is still unimportant. This guide provides a systematic framework for evaluating whether a problem is worth your time.

## The Core Question

Before investing months of work, ask: **"Is this problem worth solving?"**

This means asking two things simultaneously:
1. Is the problem important? (Does solving it matter?)
2. Is there room for contribution? (Can you make meaningful progress?)

## How to Find Important Problems

### Think About the Ultimate Form

Ask: "What is the ultimate, ideal form of this technology? What would the world look like if this problem were completely solved?"

Work backwards from that vision to identify the concrete tasks that must be solved along the way. These intermediate tasks — the milestone tasks on the path to the ultimate form — are the important problems.

### Ask Why Current Work Is Limited

Most existing work only runs on certain data, under certain conditions. Ask:
- Why does this method only work on dataset X but not Y?
- Why does it need assumption A? What breaks without it?
- What happens when the input is more complex, more diverse, or more realistic?

The answers reveal the boundaries of current solutions and the problems waiting to be solved.

### Seek New Failure Cases

Don't try to improve a technique on its original benchmark. Instead:
- Apply existing methods to new data settings
- Test on more challenging or realistic inputs
- Try different task formulations

**New failure cases are contributions.** Even if your technique is not novel, experimental conclusions on new data that demonstrate where existing methods fail are valuable and publishable. This is one of the most reliable ways to produce contributions.

### Goal-Driven vs. Idea-Driven Research

| Approach | Description | Risk |
|----------|------------|------|
| Goal-driven | Pursue important tasks, try various methods to make them work | Low — relaxing constraints ensures output |
| Idea-driven | Chase technique improvements without clear task direction | High — getting stuck optimizing benchmarks |

**Recommendation**: Be goal-driven. Pick an important task and make it work. If one method fails, try another. If the task is too hard, relax constraints slightly. This ensures you always produce useful results.

The idea-driven trap: "I improved method X by 0.5% on benchmark Y." This leads to boring, struggling projects with diminishing returns.

## The Well-Established Solution Check

Before committing to a problem, check whether a well-established solution already exists. This check has four levels:

| Level | Situation | Action |
|-------|----------|--------|
| 1 | Same I/O task already has a good solution, just minor gaps | **Switch** — improvement space is too small |
| 2 | Similar tasks across domains all have good solutions | **Switch** — the technical core is solved |
| 3 | Only 1-2 cross-domain tasks have solutions for a similar technical core | **Proceed (good for beginners)** — transfer opportunity |
| 4 | No domain has a good solution for this technical problem | **Proceed (good for experts)** — high novelty if solved |

### Level 1: Direct Solution Exists

Someone has already solved the same task with the same input/output format, and the solution works well. Only minor gaps remain (slightly better metrics, edge cases).

**Action**: Switch problems. Even if you find a clever new angle, the improvement space is small, reviewers will see it as incremental, and the work will not earn respect.

### Level 2: Cross-Domain Solutions Exist

Even if no one has solved your exact task, similar technical challenges in other domains already have good solutions. The fundamental technique is well-understood.

**Action**: Switch problems. Transferring a well-known technique to your domain is straightforward engineering, not research contribution.

### Level 3: Limited Cross-Domain Solutions

Only one or two papers in distant domains address a technically similar problem. The technique is not widely known or applied.

**Action**: Proceed — this is a good opportunity, especially for early-career researchers. Transfer and adapt the technique to your domain. The cross-domain nature provides novelty.

### Level 4: No Known Solution

No domain has a good solution for this technical core problem. The challenge is genuinely unsolved.

**Action**: Proceed — this is high-risk but high-reward. If you solve it, the contribution is unquestionable. Best suited for researchers with deep expertise and tolerance for extended exploration.

## The New Hammer Opportunity

When a breakthrough technique or tool appears (new architecture, new generative model, new training paradigm), a window of opportunity opens:

**Do**: Apply the new tool to YOUR roadmap's milestone tasks. This produces high-impact work because:
- The new tool enables previously impossible results
- You combine the tool's power with your domain expertise
- The results are immediately interesting to both communities

**Don't**: Improve the new tool itself on its original benchmarks. This is tempting but:
- You're competing with the tool's creators (who understand it best)
- Many others will try the same thing (crowded space)
- You add no unique perspective

**Pattern**: Breakthrough tool + your milestone task = high-impact paper.

## Problem Selection Checklist

Before committing to a problem, verify:

- [ ] The problem is connected to an important long-term goal
- [ ] You can articulate why existing methods fail (specific failure cases)
- [ ] The well-established solution check passes (Level 3 or 4)
- [ ] You have access to relevant data or can create it
- [ ] The problem is feasible with your current resources and expertise
- [ ] You can identify at least one plausible solution approach
