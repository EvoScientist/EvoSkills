# Paper Reading Methodology

Effective paper reading turns passive consumption into active knowledge building. The core method is to read with specific questions in mind and produce structured output for every paper.

## Core Method: Structured Q&A Reading

Use a "paper parsing tree" — a set of specific questions you answer while reading. This prevents the common problem of "I read it but retained nothing."

Before reading, decide what you want to learn:
- Am I reading for technical details (to reproduce or build on this work)?
- Am I reading for analytical understanding (to understand design decisions)?
- Am I reading for field context (to update my literature tree)?

Your reading depth should match your goal.

## Three Levels of Reading Depth

| Level | Goal | Effort | What You Can Do After |
|-------|------|--------|----------------------|
| 1. Technical | Understand all details and terminology | High | Reproduce the method; explain each component; identify implementation subtleties |
| 2. Analytical | Know what problem it solves, why this approach, why it works better | Medium | Explain the paper's motivation and design choices; compare with alternatives |
| 3. Contextual | Know its position in the literature tree; identify limitations and failure cases | Low-Medium | Update your field map; generate new research questions; classify by novelty type |

**Most papers need Level 2-3.** Reserve Level 1 for papers you plan to build on directly.

### Level 1: Technical Reading

- Read the full method section carefully, including supplementary material
- Understand every equation, every design choice
- If unclear, read the code (when available) — code doesn't lie
- After reading, you should be able to re-implement the method from scratch

### Level 2: Analytical Reading

- Focus on Introduction (paragraphs 2-3) and Method overview
- Answer: What problem does this solve? What did they try that didn't work? Why does their approach work better?
- Skip implementation details unless relevant to your work
- After reading, you should be able to explain the paper's story in 2-3 sentences

### Level 3: Contextual Reading

- Skim Abstract, Introduction, and Conclusion
- Answer: What novelty type is this? (Type 1-4 from the literature tree) Where does it fit? What does it build on? What does it enable?
- After reading, you should be able to update your literature tree and identify one limitation or potential failure case

## Structured Paper Summary

Write this summary for every paper you read. A fillable template is available at [../assets/paper-summary-template.md](../assets/paper-summary-template.md).

### Five Required Items

1. **One sentence: the paper's novelty.** What is genuinely new? Force yourself to be specific.
2. **Pipeline summary (a few sentences).** Step 1 does X, Step 2 does Y, Step 3 does Z. This trains your ability to summarize complex methods concisely.
3. **Problem and motivation.** What problem does it solve? Why do existing methods fail? Why does this approach work?
4. **Position in literature tree.** What novelty type (1-4)? What does it build on? Does it suggest new milestone tasks?
5. **Limitations and failure cases.** What are the known limitations? What data or scenarios would break this method?

## Reading Habits for Ideation

### Daily Practice

Read one paper per day and write the structured summary. This habit simultaneously:
- Builds your literature tree incrementally
- Trains summarization ability (critical for writing papers)
- Trains logical expression (articulating why something works)
- Keeps you current with the field

### Active Engagement

- **Discuss inspiring papers immediately.** When a paper excites you, discuss it with colleagues the same day. The conversation deepens understanding and may spark new ideas.
- **Use AI tools during reading.** Ask questions about terminology, background concepts, or related work to accelerate comprehension.
- **Read code when needed.** For Level 1 reading, the code often reveals details the paper omits. Understanding the implementation distinguishes deep expertise from surface familiarity.

### Building Field Vision

Paper reading is not just for individual papers — it's for building a comprehensive map of your field:
- After every paper, update your novelty tree and challenge-insight tree (see [literature-tree.md](literature-tree.md))
- Periodically review your literature trees to identify gaps and emerging trends
- Compare your trees with survey papers to check for blind spots
