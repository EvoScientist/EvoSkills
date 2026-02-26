# Literature Tree Construction

Build two complementary trees to map a research field: a **novelty tree** that classifies existing work by contribution type, and a **challenge-insight tree** that maps technical problems to known solutions.

## Four Types of Novelty

Every paper's contribution falls into one of four types. Understanding this hierarchy clarifies where your own work fits.

| Type | Definition | Novelty Level | Example |
|------|-----------|---------------|---------|
| Type 1 | Seminal work defining a milestone task | Highest | First paper to formulate a new task or problem setting |
| Type 2 | Seminal work proposing a novel pipeline or representation | High | New architecture paradigm or data representation |
| Type 3 | Seminal work introducing a novel module | Medium | New attention mechanism, loss function, training strategy |
| Type 4 | Incremental improvement using added modules or tricks | Low | Applying existing techniques to improve an existing pipeline |

**Key insight**: Type 1 contributions have the most lasting impact because they define what the field works on. Type 4 contributions are the easiest to produce but the hardest to make memorable.

## Building the Novelty Tree

### Step 1: Collect Papers

Gather papers in your research direction. Start with survey papers and recent top-venue publications. Follow citation chains in both directions (references and citing papers).

### Step 2: Identify Milestone Tasks (Type 1)

Find the milestone tasks in your field — the fundamental problems that define sub-areas of research. For each milestone task, identify the first paper that formulated it. These are your Type 1 nodes.

Ask: "What are the 3-5 core tasks that this field is trying to solve?"

### Step 3: Classify by Pipeline/Representation (Type 2)

Within each milestone task, identify papers that introduced fundamentally new approaches — new pipelines, architectures, or data representations that changed how subsequent work approached the task.

Ask: "For this task, what are the major paradigm shifts in approach?"

### Step 4: Identify Novel Modules (Type 3)

Within each pipeline/representation, identify papers that introduced specific novel components — new modules, loss functions, training strategies, or mechanisms.

Ask: "Within this approach, what specific innovations moved the needle?"

### Step 5: Classify Incremental Work (Type 4)

Remaining papers that apply existing techniques to existing pipelines without introducing new paradigms, representations, or modules.

### Step 6: Expand as Understanding Deepens

As you read more papers, you may discover new milestone tasks or realize existing classifications need revision. The novelty tree is a living document.

## Building the Challenge-Insight Tree

The challenge-insight tree captures the technical PROBLEMS in a field and the SOLUTIONS people have found for them.

### Step 1: Collect Technical Challenges

As you read papers, extract the technical challenges they identify or address. These often appear in:
- Introduction paragraph 2-3 (problem motivation)
- Related work section (limitations of prior work)
- Method section (why existing approaches fail here)

### Step 2: Collect Insights and Techniques

For each challenge, collect the insights or techniques that address it. Multiple techniques may address the same challenge, and one technique may address multiple challenges.

### Step 3: Map Relationships

Create a many-to-many mapping:

```
Challenge A ──┬── Technique 1
              └── Technique 3

Challenge B ──┬── Technique 1
              ├── Technique 2
              └── Technique 4

Challenge C ──── Technique 3
```

This mapping is your "weapon library" — when you face a new challenge, you can search this tree for relevant techniques.

## Using Both Trees for Ideation

### Finding Gaps in the Novelty Tree

- **Missing milestone tasks**: Are there important problems the field hasn't formulated yet?
- **Underexplored tasks**: Which tasks have few Type 2 contributions (limited paradigm diversity)?
- **Transfer opportunities**: Can a Type 2 approach from one task be adapted to another task?

### Finding Gaps in the Challenge-Insight Tree

- **Unsolved challenges**: Which technical challenges have no good solutions?
- **Under-applied techniques**: Which techniques solved a challenge in one domain but haven't been tried in others?
- **Emerging challenges**: Do new tasks or data settings reveal challenges not yet in the tree?

### Combining Both Trees

The most productive ideation happens at the intersection:
1. The novelty tree reveals WHERE the field has unexplored territory
2. The challenge-insight tree reveals WHAT technical problems lack solutions
3. Together, they point to high-impact, high-novelty research directions

## Maintaining the Trees

- Update after reading every paper (even briefly)
- Revisit classifications periodically — your understanding evolves
- Share and discuss with colleagues to catch blind spots
- Use the paper summary template (see [../assets/paper-summary-template.md](../assets/paper-summary-template.md)) to ensure every paper is classified
