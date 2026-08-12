# Disambiguation

Read this when the user's query looks ambiguous — a project name, codename, module name, or nickname — rather than a paper title or topic.

## Signals of an ambiguous query

- Single-word or 2-word capitalized name (e.g., "Mamba", "Engram", "Hyena")
- "the X paper" where X looks like a product or code name
- Mix of company/org name + module ("deepseek engram")
- Zero results from a direct `scholar_search` on the literal query

## Resolution steps

1. **Direct academic search first:**
   `scholar_search --query "<exact term>" --limit 5`
   If 1-3 sensible results appear → not ambiguous, return as Paper Card.

2. **Broaden to web + GitHub:**
   - Web search the term + "arxiv" or "paper"
   - `github_search.py --query "<term>" --limit 10` — repos often link the corresponding paper

3. **Extract identifiers:** From the web/GitHub results, identify
   - Actual paper title
   - arXiv ID
   - Author names
   - GitHub repo URL (if any)

4. **Re-enter the appropriate branch:**
   - If now have a specific paper → POINT
   - If now have a topic + several related papers → LIST
   - If user wants a survey of all related work → ITERATIVE

## Output: Disambiguation Report

Show the user what was resolved before proceeding to search:

```
🔍 Disambiguation: "deepseek engram"
├── Resolution: "Engram" is a memory module from DeepSeek AI
│   ├── Paper: "Conditional Memory via Scalable Lookup" (ArXiv:2601.07372)
│   └── GitHub: https://github.com/deepseek-ai/Engram
└── Next: searching forward citations + related memory modules
```

This serves two purposes: (a) lets the user confirm/correct the resolution before you spend more API calls, and (b) records the mapping so follow-up queries (e.g., "find more like it") have grounding.

## When disambiguation fails

If web + GitHub also return nothing:
- The term may be too new (last 30 days) — try `arxiv_monitor --keywords "<term>" --days 90`
- It may be jargon from a community without web presence — ask the user for source or context
- It may be a typo — try near-spellings or ask user to confirm

Don't invent a paper. If you can't resolve, say so.
