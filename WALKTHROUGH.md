# FreightGuard AI — Round 2 (10-Minute Walkthrough & Defense Guide)

> **FreightTiger 24-Hour AI Case Study**  
> **Candidate:** Saurabh Kumar  
> **Role:** Software Engineering Intern (AI)  
> **Topic:** Automated Shipping Cost Creep Detection & RAG-Powered Audit Assistant  

---

## 1. 10-Minute Presentation Agenda & Timing

```
[00:00 - 02:00]  Problem Definition & Comparison Baselines
[02:00 - 04:30]  Core Detection Pipeline & Mathematical Formulation
[04:30 - 07:00]  Anti-Hallucination Guardrails & Negative-Evidence Retrieval
[07:00 - 08:30]  Verification: Eval Harness (7/7 Passed) & 3-Run Reproducibility
[08:30 - 10:00]  Interactive Live Demo & Stretch Goal Assistant
```

---

## 2. Minute-by-Minute Script

### Minute 00:00 – 02:00: Problem Context & Baselines
* **Hook:** *"Companies pay transporters per tonne-km, but over time, rates quietly creep up. Some increases are valid—monsoons or festival surges—while others are uncommunicated billing inflation. The core challenge is: how do we separate legitimate operational friction from unearned cost creep, at zero hallucination risk?"*
* **Key Architecture Decisions:**
  - Standardized all raw dates into Monday–Sunday weekly cycles (`week_of` = Monday).
  - Computed true weighted unit cost:
    $$\text{Cost per tonne-km} = \frac{\sum \text{freight\_cost\_inr}}{\sum (\text{quantity\_tonnes} \times \text{distance\_km})}$$
  - **Strict No-Lookahead History:** Trailing 8-week rolling baseline strictly looks at $w < W$.
  - **Edge Case Handled:** If fewer than 8 prior weeks exist (e.g., corridor ramp-up), we use all prior weeks available without padding or extrapolation. If 0 prior weeks exist, we report `N/A`.
  - **Self-Excluding Peer Average:** Peer averages across same route length buckets (`Short`, `Medium`, `Long`) strictly exclude the corridor itself to avoid skewing the benchmark.

---

### Minute 02:00 – 04:30: Core Detection Pipeline & Results
* **Dataset Scope:** 2,940 shipment transactions collapsed into 728 unique route-weeks across 6 corridors.
* **Findings Breakdown:**
  - **708 Route-Weeks (97.3%):** Within normal variance (±5% to ±14%). Bypassed LLM inference entirely to conserve tokens.
  - **20 Route-Weeks (2.7%):** Surged $>20\%$ above historical baseline or peer corridor averages.
  - **3 Justified:**
    1. `Ahmedabad-Mumbai` (Jan 20, 2025): ₹3.29/t·km (+29.5% vs past, +22.5% vs peers) → Verified under **Note N002** (Festival week capacity surcharge).
    2. `Chennai-Bangalore` (Feb 24, 2025): ₹3.58/t·km (+31.5% vs past) → Verified under **Note N001** (Highway flooding detour).
    3. `Chennai-Bangalore` (Mar 03, 2025): ₹3.48/t·km (+22.8% vs past) → Verified under **Note N001** (Flooding continuation).
  - **17 Unexplained Anomalies:**
    - `Delhi-Jaipur` (Nov 11 & Nov 18, 2024): Rates spiked to ₹4.17 (+35.5%) and ₹4.09 (+27.6%). No notes or weather events filed. Disputed with NorthFleet Logistics.
    - `Mumbai-Pune` (Sep–Dec 2025): Rates steadily climbed to ₹4.49 (+38.9% vs peers). Flagged for contractual tariff review with Shivam Freight Co.

---

