# Experiments Guide

## Three Key Questions

The Experiments section must answer three questions:

1. **How to prove our method is better?** → Comparison experiments
2. **How to prove our modules are effective?** → Ablation studies
3. **How to showcase the method's upper limit?** → Demos on challenging data

---

## Experimental Analysis Writing Style

### Use Structured Observations, Not Continuous Paragraphs

When presenting experimental results and analysis (especially for Research Questions), prefer **structured observation lists** over continuous paragraphs:

**Anti-pattern** (continuous paragraphs):
```latex
\subsection{Main Results (RQ1)}
Our method achieves strong performance on the benchmark. 
The results show improvements across all metrics. 
We observe that the model generalizes well...
```

**Best practice** (structured observations):
```latex
\subsection{Main Results (RQ1)}

We evaluate our method on the benchmark dataset. 
Based on the results in Table~\ref{tab:main}, we have four main observations:
\begin{itemize}[leftmargin=*,nosep]
\item \textbf{Method's innovation X achieves result Y.} [Detailed explanation with specific numbers, followed by deeper analysis of why this happens...]

\item \textbf{Method's feature Z enables capability W.} [Empirical observations, then mechanistic explanation...]

\item \textbf{Method's design choice A produces expected trade-off B.} [Evidence from results, then interpretation...]
\end{itemize}
```

### Observation Structure Template

Each observation should follow this three-part structure:

1. **Bold title (innovation → result)**: State the method's innovation point and the resulting phenomenon
2. **Empirical evidence**: Present specific numbers, comparisons, or patterns from tables/figures
3. **Mechanistic explanation**: Explain why this result occurs, connecting back to method design

### Use Method Name as Subject

- All observations should use your **method name** as the subject (e.g., "EvoIdeator achieves...", "EvoIdeator's mechanism enables...")
- Avoid generic subjects like "our model", "the system", or "we observe that"
- Exception: When describing universal findings that apply to all models, use neutral subjects ("all models show...")

### Subsection Titles Should Be Concise

Research question subsections should use **3-5 words + RQ marker**:
- ✅ `\subsection{Main Results (RQ1)}`
- ✅ `\subsection{Additive Effects Analysis (RQ2)}`
- ✅ `\subsection{Cross-Judge Generalization Analysis (RQ3)}`
- ❌ `\subsection{Detailed Analysis of Language Feedback Quality Across Different Large Language Model Providers (RQ3)}`

### Research Question Formulation

State research questions with precision and method-centricity:

**Anti-pattern** (vague, method-agnostic):
- "Does the setup work better than baselines?"
- "Do components combine additively?"
- "How does feedback quality depend on the judge?"

**Best practice** (precise, method-centric):
- "Does [MethodName] outperform [specific baselines] on [specific evaluation dimension]?"
- "Do [MethodName]'s [component A] and [component B] combine additively, and what are their individual contributions?"
- "Does [MethodName]'s [specific mechanism] generalize to [specific test condition]?"

---

## Comparison Experiments

### Version 1 — Existing Baselines

When established baselines exist for the task:

- Compare with closely related, **recent** baseline methods
- Include the current SOTA methods
- Use standard evaluation metrics for the task
- Use the same evaluation protocol (datasets, splits, metrics)

### Version 2 — Novel Task (No Direct Baselines)

When no existing methods directly address the same task:

- Construct method variants as baselines:
  - Adapt methods from related tasks
  - Create ablated versions of your method
  - Combine existing techniques in straightforward ways
- Clearly explain how each baseline is constructed
- Justify why these are fair comparisons

---

## Ablation Studies

Ablation studies must include **two parts**:

### Part 1: Core Contribution Ablation (One Big Table)

- One comprehensive table + visualization comparisons
- Shows the impact of **core contributions** and **important components**
- Each row removes or replaces one key component
- Demonstrates that each contribution is necessary

### Part 2: Module Design Choices (Several Small Tables)

Each small table examines one pipeline module's design choices:
- **Hyperparameter sensitivity**: How does performance change with different hyperparameter values?
- **Input data quality**: How does performance degrade with lower-quality inputs?
- **Design choice ablation**: What happens when a specific design choice is removed or replaced?

> Each small table examines the impact of one pipeline module's design choices on performance.

---

## Demos and Applications

> Applications and demos are critical for the paper's impact.

- Demonstrate the method on **more challenging data** beyond standard benchmarks
- Show applications that highlight the method's generalizability
- Include qualitative results that are visually compelling
- Demos help reviewers and readers appreciate the practical value

---

## Table and Figure Guidelines

### Table Formatting

Follow the iterative improvement process:

1. **Caption above the table** — Always place the caption above, not below
2. **No vertical lines** — Remove all vertical lines; do not connect vertical and horizontal lines
3. **Use booktabs** — Replace `\hline` with `\toprule`, `\midrule`, `\bottomrule`
4. **Minimize horizontal lines** — Only use rules to separate header and major sections
5. **Add color highlighting** — Use color (e.g., red for best, blue for second-best) for key numbers

```latex
\begin{table}[t]
\centering
\caption{Quantitative comparison on [dataset]. \textbf{Bold}: best, \underline{underline}: second best.}
\label{tab:comparison}
\begin{tabular}{lccc}
\toprule
Method & Metric 1 $\uparrow$ & Metric 2 $\uparrow$ & Metric 3 $\downarrow$ \\
\midrule
Baseline A & 0.85 & 0.72 & 3.21 \\
Baseline B & 0.87 & 0.75 & 2.98 \\
\midrule
Ours & \textbf{0.92} & \textbf{0.81} & \textbf{2.45} \\
\bottomrule
\end{tabular}
\end{table}
```

### Caption Guidelines

- Table/figure captions must **clearly describe the experimental setting and notation**
- Caption content should **NOT extensively discuss results** (avoids repetition with main text)
  > Captions should not extensively discuss results — this avoids repetition with the main text
- Use arrows (↑/↓) to indicate whether higher or lower is better
- Define abbreviations in the caption if not obvious

### Layout Tips

- Single-column figures/tables look better in the **right column**
  > Single-column figures/tables look better in the right column — reading habit starts from the upper-left
- This follows reading habit: eyes start from the upper-left, so text flows naturally on the left while figures sit on the right

---

## Experiment Section Structure

A typical Experiments section:

```latex
\section{Experiments}

\subsection{Experimental Setup}
% Datasets, evaluation metrics, implementation details, baselines

\subsection{Comparison with State-of-the-Art Methods}
% Quantitative comparison table + qualitative comparison figure
% Analysis of why our method outperforms

\subsection{Ablation Study}
% Core contribution ablation (big table)
% Module design choice ablations (small tables)

\subsection{Applications / Demos}  % Optional but recommended
% Results on challenging data, real-world applications
```

---

## Common Pitfalls

Reviewers frequently flag these issues:

- **Missing ablation studies**: Every core contribution must be ablated
- **Missing important baselines**: Omitting recent, well-known methods in the field
- **Missing evaluation metrics**: Not using standard metrics for the task
- **Data too simple**: Using only easy benchmarks that don't stress-test the method
- **Unfair comparison**: Different training data, different resolution, different evaluation protocol
- **No qualitative results**: Tables alone are insufficient — visual comparisons matter
