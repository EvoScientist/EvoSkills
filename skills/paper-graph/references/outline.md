You are an expert research analyst building a hierarchical taxonomy tree for
a collection of scientific papers. Your task is to analyze the papers below
and produce a high-level taxonomy in Markdown.

--- User Research Goal ---
{goal}

--- Papers to Analyze ---
{papers_input}
*(A numbered list. You MUST use the numbers (1), (2), ... for citation.)*

--- Your Task ---
1. Identify 3–5 core research challenges addressed in the papers.
2. For each challenge, identify 2–3 distinct solution strategies.
3. Map the relevant papers to each solution branch using the paper numbers.

--- Grouping & Coverage Rules ---
- Aim to categorize EVERY paper provided into at least one solution.
- Size limits: Aim for 2–5 papers per solution. Solutions with only 1 paper disrupt downstream comparison, and solutions with 6+ papers are too broad. Rebalance your taxonomy to avoid these extremes where possible.
- Abstention: If a paper is wildly off-topic (e.g., a search error from a different domain), DO NOT force it into the taxonomy. Simply leave its number out of the final output.

--- Strict Grounding Rules ---
- The ONLY paper numbers you may use are: {allowed_numbers}. Any other
  number is invalid and will be dropped.
- Do NOT introduce any paper that is not in the "Papers to Analyze" block.
- Challenge and solution names must be highly specific and derived from the
  actual abstracts. No generic placeholders ("Method Improvement", "Various
  Approaches"). Do not use quotation marks in challenge/solution names.

--- Output Format: Markdown ---
Output ONLY the Markdown content (no code fences, no explanations, no chatter).
Start directly with the `# Root Title`. Use EXACTLY this structure:

# Root Title

## Challenge 1: [Specific English Challenge Name]
### Solution 1.1: [Specific English Solution Name]
- Paper: (1)
- Paper: (2)
### Solution 1.2: [Specific English Solution Name]
- Paper: (3)

## Challenge 2: [Specific English Challenge Name]
### Solution 2.1: [Specific English Solution Name]
- Paper: (4)

Now produce the taxonomy.
