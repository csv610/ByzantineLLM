# ByzantineLLM - Architecture Documentation

## Overview

ByzantineLLM is a decentralized research framework for studying **Byzantine Fault Tolerance (BFT)** and emergent truth in Large Language Model clusters. It implements a strict N x N ranking protocol where participants are fully anonymous and the system has zero prior knowledge of adversarial agents.

---

## 🏗️ The 6-Step Consensus Workflow

The system follows a deterministic communication flow between independent nodes and a central Judge.

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

---

## 🛡️ The Zero-Trust Analysis Loop

The framework is designed to move from decentralized generation to centralized verification through rigorous cross-auditing and statistical discovery of "Byzantine" behavior.

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
2.  **Proposal:** $N$ nodes generate responses independently.
3.  **Prepare:** Anonymized proposals are sent back to all $N$ nodes.
4.  **Audit:** Nodes submit their anonymous rankings to the Judge.
5.  **Commit:** Judge analyzes the $N \times N$ table for Byzantine behavior.
6.  **Finality:** Judge publishes the final authoritative consensus report.
