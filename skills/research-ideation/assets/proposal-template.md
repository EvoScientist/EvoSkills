# Research Proposal Template Guide

This is NOT a fixed template. Different fields require different proposal structures. Use the two-phase process below.

## Phase 1: Generate a Domain-Specific Proposal Template

Before writing the proposal, first generate a template tailored to the user's field. Consider:

### Field-Specific Sections to Include

| Field | Additional Sections Beyond Universal Ones |
|-------|------------------------------------------|
| Medicine / Clinical | Ethics & IRB approval, Clinical trial design (phases, arms, endpoints), Patient recruitment & inclusion/exclusion criteria, Informed consent, Statistical analysis plan (power analysis, sample size), Safety monitoring & adverse event reporting |
| Social Sciences | Theoretical/conceptual framework, Participant recruitment strategy, Interview/survey instrument design, Informed consent & confidentiality, Qualitative analysis methodology (coding scheme), Positionality statement |
| Chemistry / Materials | Synthetic route & reaction conditions, Characterization plan (XRD, SEM, NMR, etc.), Safety & hazard analysis, Scale-up considerations |
| Physics | Mathematical derivation / theoretical framework, Computational setup (DFT parameters, grid resolution, etc.), Error analysis & uncertainty quantification, Instrument/facility requirements |
| Engineering | Design specifications & constraints, Simulation/FEA methodology, Prototype fabrication plan, Testing standards & compliance (ISO, ASTM, etc.), Cost-benefit analysis |
| Environmental / Earth Science | Field sampling protocol, Environmental impact assessment, Temporal/spatial scale justification, Data quality assurance plan |
| Biology / Life Sciences | Organism/model system justification, IACUC/ethics for animal studies, Experimental controls design, Biological replicates & statistical power |
| CS / ML | Computational resource requirements, Baseline reproduction plan, Ablation study design, Code/data availability statement |
| Interdisciplinary | Identify which field conventions dominate, then combine relevant sections |

### Template Generation Instructions

When generating the domain-specific template, follow these steps:

1. **Identify the user's field** from their research goal and literature
2. **Select the universal sections** (see below) that apply to all fields
3. **Add field-specific sections** from the table above
4. **Adapt terminology**: Use the field's standard section names (e.g., "Study Design" not "Experimental Design" in clinical research; "Methodology" not "Method" in social sciences)
5. **Order sections** according to the field's convention (e.g., in medicine, Ethics comes before Results; in CS, it's often omitted entirely)

### Universal Sections (present in all fields)

These sections appear in virtually every research proposal, though the terminology and emphasis differ:

1. **Title**
2. **Abstract / Summary** — Self-contained overview of the entire proposal
3. **Problem Statement / Introduction / Background** — Why this problem matters
4. **Related Work / Literature Review** — What has been done, what gaps remain
5. **Proposed Approach / Method / Study Design** — What you will do and how
6. **Evaluation / Validation / Expected Results** — How you will know it works
7. **Conclusion / Significance / Impact** — Why it matters

## Phase 2: Fill the Domain-Specific Template

Once the template is generated, write the proposal following these universal writing principles:

### Writing Meta-Instructions

1. **Write for a top-tier reviewer in the field** — every claim supported, every design choice justified, every weakness proactively addressed

2. **Narrative coherence** — the proposal should read as a cohesive academic document. Use prose and paragraphs. Reserve bullet points for true lists (e.g., enumerated innovations, inclusion criteria, baselines)

3. **Avoid variable confusion** — if combining multiple novel components, clearly state which is the core contribution. Answer: "How can you be sure the observed effect is due to your claimed innovation, not a confound?"

4. **Citation mandate** — ground all technical claims by citing sources [1], [2, 3]

5. **Formalization where appropriate** — use mathematical notation (`$$...$$`) for quantitative fields; use precise protocol descriptions for experimental fields. Always follow formal notation with intuitive explanation

6. **Field-appropriate rigor** — match the field's standards:
   - Quantitative fields: mathematical derivations, statistical power analysis
   - Experimental fields: controls, replicates, blinding, randomization
   - Qualitative fields: coding schemes, triangulation, member checking
   - Design fields: specifications, tolerances, compliance standards

### Section-Level Guidance (Universal)

**Abstract**: Dense single paragraph. Flow: domain + challenge → current limitation → your method → validation plan → expected impact.

**Problem Statement**: Compelling narrative ending with your paradigm shift. Must answer: "Why now? Why this approach?"

**Related Work**: Not a list of papers. Build a narrative showing evolution of the field, then construct a gap argument that makes your work feel like the necessary next step. Include a paradigm comparison table.

**Proposed Method/Approach**: The most detailed section. For each component: purpose → mechanism → rationale (why this design overcomes a specific identified limitation). Include an illustrative example or case study.

**Evaluation**: Research questions → experimental/study design per question → expected outcomes with hypotheses → ablation/sensitivity analysis → alternative outcomes and contingency plans.

**Conclusion**: Reiterate problem → solution → expected impact → forward-looking statement.

### References Format

```
**1. Paper Title** (Year). _Authors_. *Venue*. Citations: N. [[Link]](url)
```
