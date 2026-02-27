# 🧬 EvoSkills

**The official skill repository for [EvoScientist](https://github.com/EvoScientist/EvoScientist). Each skill is an installable knowledge pack that extends EvoScientist with domain-specific expertise.**

## 📦 Installation

### In-session commands

Install all skills at once:

```bash
/install-skill EvoScientist/EvoSkills@skills
```

Or install a single skill:

```bash
/install-skill EvoScientist/EvoSkills@skills/paper-planning
```

### Ask EvoScientist directly

Simply ask the agent in conversation:

```text
"Install all skills from EvoScientist/EvoSkills@skills."
```

## ✨ Available Skills

| Skill | Description |
| ----- | ----------- |
| [`research-ideation`](#-research-ideation--literature-tree--problem-finding) | 💡 Research ideation, literature tree & problem finding |
| [`paper-planning`](#-paper-planning--research-paper-planning--outline-generation) | 📐 Research paper planning & outline generation |
| [`paper-writing`](#-paper-writing--section-by-section-paper-drafting) | ✍️ End-to-end paper writing assistance |
| [`experiment-craft`](#-experiment-craft--experiment-debugging--iteration) | 🔧 Experiment debugging, logging & iteration |
| [`paper-review`](#-paper-review--self-review--quality-assurance) | 🔍 Automated paper review & feedback |
| [`paper-rebuttal`](#-paper-rebuttal--rebuttal-writing-after-peer-review) | 💬 Rebuttal writing after peer review |
| [`academic-slides`](#-academic-slides--presentation--research-talk-creation) | 🎤 Academic presentation & research talk creation |

> **Paper Suite**: Each skill is self-contained — use them individually or combine freely to fit your workflow.

### 💡 `research-ideation` — Literature Tree & Problem Finding

The starting point of the research pipeline. Guides ideation from literature analysis to solution design:

- **Literature Tree** — Build a novelty tree and challenge-insight tree to map the research landscape
- **Problem Selection** — 4-level well-established solution check to identify open problems worth pursuing
- **Solution Design** — Cross-domain transfer and problem decomposition strategies
- **Paper Reading** — 3-level structured Q&A methodology for deep comprehension
- **Counterintuitive Rules** — Problem selection matters more than solution design; pursue new failure cases rather than incremental improvements

### 📐 `paper-planning` — Research Paper Planning & Outline Generation

Guides pre-writing planning before a single word is drafted. Covers four key activities:

- **Story Design** — Reverse-engineer the narrative: task → challenge → insight → contribution → advantage
- **Experiment Planning** — Plan comparisons, ablations, and demo scenarios with structured checklists
- **Figure Design** — Pipeline figures that highlight novelty; teaser figures that hook reviewers
- **Timeline Management** — 4-week countdown schedule from outline to submission

Includes counterintuitive tactics: write your rejection letter first, narrow claims before broadening, and plan fallback narratives.

### ✍️ `paper-writing` — Section-by-Section Paper Drafting

A proven 11-step workflow for writing academic papers with LaTeX templates:

- **Structured Process** — From pipeline sketch → story design → Method → Experiments → Related Work → Abstract → Title
- **Section Templates** — Three Abstract templates, four Introduction openers, Method module structure, Experiments organization
- **LaTeX Assets** — Annotated paper skeleton (`paper-skeleton.tex`) and booktabs table macros (`table-style.tex`)
- **Writing Principles** — One message per paragraph, topic sentence first, terminology consistency, reverse-outlining
- **Counterintuitive Tactics** — Underclaim in prose / overdeliver in evidence; lead with mechanism, not just metrics

### 🔧 `experiment-craft` — Experiment Debugging & Iteration

A systematic approach to experiment debugging, logging, and iterative improvement:

- **5-Step Diagnostic Flow** — Collect failures → find a working version → bridge the gap → hypothesize → fix
- **Counterintuitive Rules** — Change one variable at a time; effective experiments beat more experiments
- **Experiment Logging** — 5-section structured log template for reproducible records
- **Handoff to Paper-Writing** — Feed validated results and logs into `paper-writing` for drafting

### 🔍 `paper-review` — Self-Review & Quality Assurance

Systematic self-review before submission using adversarial and counterintuitive review strategies:

- **5-Aspect Checklist** — Contribution sufficiency, writing clarity, results quality, testing completeness, method design
- **Reverse-Outlining** — Extract the outline from finished paragraphs to verify logical flow
- **Figure & Table Quality Checks** — Captions, resolution, booktabs, color-blind friendliness
- **Rejection Simulation** — Force a reject summary first; attack your own novelty claim
- **Handoff to Rebuttal** — After review, feed identified weaknesses into `paper-rebuttal` for response preparation

### 💬 `paper-rebuttal` — Rebuttal Writing After Peer Review

Dedicated rebuttal skill for responding to reviewer feedback after peer review:

- **Score Diagnosis** — Color-code every reviewer comment: red (critical), orange (important), gray (minor), green (positive)
- **Champion Strategy** — Arm your most positive reviewer with evidence for the Area Chair discussion
- **Tactical Writing** — 18 rules for structure, content, and tone in rebuttal responses
- **Counterintuitive Principles** — Submit even with extreme scores; concede small points to win the big argument
- **Common Concerns** — Response strategies for 12 frequently raised reviewer complaints

### 🎤 `academic-slides` — Presentation & Research Talk Creation

A structured approach to creating academic presentations and preparing research talks:

- **Narrative Arc** — Define scope, audience, and key takeaway before touching slides
- **Slide Design** — 10 design rules, visual hierarchy, one idea per slide, claim-style titles
- **Practical Creation** — `.pptx` file generation with color palettes, layout code, charts, and figures
- **Delivery & Q&A** — Rehearsal protocol, timing, and backup slide preparation
- **Counterintuitive Rules** — Slides are not your paper; enthusiasm beats polish; related work builds motivation, not citation counts

## 🎯 ᯓ➤ Roadmap

Coming soon:
- [ ] 🧠 **Self-Evolution Suite** — Skills that learn, adapt & improve themselves
- [ ] 🏅 **Math Olympiad** — Advanced mathematical reasoning & problem solving
- [ ] 🎨 **Visual Generation** — Diagrams, figures & graphic content creation
- [ ] 📚 **Literature Survey** — Systematic literature search, filtering, and survey generation
- [ ] 🔬 **Paper Reproduction** — Read a paper, reproduce its core results, and verify claims
- [ ] 💡 **Grant & Proposal Writing** — Research proposal drafting with funding agency conventions
- [ ] 🤖 **Peer Debate** — Multi-agent adversarial discussion to stress-test research ideas
- [ ] 📈 **Trend Radar** — Analyze publication trends, identify emerging topics & research gaps
- [ ] 🗣️ **Paper QA** — Interactive question-answering over paper collections, extracting key findings & cross-referencing claims

Stay tuned — more skills are on the way!

## 🌍 Project Roles

<table>
  <tbody>
    <tr>
      <td align="center">
        <a href="https://x.com/EvoScientist">
          <img src="https://pbs.twimg.com/profile_images/2020492875340136448/CbdhV-u__400x400.jpg"
               width="100" height="100"
               style="object-fit: cover; border-radius: 20%;" alt="Xi Zhang"/>
          <br />
          <sub><b>EvoScientist</b><sup>‡</sup></sub>
        </a>
      </td>
      <td align="center">
        <a href="https://x-izhang.github.io/">
          <img src="https://x-izhang.github.io/author/xi-zhang/avatar_hu13660783057866068725.jpg"
               width="100" height="100"
               style="object-fit: cover; border-radius: 20%;" alt="Xi Zhang"/>
          <br />
          <sub><b>Xi Zhang</b><sup>†</sup></sub>
        </a>
      </td>
      <td align="center">
        <a href="https://youganglyu.github.io/">
          <img src="https://youganglyu.github.io/images/profile.png"
               width="100" height="100"
               style="object-fit: cover; border-radius: 20%;" alt="Yougang Lyu"/>
          <br />
          <sub><b>Yougang Lyu</b><sup>§</sup></sub>
        </a>
      </td>
    </tr>
  </tbody>
</table>

> <sup>‡</sup>Core Developer <sup>†</sup>Project Lead & Engineering Lead <sup>§</sup>Project Correspondent

> *Xiaoyi DeepResearch Team* and the wider open-source community contribute to this project.

For any enquiries or collaboration opportunities, please contact: [**EvoScientist.ai@gmail.com**](mailto:evoscientist.ai@gmail.com)

<p align="right"><a href="#top">🔝Back to top</a></p>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

<p align="right"><a href="#top">🔝Back to top</a></p>

---

<p align="center">
  Initiated and led by <a href="https://github.com/x-izhang">Xi Zhang</a>, built with the open-source community.
</p>