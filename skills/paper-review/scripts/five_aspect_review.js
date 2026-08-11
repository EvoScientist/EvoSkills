const ASPECTS = [
  ["contribution", "Contribution sufficiency: are the claimed contributions real, novel, and sufficient for the venue? Attack novelty explicitly."],
  ["clarity", "Writing clarity: reverse-outline the draft - does each paragraph earn its place? Flag structure breaks and unsupported claims."],
  ["results", "Results quality: do the experiments support every claim? Score the trust of each headline number."],
  ["testing", "Testing completeness: missing baselines, ablations, seeds, statistical care."],
  ["method", "Method design: is the approach sound, are assumptions stated, are limitations promoted honestly?"],
];

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
      "Review ONLY through this aspect. Be concrete: quote or point to the " +
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