### Minute 04:30 – 07:00: Anti-Hallucination Guardrails & Negative-Evidence Handling
* **The Pitfall of Naive LLM / RAG:** *"If you ask a standard LLM to explain why Mumbai-Pune spiked in late 2025, it finds Note N010 (Vehicle Tracking Mandate, Oct 2025) and eagerly justifies the rate increase. That is an AI hallucination."*
* **Our Guardrail Solution:**
  1. **Negative-Evidence Parsing:** Note N010 explicitly states *"compliance costs were absorbed by transporters without a rate change."* Our engine classifies N010 as an explicit non-justification.
  2. **Corridor Boundary Checking:** Note N004 mentions a toll plaza, but explicitly notes *"affected routes are not part of this dataset."* Instantly rejected.
  3. **Temporal Return-to-Normalcy:** Note N009 reports that Chennai-Bangalore road repairs completed on Mar 9 and returned to normal. When high costs lingered into mid-March (Mar 10 & 17), the engine flagged them because the disruption was over.
  4. **Strict Schema Contract:** Grounding requires `matched_note_id` to be explicitly populated if and only if a valid, applicable note exists; otherwise, blank with verdict `Yes`.

---

### Minute 07:00 – 08:30: Evaluation Harness & Reproducibility Check
* **Lightweight Eval Harness (`eval_harness.py`):**
  - Runs automated assertions against ground-truth benchmark cases from `sample_output_format_v2.csv`.
  - Asserts exact cost calculations, flag status, and guardrail trap rejections.
  - **Result:** **7/7 Tests Passed (100% Success)**.
* **3-Run Reproducibility (`reproducibility_check.py`):**
  - Runs 3 consecutive end-to-end executions on raw input.
  - Cryptographically verifies SHA-256 hash across all three runs (`8eb0b7749ac93412...`).
  - Bit-for-bit identical outputs for routes, weeks, costs, verdicts, and cited notes.
* **Token Cost Efficiency (`token_cost_log.md`):**
  - Selective 2-stage architecture: 20 LLM calls, 9,840 input tokens, 1,560 output tokens.
  - Total inference cost: **$0.0012 USD (~₹0.10 INR)** for the entire company dataset.

---

### Minute 08:30 – 10:00: Interactive Live Demo & UI
* **Show Live Application (`index.html`):**
  - KPI cards with instant status filtering.
  - Instant CSV downloads (`Download AI Audit CSV` and `Export CSV`).
  - Modal inspections for Carriers & Disputes and Settings.
* **Show Corridor Deep-Dive (`route-analytics.html`):**
  - SVG timeline chart for Delhi–Jaipur showing historical baseline vs. Nov 2024 anomaly peak.
  - Telemetry verification & dispute packet exports.
* **Stretch Goal Natural Language Assistant:**
  - Ask: *"Why did Delhi-Jaipur spike in November 2024?"*
  - Assistant responds with exact dates, unit rates, peer comparisons, and flags NorthFleet Logistics.

---

## 3. Anticipated Interviewer Questions & Model Answers

### Q1: "Why did you use trailing 8 weeks instead of calendar months or a centered window?"
> **Answer:** *"Calendar months vary in duration (28 to 31 days) and cross mid-week boundaries. Monday–Sunday cycles give consistent 7-day accounting intervals. Trailing 8 weeks strictly prior to the current week ($w < W$) guarantees zero lookahead bias and avoids data leakage, which is crucial in real-time streaming logistics."*

### Q2: "How did you prevent the LLM from hallucinating reasons when no note existed?"
> **Answer:** *"We instituted a hard two-stage gate. The LLM or semantic matcher is never asked 'Why did this rise happen?'; it is asked 'Does any filed operational note explicitly cover this corridor within this exact date range with non-absorbed cost impact?'. If similarity scores fall below threshold or if negative-evidence tokens are present (e.g. 'absorbed without rate change'), the pipeline deterministically returns `unexplained` without ever invoking creative prose generation."*

### Q3: "What happens if a new route only has 2 weeks of history?"
> **Answer:** *"Our baseline formula dynamically adjusts: $K = \min(8, \text{prior\_weeks})$. For week 3, it computes the rolling average of weeks 1 and 2. We explicitly document this in the README: we never pad or extrapolate synthetic data, as fabricated baselines create false-positive anomaly spikes."*

### Q4: "How does the system scale to millions of shipments across India?"
> **Answer:** *"Metric aggregation uses vectorized Pandas/DuckDB operations that execute in sub-second time. Because 97%+ of shipments fall within normal variance, our 2-stage gating only sends true anomalies to the retrieval layer. This keeps LLM operational cost under ₹100 INR even across nationwide networks."*
