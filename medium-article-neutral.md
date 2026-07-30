# ByzantineLLM: A Zero-Trust Consensus Framework for LLMs

## The Problem

Large language models (LLMs) are often used as single sources of truth. You ask a question, get an answer, and proceed. But models can hallucinate, show bias, or produce inconsistent results. Running the same prompt multiple times (self-consistency) or using multiple models (majority voting) helps, but both assume at least one model is reliable. If all models share a blind spot, the consensus is wrong.

## The Approach: Byzantine Fault Tolerance for LLMs

Byzantine Fault Tolerance (BFT) is a concept from distributed systems. It allows a network to reach agreement even when some nodes behave arbitrarily — they may lie, fail, or collude. Traditional BFT requires 3f+1 nodes to tolerate f faulty ones.

ByzantineLLM adapts this idea for LLMs. Instead of deterministic nodes, it uses different LLM models as participants. The key difference: **no model is trusted by default**. The system discovers reliability through cross-examination.

## The 6-Step Protocol

### Step 1: Initialize
Create N nodes (each a different LLM) and 1 judge model. No node is labeled "honest" or "Byzantine."

### Step 2: Parallel Proposal
All nodes receive the exact same prompt. Each generates an answer independently. Nodes cannot see each other's outputs.

### Step 3: Anonymize
Replace model names with generic labels ("Participant A," "Participant B"). This prevents bias based on model reputation.

### Step 4: Blind Cross-Auditing
Each node evaluates **all N anonymous answers** (including its own) and ranks them from best to worst with brief justifications. This produces an N×N ranking matrix — N evaluators each ranking N proposals.

### Step 5: Judge Analysis
The judge model receives:
- All N anonymous proposals
- The complete N×N ranking matrix with justifications

The judge analyzes patterns: Which answers are consistently ranked high? Which evaluators disagree with the majority? Which justifications are coherent?

### Step 6: Verified Synthesis
The judge identifies the consensus winner, assigns scores (0–10) to each participant, and writes a final answer based on the winning proposal. The winner's identity is then revealed.

## Why Cross-Auditing Works

| Attack Type | Majority Voting | ByzantineLLM |
|-------------|----------------|--------------|
| One hallucinating model | May win if others agree | Ranked low by peers |
| Two colluding models | Can dominate | Judge detects mutual high-ranking |
| Many weak models (Sybil) | Numerical advantage | Quality-based ranking, not count |
| Biased judge | Single point of failure | Judge constrained by N×N matrix |

The N×N matrix is the core mechanism. Instead of asking "which answer is best?" (subjective), each model answers "how do these answers compare?" (relative). Relative ranking is more reliable than absolute scoring.

## Architecture

```python
from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder

models = ByzantineModelsConfig(
    node_models=["gpt-4o-mini", "claude-3-haiku-20240307", "gemini-1.5-flash"],
    judge_model="gpt-4o"
)

builder = PromptBuilder(
    system_prompt="You are a senior engineer. Be precise.",
    user_template="Explain technically: {topic}"
)

engine = ByzantineLLM(models=models, prompt_builder=builder, temperature=0.5)
result = engine.run("What is Byzantine Fault Tolerance?")

print(f"Winner: {result.winner}")
print(f"Scores: {result.final_scores}")
print(f"Answer: {result.final_response}")
```

**Design patterns used:**
- Strategy pattern: `PromptBuilder` separates prompt logic from consensus logic
- Template method: `ByzantineLLM.run()` fixes the 6-step workflow
- Pydantic models: Structured data exchange between heterogeneous LLMs

## Complexity

| Phase | API Calls | Evaluations | Token Growth |
|-------|-----------|-------------|--------------|
| Generation | N | 0 | Linear |
| Audit | N | N² Quadratic |
| Judgment | 1 | 2N Linear |
| **Total** | **2N+1** | **N²+2N** | **Quadratic** |

**Trade-off:** Quadratic token growth in the audit phase (each node reads all N proposals). Practical limit: N ≤ 5 with current context windows.

## Example Run

Configuration (4 nodes, 1 judge):
```json
{
  "topic": "Effective urban climate mitigation strategies for the next decade",
  "models": {
    "node_models": ["gpt-4o-mini", "claude-3-haiku-20240307", "gpt-4o-mini", "gemini-1.5-flash"],
    "judge_model": "gpt-4o"
  }
}
```

Output includes:
- Ranked winner (e.g., "Node-3")
- Scores for all participants (e.g., {"Node-1": 7.2, "Node-2": 8.5, "Node-3": 9.1, "Node-4": 6.8})
- Byzantine analysis (e.g., "Node-1 ranked consensus winner 4th; justification referenced outdated data")
- Final synthesized answer

## When to Use

**Suitable for:**
- High-stakes decisions needing audit trails
- Research on LLM reliability
- Heterogeneous model fleets
- Cases where no single model is fully trusted

**Not suitable for:**
- Latency-sensitive applications (2N+1 sequential LLM calls)
- Simple factual queries
- Cost-sensitive workloads (N+1 model calls per query)
- N > 5 (context window pressure)

## Limitations

1. **No benchmarks yet** — hallucination reduction claims are theoretical
2. **Judge dependency** — final quality caps at judge model capability
3. **Parsing failures** — LLMs occasionally output invalid JSON; retry logic not built in
4. **Quadratic context** — audit phase sends all proposals to each node
5. **Cost** — 3 nodes + 1 judge = 7 LLM calls per query

## Getting Started

```bash
git clone https://github.com/your-repo/ByzantineLLM
cd ByzantineLLM
pip install -r requirements.txt
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GOOGLE_API_KEY=...

python examples/01_basic_consensus.py
# Or CLI:
python consensus_cli.py --topic "Your question" --n 3
```

## Summary

ByzantineLLM applies Byzantine Fault Tolerance principles to LLM ensembles. It replaces trust with verification: models audit each other anonymously, a judge analyzes the resulting ranking matrix, and the consensus winner produces the final answer. The protocol achieves quadratic evaluation depth (N×N) with linear API cost (2N+1), but introduces latency, cost, and context-window constraints. It is a research framework — not a drop-in replacement for single-model inference.