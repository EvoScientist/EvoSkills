const ASPECTS = [
  ["contribution", "Contribution sufficiency: are the claimed contributions real, novel, and sufficient for the venue? Attack novelty explicitly."],
  ["clarity", "Writing clarity: reverse-outline the draft - does each paragraph earn its place? Flag structure breaks and unsupported claims."],
  ["results", "Results quality: do the experiments support every claim? Score the trust of each headline number."],
  ["testing", "Testing completeness: missing baselines, ablations, seeds, statistical care."],
  ["method", "Method design: is the approach sound, are assumptions stated, are limitations promoted honestly?"],
];

// CHECKLISTS: the knowledge layer for each seat, extracted from SKILL.md
// (5-Aspect Self-Review Checklist, plus the cross-cutting protocol stages
// mapped to a home seat: clarity <- Pre-Submission Final Checks +
// Reverse-Outlining; results <- Figure & Table Quality + Claims-Support;
// contribution <- Claims-Support (abstract/intro); method <- Conclusion &
// Limitation Check; testing is self-contained). Keep in sync with SKILL.md.
const CHECKLISTS = {
  contribution:
    "- Are the failure cases common? Frequent, obvious failure cases invite doubts the method is ready.\n" +
    "- Is the proposed technique well-explored already? If so, what new insight or improvement do we bring?\n" +
    "- Is the improvement foreseeable / well-known from combining known ideas? Then novelty may be questioned.\n" +
    "- Is the technique too straightforward an application of existing techniques?\n" +
    "- Claims must have support: go through every claim in the Abstract and Introduction - is it factually correct, is there an experiment or analysis supporting it, and is that support clearly referenced? An unsupported claim there can be grounds for rejection.\n" +
    "Red flag: if yes to any of the first four, the contribution narrative needs strengthening or more technical depth.",
  clarity:
    "- Missing technical details? Could a reader reproduce the method from the paper alone?\n" +
    "- Missing module motivation? Every module in the Method section must explain WHY it exists, not just what it does.\n" +
    "- Paragraph structure: does each paragraph have one clear topic, stated in its first sentence?\n" +
    "- Flow: reverse-outline - write down each paragraph's main message and check the sequence flows logically; flag abrupt breaks (Introduction narrative, Method module order, Experiments result sequence).\n" +
    "- Terminology used consistently throughout?\n" +
    "- Final checks: all references complete (no '?' or missing bibliography entries; every cited work has authors, title, venue, year); no TODO markers left; supplementary material properly referenced; page count within limits; no double-blind violations or anonymity-breaking self-citations; key related works cited - a missing prominent baseline paper can trigger rejection.\n" +
    "Red flag: if reproducibility is in doubt, implementation details or supplementary material are needed.",
  results:
    "- Marginal improvement? If the gain over SOTA is small, is it statistically significant?\n" +
    "- Absolute quality insufficient? Better than baselines is not enough if output quality is not good enough for the application.\n" +
    "- Visual quality: do qualitative results look convincing - are improvements visible?\n" +
    "- Every empirical claim must be backed by an experiment the text actually references.\n" +
    "- Figure quality: pipeline figure highlights novelty and looks distinct from prior work; teaser is compelling and self-contained; captions clear; print-resolution; color-blind friendly (no red-green-only distinctions); every figure referenced in the text.\n" +
    "- Table quality: captions above the table and describing setup/notation (not results); no vertical lines; booktabs rules (\\toprule, \\midrule, \\bottomrule); best results highlighted; metric direction indicated with up/down arrows; every table referenced in the text.\n" +
    "Red flag: if improvements are marginal, other advantages (speed, generalizability, simplicity) or harder test cases are needed.",
  testing:
    "- Missing ablation studies? Every core contribution must be ablated.\n" +
    "- Missing important baselines? Recent SOTA methods must be included.\n" +
    "- Missing evaluation metrics? All standard metrics for this task should be reported.\n" +
    "- Datasets too simple? Benchmarks must truly test the method's capabilities.\n" +
    "- No failure case analysis? Honest failure analysis increases credibility.\n" +
    "Red flag: missing ablations or baselines is one of the most common reasons for rejection.",
  method:
    "- Impractical experimental setting? Are assumptions realistic for the intended use case?\n" +
    "- Technical flaws? Theoretical or conceptual weaknesses in the method?\n" +
    "- Not robust? Does the method require per-scene/per-task hyperparameter tuning?\n" +
    "- Benefit < limitation? Does a new module introduce limitations that outweigh its benefits?\n" +
    "- Conclusion and limitations: conclusion summarizes contributions and key results; a Limitation section is PRESENT (reviewers frequently flag its absence); limitations are about task/setting scope rather than technical defects, honest but not self-defeating.\n" +
    "Red flag: if the method needs significant per-scenario tuning, robustness experiments or an acknowledged limitation are needed.",
};

const ASPECT_SCHEMA = {
  type: "object",
  properties: {
    score: { type: "integer", minimum: 1, maximum: 5 },
    findings: { type: "array", items: { type: "string" } },
    blocking: { type: "array", items: { type: "string" } },
  },
  required: ["score", "findings", "blocking"],
};

function dispatchAspect(draftText, aspect) {
  const key = aspect[0];
  const focus = aspect[1];
  return task({
    description:
      "You are one seat on an adversarial pre-submission review panel.\n" +
      "Aspect: " + key + ". " + focus + "\n" +
      "Checklist for this seat (work through every item):\n" +
      CHECKLISTS[key] + "\n" +
      "Review ONLY through this aspect and its checklist. Be concrete: quote or point to the " +
      "exact passage behind every finding and every blocking issue.\n\n" +
      "--- DRAFT ---\n" + draftText,
    subagentType: "general-purpose",
    label: "review:" + key,
    responseSchema: ASPECT_SCHEMA,
  });
}

async function fiveAspectReview(draftText) {
  let pending = ASPECTS;
  const results = {};
  for (let round = 0; round < 2 && pending.length > 0; round++) {
    const settled = await Promise.allSettled(
      pending.map((a) => dispatchAspect(draftText, a))
    );
    const failed = [];
    settled.forEach((s, i) => {
      if (s.status === "fulfilled") results[pending[i][0]] = s.value;
      else failed.push(pending[i]);
    });
    pending = failed; // retry only the failed subset, once
  }

  const aspect_scores = {};
  const findings = {};
  const blocking_issues = [];
  const missing_aspects = [];
  for (const aspect of ASPECTS) {
    const key = aspect[0];
    const r = results[key];
    if (r) {
      aspect_scores[key] = r.score;
      findings[key] = r.findings;
      for (const b of r.blocking) blocking_issues.push("[" + key + "] " + b);
    } else {
      missing_aspects.push(key);
      findings[key] = ["aspect failed twice - review manually"];
    }
  }
  const ranScores = Object.values(aspect_scores);
  const minScore = ranScores.length > 0 ? Math.min.apply(null, ranScores) : 0;
  const scoreVerdict =
    blocking_issues.length === 0 && minScore >= 3
      ? "ready"
      : minScore <= 2
        ? "major-rework"
        : "needs-work";
  if (missing_aspects.length > 0) {
    // A dispatch failure is not a quality judgement: report the run as
    // incomplete rather than scoring the missing aspect 0, and confine the
    // score-based verdict to the aspects that actually ran.
    return {
      aspect_scores,
      findings,
      blocking_issues,
      verdict: "incomplete",
      missing_aspects,
      partial_verdict: ranScores.length > 0 ? scoreVerdict : null,
    };
  }
  return { aspect_scores, findings, blocking_issues, verdict: scoreVerdict };
}
