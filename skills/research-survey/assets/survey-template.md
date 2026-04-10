# Survey Template Guide

This is NOT a fixed template. Different fields have different survey conventions. Use the two-phase process below.

## Phase 1: Generate a Domain-Specific Survey Template

Before writing, first generate a survey structure tailored to the user's field.

### Field-Specific Survey Conventions

| Field | Organization Logic | Methods Section Name | Evaluation Section | Special Requirements |
|-------|-------------------|---------------------|-------------------|---------------------|
| **CS / ML** | By technical mechanism/paradigm | Mainstream Methods / Methodologies | Benchmarks, Metrics, SOTA | Paradigm comparison tables, ablation-style analysis |
| **Medicine / Clinical** | By intervention type or PICO framework | Treatment Modalities / Interventions | Clinical Outcomes, Evidence Quality | PRISMA flowchart, risk of bias assessment, evidence grading (GRADE), forest plot description |
| **Chemistry / Materials** | By reaction type, material class, or synthetic approach | Synthetic Approaches / Preparation Methods | Characterization Techniques, Performance Metrics | Reaction condition tables, property comparison tables, structure-activity relationships |
| **Physics** | By theoretical framework or phenomena | Theoretical Approaches / Experimental Methods | Measurements, Validation | Mathematical derivations, symmetry arguments, error/uncertainty analysis |
| **Social Sciences** | By theoretical perspective or theme | Theoretical Frameworks / Methodological Approaches | Study Design Critique, Validity Assessment | Conceptual framework diagram, thematic analysis, reflexivity/positionality |
| **Engineering** | By design approach or application domain | Design Methods / Technical Approaches | Performance Under Standards, Compliance | Design specification tables, standard compliance (ISO/ASTM), cost-benefit analysis |
| **Biology / Life Sciences** | By biological process, model organism, or pathway | Biological Mechanisms / Experimental Strategies | Assay Methods, Statistical Approaches | Pathway diagrams, model organism comparison, translational potential |
| **Environmental / Earth Science** | By spatial/temporal scale or process type | Observational/Modeling Methods | Data Quality, Model Validation | Spatial/temporal scale tables, policy implications, field protocol comparison |

### Template Generation Steps

1. **Identify the field** from the user's research goal and collected papers
2. **Select universal sections** (see below) — present in all surveys
3. **Add field-specific sections and rename** according to the table above
4. **Choose organization logic**: How should the main body be structured? (by mechanism, by intervention type, by theoretical perspective, etc.)
5. **Determine required tables**: Every field has different comparison dimensions

### Universal Sections (present in all survey fields)

These appear in virtually every survey, though naming and emphasis differ:

1. **Title** — specific to the research goal
2. **Abstract / Summary** — self-contained overview
3. **Introduction** — why this topic matters, scope of review
4. **[Main Body: organized by field convention]** — the core synthesis
5. **Evaluation / Assessment** — how work in this area is measured
6. **Challenges and Future Directions** — open problems and opportunities
7. **Conclusion** — summary and outlook

### Field-Specific Sections to Add

| Field | Additional Sections |
|-------|--------------------|
| Medicine / Clinical | Search Strategy & Inclusion Criteria, Risk of Bias Assessment, Evidence Synthesis (meta-analysis if applicable), Clinical Implications, Limitations of Included Studies |
| Chemistry / Materials | Structure-Property Relationships, Scalability & Industrial Viability, Environmental & Safety Considerations |
| Physics | Mathematical Formalism, Computational Methods, Open Theoretical Questions |
| Social Sciences | Conceptual/Theoretical Framework, Methodological Critique, Ethical Considerations, Policy Implications |
| Engineering | Design Specifications & Constraints, Standards Compliance, Economic Analysis, Technology Readiness Levels |
| Biology | Model Systems Comparison, Translational Potential, Ethical Considerations (animal/human subjects) |
| Environmental | Policy Context, Monitoring Protocols, Uncertainty & Scale Dependencies |

## Phase 2: Fill the Domain-Specific Template

### Universal Writing Principles (all fields)

1. **Goal-centric filtering**: Every piece of information must serve the user's research goal. Discard tangentially related content.

2. **Build taxonomy, don't enumerate**: Organize work by underlying principle/mechanism/approach, not paper-by-paper or chronologically.

3. **Critical analysis over description**: For each approach, explain WHY it works, WHAT trade-off it makes, WHERE it fails.

4. **Dense citations**: Ground ALL claims with numbered citations [X]. Nearly every sentence should reference at least one source.

5. **Zero vagueness**: Use specific names — methods, datasets, metrics, reagents, organisms, instruments. No generic statements.

6. **Comparison tables**: Every major category of work should have a structured comparison table with field-appropriate columns.

### Field-Specific Writing Standards

| Field | Key Standard |
|-------|-------------|
| Medicine | Follow PRISMA reporting guidelines; assess evidence quality using GRADE or similar; distinguish RCTs from observational studies |
| Chemistry | Include reaction conditions (temperature, solvent, catalyst, yield); compare characterization results quantitatively |
| Physics | Include mathematical formulations with derivation sketches; quantify experimental uncertainties |
| Social Sciences | Discuss epistemological foundations; critique study designs (sampling, validity); address generalizability |
| Engineering | Reference applicable standards (ISO, ASTM, IEEE); include performance under specified conditions |
| Biology | Specify model organisms and their relevance; discuss statistical approaches; note sample sizes |

### Section-Level Guidance

**Abstract**: Dense continuous paragraph. Flow: domain + challenge → scope of review → key findings across categories → outlook. No bullet points.

**Introduction**: Continuous narrative. Cover: research background → why this survey is needed now → scope and boundaries → organization of the paper.

**Main Body**: The core of the survey.
- Organize by field convention (mechanism, intervention, theory, etc.)
- Each major category: technical narrative (multi-paragraph, not bullet points) + comparison table
- Cross-category analysis: what connects different approaches, what distinguishes them

**Evaluation / Assessment**: How is work in this area judged?
- Field-appropriate criteria (benchmarks for CS, clinical endpoints for medicine, characterization for materials)
- Critique of evaluation methods themselves (what do current metrics miss?)

**Challenges & Future Directions**: 3-5 specific challenges, each with:
- Problem definition
- Evidence from literature
- Strategic opportunity
- Initial attempts (if any)

**Conclusion**: Reiterate scope → summarize key findings → state which approaches are most promising → provide forward-looking recommendation.

### References Format

```
**1. Paper Title** (Year). _Authors_. *Venue*. Citations: N. [[Link]](url)
```
