# ByzantineLLM - Architecture Documentation

## Overview

ByzantineLLM is a decentralized research framework for studying **Byzantine Fault Tolerance (BFT)** and emergent truth in Large Language Model clusters. It implements a strict N x N ranking protocol where participants are fully anonymous and the system has zero prior knowledge of adversarial agents.

---

## 🏗️ The 6-Step Consensus Workflow

The system follows a deterministic communication flow between independent nodes and a central Judge.

```mermaid
sequenceDiagram
    autonumber
    participant U as User/Config
    participant N as Participants (N Nodes)
    participant A as Anonymity Layer
    participant J as Judge

    U->>N: (1) Broadcast same question/topic
    N->>N: (2) Generate independent proposals
    N->>A: Submit raw proposals
    A->>A: (3) Strip model names (Participant A, B...)
    A->>N: (4) Distribute anonymous proposals for cross-audit
    N->>N: Evaluate & Rank all N participants
    N->>J: (5) Submit NxN ranking matrix
    J->>J: Analyze matrix for Byzantine outliers
    J->>J: (6) Determine winner & synthesize content
    J->>U: Final Authoritative Response
```

---

## 🛡️ The Zero-Trust Analysis Loop

The framework is designed to move from decentralized generation to centralized verification through rigorous cross-auditing and statistical discovery of "Byzantine" behavior.

```mermaid
graph TD
    Start((Question)) --> P[Parallel Proposal Generation]
    
    subgraph "The Blind Network"
    P --> Anon{Anonymizer}
    Anon --> |Participant A| N1[Node 1 Audits All]
    Anon --> |Participant B| N2[Node 2 Audits All]
    Anon --> |Participant N| N3[Node N Audits All]
    end

    N1 --> Matrix[NxN Ranking Matrix]
    N2 --> Matrix
    N3 --> Matrix

    subgraph "The Judge's Chambers"
    Matrix --> BFT[Byzantine Behavior Discovery]
    BFT --> Stats[Statistical Consensus Extraction]
    Stats --> Final[Authoritative Finality]
    end

    Final --> Output((Verified Response))

    style BFT fill:#f96,stroke:#333,stroke-width:2px
    style Anon fill:#bbf,stroke:#333,stroke-dasharray: 5 5
```

---

## Core Components

### 1. The Nodes (N Participants)
Nodes are entirely independent and receive no special instructions or labeling.
- **Proposal Generation:** Every node answers the same prompt independently.
- **Blind Cross-Auditing:** Nodes evaluate anonymous versions of all $N$ proposals (including their own).
- **Independent Ranking:** Nodes produce a ranked list (Best to Worst) based on Accuracy, Completeness, and Logic.

### 2. The Anonymity Layer
A middleware that ensures evaluations are purely content-based.
- **Labeling:** Replaces node names/models with IDs like "Participant A", "Participant B".
- **Blind Matrix:** Ensures the $N \times N$ matrix submitted to the Judge is free of identity-based bias.

### 3. The Judge (Judge Model)
The final authority that analyzes the network's self-evaluation.
- **Outlier Detection:** Identifies "Byzantine" behavior by looking for nodes whose rankings deviate significantly from the majority or provide inconsistent feedback.
- **Aggregate Consensus:** Calculates the most reliable ranking based on the cross-auditing results.
- **Authoritative Synthesis:** Generates a final report synthesized from the content of the top-ranked "verified" nodes.

---

## Execution Logic

1.  **Request:** User provides a topic.
2.  **Proposal:** $N$ nodes generate responses.
3.  **Prepare:** Anonymized proposals are sent back to all $N$ nodes.
4.  **Audit:** Nodes submit their anonymous rankings to the Judge.
5.  **Commit:** Judge analyzes the $N \times N$ table for Byzantine behavior.
6.  **Finality:** Judge publishes the final authoritative consensus report.
