# Tree Search Protocol

Detailed rules for expanding the idea tree during idea generation. The tree structure ensures diverse idea generation by systematically varying one axis per level.

## The Three Axes

Each level of the tree varies a different axis. This constraint prevents "similar but different" ideas — each branch explores a fundamentally different dimension of variation.

### Technique Axis (Level 1)

**What varies**: The core technical approach to the problem.

**Good variation**: Each technique represents a fundamentally different paradigm.
- Example for "improving drug delivery across the blood-brain barrier": Nanoparticle carriers (physical transport), receptor-mediated transcytosis (biological hijacking), focused ultrasound (temporary barrier disruption)
- These are genuinely different approaches with different assumptions and trade-offs

**Bad variation**: Variations within the same paradigm.
- "PLGA nanoparticles", "Lipid nanoparticles", "Gold nanoparticles" — all nanoparticle carriers
- Save these for Level 3 (formulation variants within a technique)

**How to generate**: Ask "What are the 3 fundamentally different ways to approach this problem?" Verify each technique is genuinely distinct — they should rely on different principles, not just different parameters.

### Domain Axis (Level 2)

**What varies**: The application context or problem domain where the technique is applied.

**Good variation**: Each domain introduces meaningfully different constraints.
- Example for "nanoparticle drug delivery to the brain": Alzheimer's disease (chronic, low-dose), Glioblastoma (acute, high-dose, tumor microenvironment), Pediatric epilepsy (developing brain, safety-critical)
- Each domain changes which aspects of the delivery system matter most

**Bad variation**: Domains that are functionally identical for this technique.
- "Parkinson's disease" vs "Lewy body dementia" — nearly identical delivery challenges
- Domains should create different technical demands

**How to generate**: Ask "In what contexts would this technique face fundamentally different challenges?" List 2-3 domains per Level 1 node.

### Formulation Axis (Level 3)

**What varies**: The specific problem formulation — inputs, outputs, constraints, evaluation criteria.

**Good variation**: Each formulation defines a different concrete problem.
- Example for "nanoparticle delivery for glioblastoma": Maximize tumor accumulation (biodistribution-optimized), Minimize systemic toxicity (safety-optimized), Enable real-time imaging + therapy (theranostic)
- Each formulation leads to different optimization targets and evaluation metrics

**Bad variation**: Formulations that are equivalent in practice.
- "Reduce side effects" vs "Improve safety profile" — same optimization

**How to generate**: Ask "What are the different ways to precisely state what success looks like?" Generate 1-2 formulations per Level 2 node.

## Expansion Rules

### Per-Node Cycle: Propose → Review → Refine

**Step 1 — Propose**:
Write a 2-3 sentence description of the idea. Include:
- What the technique does (in this domain, under this formulation)
- Why it might work (the key insight or hypothesis)
- How it differs from the parent node

**Step 2 — Review** (evaluate critically):
Evaluate three questions:
1. Is this genuinely different from sibling nodes? (If not, merge or replace)
2. Is it at least plausible? (If clearly impossible, prune)
3. Is the description specific enough to act on? (If vague, refine)

**Step 3 — Refine**:
Based on the review, sharpen the description. Remove vague language ("might be useful", "could potentially"). Make the novelty claim specific ("uses X to solve Y, which previous approaches Z cannot handle because...").

### Target: Up to N_I=21 Leaf Candidates

A 3-level tree with 3 technique × 3 domain × ~2-3 formulation branches naturally produces 18-27 leaves. Aim for 15-21 leaves:
- **<10 candidates**: Not enough diversity. Tournament results are unreliable.
- **15-21 candidates**: Good diversity with manageable tournament size.
- **>21 candidates**: Prune more aggressively to stay within 21.

## Pruning Criteria

Prune after each level expansion. A branch should be pruned ONLY if:

### Clearly Infeasible
- Requires resources fundamentally unavailable (e.g., proprietary data, equipment you can't access)
- Contradicts well-established theoretical or physical constraints
- Violates known impossibility results

### Duplicate
- Effectively identical to another branch (same technique + domain + formulation despite different wording)
- When merging duplicates, keep the more precisely stated version

### Known Failure (from evo-memory)
- Appears in M_I unsuccessful directions as a **fundamental failure** (not implementation failure)
- Implementation failures may be worth retrying — do NOT prune these

### Do NOT Prune
- Ideas that seem unlikely but are not provably impossible
- Ideas outside your current expertise (unfamiliarity ≠ infeasibility)
- Ideas that challenge conventional wisdom (these are often the most interesting)
- Ideas rated low on any single dimension (the tournament evaluates holistically)

## Diversity Metrics

After tree expansion, check diversity before proceeding to the tournament:

### Inter-Branch Diversity
Are Level 1 branches genuinely different techniques?
- Test: Could you explain each to a colleague in one sentence, and would they recognize them as different approaches?

### Intra-Branch Diversity
Within each Level 1 branch, are Level 2 nodes exploring different domains?
- Test: Do the domains create different technical challenges for the technique?

### Leaf Diversity
Across all leaf nodes, is there variety in formulations?
- Test: Would the evaluation metrics be different for different leaves?

## Example Tree: Improving Drug Delivery Across the Blood-Brain Barrier

```
Level 0 (Seed): Improving drug delivery across the blood-brain barrier

Level 1 (Technique):
├── T1: Engineered Nanoparticle Carriers
├── T2: Receptor-Mediated Transcytosis
└── T3: Focused Ultrasound-Assisted Delivery

Level 2 (Domain):
├── T1-D1: Nanoparticles for Alzheimer's (chronic, low-dose)
├── T1-D2: Nanoparticles for Glioblastoma (acute, high-dose)
├── T1-D3: Nanoparticles for Pediatric Epilepsy (developing brain)
├── T2-D1: Transcytosis for neurodegenerative proteins
├── T2-D2: Transcytosis for gene therapy vectors
├── T2-D3: Transcytosis for antibody therapeutics
├── T3-D1: Ultrasound for focal drug release in tumors
├── T3-D2: Ultrasound for widespread CNS gene therapy
└── T3-D3: Ultrasound for acute stroke intervention

Level 3 (Formulation):
├── T1-D1-F1: Sustained-release nanoparticles minimizing dosing frequency
├── T1-D1-F2: Stimuli-responsive nanoparticles triggered by amyloid-β
├── T1-D2-F1: Tumor-targeting nanoparticles maximizing accumulation ratio
├── T1-D2-F2: Theranostic nanoparticles enabling MRI-guided delivery
├── T1-D3-F1: Size-optimized nanoparticles for immature BBB
├── T2-D1-F1: Bispecific antibody exploiting transferrin receptor
├── T2-D2-F1: AAV conjugated with BBB-penetrating peptide
├── T2-D2-F2: Exosome-mediated gene delivery across BBB
├── T2-D3-F1: Antibody shuttle with Fc-engineered half-life extension
├── T3-D1-F1: MRI-guided focused ultrasound with microbubbles
├── T3-D1-F2: Low-intensity pulsed ultrasound for repeated sessions
├── T3-D2-F1: Whole-brain opening protocol with safety monitoring
├── T3-D3-F1: Emergency ultrasound protocol for thrombolytic delivery
├── T3-D3-F2: Ultrasound + nanoparticle combined delivery for stroke
```

14 leaf nodes — within the target range (≤N_I=21). Each leaf represents a distinct, well-defined research problem.
