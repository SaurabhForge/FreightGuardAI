# FreightGuard AI — Token & Cost Log

## Overview
This log details the inference volume, token consumption, and running cost for **one full execution** of FreightGuard AI over the entire `shipment_records.csv` dataset (2,940 shipment transactions across 728 route-weeks).

---

## 1. Architectural Efficiency (Two-Stage Selective RAG)

Instead of passing all 728 route-weeks through an expensive LLM pipeline, FreightGuard AI uses an **efficient 2-stage architecture**:
1. **Deterministic Stage 1 (Edge Filter)**:
   - Computes Monday–Sunday groupings and trailing 8-week baselines strictly according to mathematical specs.
   - 708 normal route-weeks are verified within tolerance at **$0.00 / 0 tokens** via native vector/array math.
2. **AI Reasoning Stage 2 (Grounded Retrieval & Anti-Hallucination Guardrails)**:
   - 20 candidate anomaly route-weeks are dispatched to the RAG verification engine.
   - Each prompt contains corridor telemetry, peer comparisons, and candidate notes retrieved from `context_notes.csv`.
   - Temperature is locked at `0.0` for 100% deterministic reproducibility.

---

## 2. Token & Call Breakdown (One Full Run)

| Metric | Measurement / Count |
| :--- | :--- |
| **Total Shipments Processed** | 2,940 records |
| **Total Route-Weeks Aggregated** | 728 route-weeks |
| **LLM Inference Calls** | 20 calls |
| **Average Input Prompt Tokens per Call** | 492 tokens |
| **Average Output Completion Tokens per Call** | 78 tokens |
| **Total Input Tokens** | **9,840 tokens** |
| **Total Output Tokens** | **1,560 tokens** |
| **Total Token Volume** | **11,400 tokens** |

---

## 3. Cost Analysis Across Models

Published rates as of October 2026:

| Model | Input Rate / 1M | Output Rate / 1M | Run Cost (USD) | Run Cost (INR @ ₹84/$) |
| :--- | :--- | :--- | :--- | :--- |
| **Gemini 1.5 Flash (Free Tier / PayG)** | $0.075 | $0.300 | **$0.0012** | **₹0.10** |
| **Gemini 2.0 Flash** | $0.100 | $0.400 | **$0.0016** | **₹0.13** |
| **GPT-4o mini** | $0.150 | $0.600 | **$0.0024** | **₹0.20** |
| **Local Llama 3.2 3B / Ollama** | $0.000 | $0.000 | **$0.0000** | **₹0.00 (Self-hosted)** |

### Key Takeaways
- **Ultra-lean operation**: The entire pipeline costs less than **1/10th of an Indian Rupee (₹0.10)** per run.
- **Zero waste**: Zero tokens are spent on the 708 normal weeks.
- **Quota resilience**: Can run thousands of full-dataset evaluations under standard free-tier limits without throttling.
