# FreightGuard AI — Smart Assistant That Watches Shipping Costs

> **FreightTiger 24-Hour AI Case Study Submission**  
> *Role:* Software Engineering Intern (AI)  
> *Candidate:* **Saurabh Kumar** (sk1300374@gmail.com · GitHub: [@SaurabhForge](https://github.com/SaurabhForge))  
> *Status:* Production Ready · 100% Eval Pass (7/7) · 100% Deterministic Reproducibility  

---

## 📋 Case Study Deliverables Checklist

| Case Study Requirement | File / Artifact | Description & Status |
| :--- | :--- | :--- |
| **1. Working Code** | [`detect_anomalies.py`](detect_anomalies.py), [`rag_engine.py`](rag_engine.py), [`app.py`](app.py), [`assistant.py`](assistant.py) | Full detection pipeline, vector store RAG engine, zero-crash multi-threaded server, and standalone CLI assistant. |
| **2. Output CSV** | [`flagged_anomalies.csv`](flagged_anomalies.csv) | Exact contract match with `sample_output_format.csv` (20 anomalies: 17 unexplained, 3 justified). |
| **3. README Report** | [`README.md`](README.md) | Comprehensive engineering report, mathematical formulations, edge-case handling, and verification. |
| **4. Reproducibility Check** | [`reproducibility_check.py`](reproducibility_check.py) | 3-run deterministic verification with identical SHA-256 hash across all three runs (`8eb0b7749ac93412...`). |
| **5. Token / Cost Log** | [`token_cost_log.md`](token_cost_log.md) | Full accounting: 20 LLM calls, 11,400 tokens, **$0.0012 USD (~₹0.10 INR)** total cost per full company run. |
| **6. 10-Min Walkthrough** | [`WALKTHROUGH.md`](WALKTHROUGH.md) | Slide-by-slide 10-minute presentation script and anticipated technical interview Q&A for Round 2. |
| **7. Stretch Goal UI & Q&A** | [`index.html`](index.html), [`route-analytics.html`](route-analytics.html) | Interactive dashboard, Delhi-Jaipur corridor deep-dive, and natural-language Q&A assistant modal. |
| **8. AWS Bedrock AgentCore** | [`AWS_BEDROCK_AGENTCORE.md`](AWS_BEDROCK_AGENTCORE.md), [`freightguard/`](freightguard/) | Enterprise deployment on AWS Bedrock AgentCore (`473412285410`, `ap-south-1`) with 4 autonomous logistics tools and Claude 3 Haiku / Nova runtime. |

## 1. Executive Summary & Problem Overview

Freight rates often quietly creep up across transport corridors. Some price increases stem from genuine operational disruptions (such as highway flooding or festival surcharges), while others represent unjustified margin inflation by carriers.

**FreightGuard AI** is an intelligent auditing system that:
1. Ingests raw multi-leg shipment transaction records.
2. Groups shipments into standard Monday–Sunday weekly cycles.
3. Computes exact ton-kilometer unit costs:
   $$\text{Cost per tonne-km} = \frac{\sum \text{freight\_cost\_inr}}{\sum (\text{quantity\_tonnes} \times \text{distance\_km})}$$
4. Grades each route against two strict benchmarks:
   - **vs. Own History:** Trailing 8-week rolling average cost per tonne-km strictly prior to the current week (no lookahead bias).
   - **vs. Similar Routes:** Current-week peer group average across identical length buckets (`Short`, `Medium`, `Long`), strictly excluding the route itself.
5. Flags anomalous spikes (>20% deviation) and deploys an **anti-hallucination RAG retrieval engine** against contextual field notes.
6. Delivers plain-English operational reasoning and an interactive visual dashboard with natural-language Q&A.

---

## 2. Core Architecture & Workflow

```
┌─────────────────────────────────┐      ┌───────────────────────────────┐
│     shipment_records.csv        │      │       context_notes.csv       │
│  (2,940 shipment transactions)  │      │  (10 operational field notes) │
└────────────────┬────────────────┘      └──────────────┬────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌───────────────────────────────┐
│     Metric Aggregation Engine   │      │   Context Retrieval Engine    │
│  - Monday–Sunday week grouping  │      │  - Route-scope matching       │
│  - Cost/t·km = Total INR/t·km   │      │  - Event window bounding      │
│  - Trailing 8-wk rolling avg    │      │  - Negative-evidence guard    │
│  - Peer-route weekly average    │      │    (rejects distractors)      │
└────────────────┬────────────────┘      └──────────────┬────────────────┘
                 │                                      │
                 ▼                                      │
┌─────────────────────────────────┐                     │
│    Anomaly Trigger (>20% rise)  │                     │
│       (20 candidate weeks)      │◄────────────────────┘
└────────────────┬────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│             Output & Delivery Channels                 │
│  1. flagged_anomalies.csv (exact schema contract)      │
│  2. Interactive Dashboard (index.html)                 │
│  3. Corridor Deep-Dive (route-analytics.html)          │
│  4. Natural Language Assistant Modal                   │
└────────────────────────────────────────────────────────┘
```

---

## 3. Comparison Baselines, Precisely Defined

In accordance with the prompt's grading specification:

### A. vs. Own History (Rolling 8-Week Average)
- For route $R$ at week $W$, baseline $\bar{C}_{\text{hist}}(R, W)$ is the arithmetic mean of the weekly unit costs for up to 8 prior weeks where $w < W$:
  $$\bar{C}_{\text{hist}}(R, W) = \frac{1}{K} \sum_{k=1}^{K} C(R, w_k), \quad K = \min(8, \text{available prior weeks})$$
- **Edge cases handled:** If fewer than 8 prior weeks exist (e.g. during corridor warm-up), the engine uses all available prior weeks without padding or extrapolation. If zero prior weeks exist, it reports `N/A (insufficient prior history)`.

### B. vs. Similar Routes (Peer Group Average)
- For route $R$ of type $T \in \{\text{Short}, \text{Medium}, \text{Long}\}$ at week $W$:
  $$\bar{C}_{\text{peer}}(R, W) = \frac{1}{|P|} \sum_{p \in P} C(p, W), \quad P = \{r \mid \text{type}(r) = T \land r \neq R\}$$
- The route $R$ is strictly excluded from its own peer baseline.

---

## 4. Hallucination Guardrails & Anti-Distractor Defenses

A primary failure mode of LLMs in log auditing is accepting distractor notes that mention routes or dates but explicitly state that costs were unaffected. FreightGuard AI implements deterministic guardrails:

| Note ID | Content Summary | Guardrail Verdict | Engine Decision & Defense |
| :--- | :--- | :--- | :--- |
| **N001** | Chennai–Bangalore highway flooding (Feb 24 – Mar 8, 2025). | **GENUINE JUSTIFICATION** | **Accepted (`No (justified)`)**: Exact corridor match, covers flood weeks with detours and elevated costs. |
| **N002** | Ahmedabad–Mumbai festival week surcharge (Jan 20, 2025). | **GENUINE JUSTIFICATION** | **Accepted (`No (justified)`)**: Exact corridor match and exact date alignment. |
| **N003** | Nationwide diesel price rise (5–7% starting May 5, 2025). | **INSUFFICIENT JUSTIFICATION** | **Rejected (`Yes`)**: A 5–7% fuel rise cannot explain a +25% to +35% rate spike. Flagged for review. |
| **N004** | New toll plaza commissioned on national highway. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Note explicitly states: *"the affected routes are not part of this dataset"*. |
| **N005** | Highway maintenance between Mumbai and Delhi. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Note explicitly states: *"costs were not significantly affected"*. |
| **N006** | Industry report noting stable freight demand. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Cites normal demand with no disruption. Does not justify cost increases. |
| **N007** | Delhi–Jaipur resurfacing and road improvement. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Reports improved road quality, not cost rises. |
| **N008** | Kolkata–Bhubaneswar normal operations. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Reports normal freight movement. |
| **N009** | Chennai–Bangalore route returned to normal on Mar 17. | **NEGATIVE EVIDENCE** | **Rejected (`Yes`)**: Reports return to normalcy; cannot justify high ongoing freight charges. |
| **N010** | Vehicle tracking mandate for commercial fleets. | **EXPLICIT DISTRACTOR** | **Rejected (`Yes`)**: Note explicitly states: *"compliance costs were absorbed by transporters without a rate change"*. |

---

## 5. Verification & Ground Truth Evaluation Harness

To ensure the system can be trusted before submission, we built [`eval_harness.py`](eval_harness.py), which scores against reference cases from `sample_output_format_v2.csv` and tests guardrail defenses.

### Test Execution Output:
```bash
python eval_harness.py
```
```
============================================================
RUNNING FREIGHTGUARD AI EVALUATION HARNESS
============================================================
Successfully processed 728 route-weeks.
Exported 20 records to scratch_eval_output.csv
Anomalies: 17 Unexplained, 3 Justified.
[PASS] Ground Truth Check: Delhi-Jaipur (2024-11-11) -> Cost=4.17, Flag=Yes, Note=None
[PASS] Ground Truth Check: Ahmedabad-Mumbai (2025-01-20) -> Cost=3.29, Flag=No (justified), Note=N002
[PASS] Ground Truth Check: Mumbai-Pune (2025-09-15) -> Cost=3.98, Flag=Yes, Note=None
[PASS] Guardrail Check: Note N010 (costs absorbed without rate change) correctly rejected.
[PASS] Guardrail Check: Note N004 (routes not in dataset) correctly rejected.
[PASS] Guardrail Check: Note N005 (costs unaffected) correctly rejected.
[PASS] Column Contract: Output columns exactly match expected schema.
============================================================
EVALUATION COMPLETE: 7/7 Tests Passed (100% Success)
============================================================
```

---

## 6. Reproducibility Verification (3 Untouched Runs)

The pipeline is 100% deterministic (locked seed and zero-temperature inference). Running [`reproducibility_check.py`](reproducibility_check.py) executes 3 consecutive runs and verifies cryptographic hashes:

```bash
python reproducibility_check.py
```
```
=================================================================
RUNNING 3-RUN REPRODUCIBILITY VERIFICATION
=================================================================
Executing Run 1/3... (SHA-256: 8eb0b7749ac93412...)
Executing Run 2/3... (SHA-256: 8eb0b7749ac93412...)
Executing Run 3/3... (SHA-256: 8eb0b7749ac93412...)

--- COMPARISON RESULTS ---
[SUCCESS] Bit-for-bit identical outputs across all 3 runs.
  * Routes Match: True
  * Weeks Match: True
  * Numbers (cost_per_tonne_km) Match: True
  * Verdicts (flagged) Match: True
  * Cited Notes (matched_note_id) Match: True
=================================================================
REPRODUCIBILITY VERIFIED: 100% Deterministic Output Across 3 Runs
=================================================================
```

---

## 7. Token Usage and Cost Log

Full details are documented in [`token_cost_log.md`](token_cost_log.md).
- **Inference Strategy:** 2-Stage Selective RAG (708 normal weeks bypassed; 20 anomaly weeks evaluated).
- **Total LLM Calls:** 20 calls.
- **Input Tokens:** 9,840.
- **Output Tokens:** 1,560.
- **Total Cost:** **$0.0012 USD (~₹0.10 INR)** per full run on Gemini 1.5 Flash.

---

## 8. Interactive Frontend & Visual Analytics

The submission includes a full, static HTML frontend that requires no local server:

1. [**`index.html`**](index.html) — **Main Anomaly Console**
   - Live KPI metric cards (Total analysed, Unexplained, Justified, Normal).
   - Real-time search, status filtering (`All`, `Flagged Only`, `Justified`, `Normal`), and instant CSV download.
   - Clickable row navigation directly into corridor deep-dives.
   - **Interactive AI Assistant Modal:** Click "Ask Assistant" to ask questions like *"Why did Delhi-Jaipur spike in November?"* or *"What happened to Chennai-Bangalore?"*.

2. [**`route-analytics.html`**](route-analytics.html) — **Corridor Deep-Dive (Delhi–Jaipur · CR-1104)**
   - SVG interactive cost curve across 2024–2025 with baseline guide and highlighted red anomaly spikes.
   - Corridor stats and linked operational notes.
   - Weekly breakdown table with telemetry inspection and dispute escalation audit actions.

---

## 9. 10-Minute Walkthrough Guide for Round 2

| Time | Agenda | Talking Points & Visual Reference |
| :--- | :--- | :--- |
| **00:00 – 02:00** | Problem & Baselines | Explain Monday–Sunday grouping and why trailing 8-week history without lookahead prevents data leakage. |
| **02:00 – 04:30** | The Core Math & Results | Show 728 route-weeks analyzed, 20 anomalies identified. Walk through Delhi-Jaipur (+35.5% spike) and Ahmedabad-Mumbai (+29.5%). |
| **04:30 – 07:00** | Guardrails & Anti-Hallucination | Walk through the trap notes (N010, N004, N005). Show why a naive RAG system fails and how FreightGuard AI correctly caught them. |
| **07:00 – 08:30** | Eval Harness & Reproducibility | Run `python eval_harness.py` and `python reproducibility_check.py` live to demonstrate 100% deterministic output. |
| **08:30 – 10:00** | Interactive UI & Q&A | Open `index.html`, demonstrate filtering, CSV export, corridor deep-dive on Delhi-Jaipur, and interactive assistant queries. |

---

## 10. Quickstart Commands

```bash
# 1. Run the anomaly detection pipeline and export CSV
python detect_anomalies.py

# 2. Run the evaluation harness (asserts 7 ground-truth and guardrail tests)
python eval_harness.py

# 3. Verify 3-run deterministic reproducibility
python reproducibility_check.py

# 4. View the dashboard
# Double-click index.html or open in any browser
```

---

## 11. AWS Bedrock AgentCore Deployment

FreightGuard AI is fully deployed to **AWS Bedrock AgentCore** on **AWS Account `473412285410`** in region **`ap-south-1` (Mumbai)**.

### Autonomous Agent Features:
- **Runtime**: Strands Agent SDK (`strands-agents`) & `bedrock-agentcore`.
- **Bedrock Models**: Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`) and Amazon Nova Lite (`amazon.nova-lite-v1:0`).
- **Autonomous Tools**:
  1. `audit_shipping_corridors()`: Whole-dataset telemetry and dispute identification.
  2. `explain_corridor_discrepancy(corridor, week)`: Single-corridor forensic breakdown with exact baseline comparisons.
  3. `search_operational_context_notes(query)`: Semantic retrieval over field disturbance reports.
  4. `get_carrier_dispute_status(carrier_name)`: Contracted carrier overcharge exposure analysis.

For complete CloudFormation CDK specifications and architecture diagrams, see [AWS_BEDROCK_AGENTCORE.md](AWS_BEDROCK_AGENTCORE.md).

```bash
# Deploy to AWS Bedrock AgentCore via CDK
cd freightguard
agentcore deploy -y -v
```

