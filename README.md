# ByzantineLLM: Blind Consensus Framework

ByzantineLLM is a research framework for studying **Byzantine Fault Tolerance (BFT)** and emergent truth in Large Language Model clusters. It implements a strict N x N ranking protocol where the system has **zero prior knowledge** of adversarial agents.

---

## 🏗️ The Blind Consensus Workflow

The system operates under a "Zero-Trust" policy through a deterministic 6-step workflow:

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant N1 as Node 1
    participant N2 as Node 2
    participant Ni as Node N
    participant A as Anonymity Layer
    participant J as Judge

    Note over N1,Ni: (Step 1) N Participants Initialized
    
    U->>N1: (Step 2) Send Question
    U->>N2: (Step 2) Send Question
    U->>Ni: (Step 2) Send Question
    
    Note over N1,Ni: [INDEPENDENT GENERATION]<br/>Nodes cannot see each other's work
    
    N1->>A: Raw Proposal 1
    N2->>A: Raw Proposal 2
    Ni->>A: Raw Proposal N
    
    Note over A: (Step 3) Anonymize & Broadcast
    A->>N1: All N Anonymous Proposals
    A->>N2: All N Anonymous Proposals
    A->>Ni: All N Anonymous Proposals
    
    Note over N1,Ni: Evaluate & Rank based on common criteria
    
    N1->>J: (Step 4) Send N ranks
    N2->>J: (Step 4) Send N ranks
    Ni->>J: (Step 4) Send N ranks
    
    Note over J: (Step 5) Evaluate NxN Matrix
    Note over J: (Step 6) Final Verdict & Response
```

1.  **Independent Initialization:** N participants (using different LLMs) are initialized. The system does not label or instruct any node to be "Byzantine."
2.  **Parallel Proposal:** All participants receive the **same question** and generate an independent answer.
3.  **Blind Cross-Auditing:** All responses are anonymized (e.g., "Participant A"). Every participant evaluates all N anonymous responses based on objective criteria.
4.  **Independent Ranking:** Participants submit a ranked list of these anonymous IDs to the Judge.
5.  **Matrix Discovery:** The **Judge** evaluates the $N \times N$ ranking table. It must **discover** Byzantine behavior (hallucinations, bias, or sabotage) purely through statistical outliers and logical inconsistencies in the matrix.
6.  **Verified Synthesis:** The Judge de-anonymizes the winner and generates a final authoritative response.

---

## 🛡️ The Zero-Trust Analysis Loop

The framework moves from decentralized generation to centralized verification through rigorous cross-auditing and statistical discovery.

```mermaid
graph TD
    Start((Broadcast Question)) --> N1P[Phase 2: Node 1 Proposal]
    Start --> N2P[Phase 2: Node 2 Proposal]
    Start --> NiP[Phase 2: Node N Proposal]

    subgraph "Independent Generation"
    N1P
    N2P
    NiP
    end

    N1P --> Anon{Anonymity Layer}
    N2P --> Anon
    NiP --> Anon

    subgraph "Phase 3 & 4: Blind Ranking Matrix"
    Anon --> |All N| N1R[Node 1 Ranks All]
    Anon --> |All N| N2R[Node 2 Ranks All]
    Anon --> |All N| NiR[Node N Ranks All]
    N1R --> Matrix[NxN Ranking Table]
    N2R --> Matrix
    NiR --> Matrix
    end

    subgraph "Phase 5 & 6: Judge's Finality"
    Matrix --> Analysis[Byzantine Discovery]
    Analysis --> Synthesis[Authoritative Response]
    end

    Synthesis --> Output((Verified Response))

    style Anon fill:#bbf,stroke:#333,stroke-dasharray: 5 5
    style N1P fill:#fff,stroke:#333
    style N2P fill:#fff,stroke:#333
    style NiP fill:#fff,stroke:#333
```

---

## 🚀 Key Features

*   **Zero-Knowledge Protocol:** No node is pre-assigned a "Byzantine" role. Malicious behavior is discovered, not declared.
*   **Total Anonymity:** Participants cannot see model names or node identities during evaluation, ensuring purely content-based auditing.
*   **Consistency Protocol:** Every node receives the exact same system and user prompts to ensure absolute objectivity and a level playing field.
*   **Self-Healing Consensus:** The protocol is designed to isolate low-quality or adversarial contributions through peer-to-peer disagreement analysis.
*   **Heterogeneous Evaluation:** Mix high-capability and low-capability models to test how the "Byzantine" effect naturally emerges from model limitations.

---

## 🛠️ Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run a Consensus Session
```bash
python consensus_cli.py \
  --topic "Explain the core mechanism of Byzantine Fault Tolerance." \
  --n 4
```

---

## 💻 Python API

```python
from src.byzantine import ConsensusConfig, ConsensusSession

config = ConsensusConfig(
    topic="What is the safest way to store private keys?",
    node_models=["gpt-4o-mini", "claude-3-haiku", "gpt-4o-mini"],
    judge_model="gpt-4o"
)

session = ConsensusSession.from_config(config)
result = session.run()

print(f"Consensus Winner: {result.winner}")
print(f"Final Response: {result.final_response}")
```

---

## 📜 License
Distributed under the **MIT License**.
