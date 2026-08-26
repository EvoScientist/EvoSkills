You are an expert research analyst building a hierarchical taxonomy tree for
a collection of scientific papers. Your task is to analyze the papers below
and produce a high-level taxonomy in Markdown.

--- User Research Goal ---
{goal}

--- Papers to Analyze ---
{papers_input}
*(A numbered list. You MUST use the numbers (1), (2), ... for citation.)*

--- Your Task ---
1. Identify 2–5 core research challenges at the natural conceptual joints of
   this paper pool. Do not force symmetry.
2. For each challenge, identify 1–4 genuinely distinct solution strategies.
3. Map the relevant papers to each solution branch using the paper numbers.

--- Grouping & Coverage Rules ---
- Researcher utility comes first: carve the field at meaningful technical
  joints, even when branches are uneven.
- Give each paper at most ONE primary solution placement. Do not duplicate a
  foundational paper across later solution branches merely to imply ancestry.
- A one-paper solution is valid when the paper represents a distinct approach
  in this pool. Conversely, split a large bucket when it combines mechanisms a
  researcher would want to distinguish.
- Foundational papers, surveys, diagnostic analyses, and derivative
  applications may be omitted from solution membership when forcing them into
  a solution would misstate their role. They remain available to the appendix
  and later evidence analysis. The detail stage may reuse an omitted or
  differently placed foundational paper as lineage context; that does not
  create a second primary taxonomy placement.
- Coverage is secondary to accurate placement. Do not create catch-all buckets
  or forced symmetry to include every paper.
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
