## 1. Hypothesis (DiabetesDAO Research Agent)

**HYP-MC-01**

> Women with T1D show a measurable rise in glucose and insulin needs during the luteal phase. Without cycle-aware dosing, this produces periods of hyperglycemia and occasional overnight crashes from over-correction. Cycle-aware recommendations improve stability.
> 

---

## 2. Research Agent → HPMP Query

- **Agent:** DiabetesDAO_ResearchAgent_v1
- **Purpose:** Validate cycle-phase insulin variability.
- **Inclusion criteria:** Women 18–45 with T1D, CGM + cycle tracking available.
- **Data requested:**
    - Menstrual cycle phase (LMP → phase) [LOINC 8665-2]
    - CGM night glucose (00:00–06:00) [LOINC 15074-8]
    - Basal insulin units [LOINC 96705-2]
    - Insulin delivery method [LOINC 96706-0]
    - Sleep awakenings [LOINC 80372-6]
    - Symptoms (night sweats [42710-6], dizziness [9535-0], palpitations [49753-3])

*(Show JSON payload for realism)*

---

## 3. Consent Layer (Patient-Facing)

**Patient card example:**

- Requester: DiabetesDAO Research Agent
- Purpose: Study glucose changes across cycle phases in T1D.
- Data requested: 90 days CGM + cycle + basal + sleep logs.
- Options: ✅ Approve | ❌ Decline
- Guarantee: Only aggregated/anonymized results; revocable anytime.

*(In demo, animate k-anonymity counter ticking up until ≥15 consented profiles)*

---

## 4. Matching Process

- **HPMP matches** profiles from two surveys:
    - Flo App (cycle, symptoms, sleep)
    - DiabetesDAO survey (insulin, CGM, delivery method)
- **Overlap set:** 187 matched profiles with valid cycle + CGM + insulin data.

*(Show panel where Flo + DAO survey data merge via LOINC codes → unified schema)*

- Flo App integration
    - The **Flo App** has integrated **Welshare Health Profiles** via HPMP.
    - So, when a user logs symptoms or cycle data in Flo, those answers are automatically stored in their **Welshare profile vault** (encrypted, user-controlled).
    - When the **DiabetesDAO agent** sends a query into HPMP, Flo users with Welshare profiles can receive a **consent request** (e.g., *“Do you want to share your cycle + symptom data with this T1D study?”*).
    - If they approve, HPMP can then link:
        - Flo’s cycle/symptom data (LOINC-coded).
        - DAO’s insulin/CGM data (also stored under their Welshare profile).
    - 

---

So in your demo storyline:

1. **Flo user → Welshare Profile integration**
    - User installs Flo, accepts Welshare integration.
    - Their cycle + symptom data is mirrored into their encrypted Welshare vault.
2. **DAO agent query → HPMP**
    - Agent requests: cycle phase + CGM + insulin dose.
    - HPMP checks user vaults for overlap.
3. **Consent request → Flo app notification**
    - User sees: “DiabetesDAO agent wants to analyze how the menstrual cycle affects glucose control. Approve to share your data?”
    - User approves → data flows *anonymously* into the aggregated analysis.
4. **HPMP merges matched profiles**
    - Because Flo + DAO surveys both use **Welshare profile standardization (LOINC/FHIR)**, HPMP can match without identity leakage.

---

## 5. Results (Synthetic Demo Output)

**Comparison: Luteal vs Follicular nights**

- Mean glucose: **+8.1 mg/dL** in luteal
- Nighttime TIR (70–180 mg/dL): **−6.4 pp**
- Basal insulin dose: **+14%** in luteal
- Glucose variability (CV): **+3.2 pp**
- Symptom co-signal: night sweats +22%, palpitations +11%, dizziness +9%

**Subset of 64 patients who tried cycle-aware adjustments (−10–20% basal on flagged nights):**

- TIR ↑ 7.8 pp
- Mean glucose ↓ 7.3 mg/dL
- Hypoglycemia (<70) no increase

*(In demo: visualize with side-by-side charts)*

---

## 6. Knowledge Graph Update

- New edge: **T1D → Luteal phase → ↑ insulin needs & nocturnal hyperglycemia**
- Mitigation: **Cycle-aware basal adjustment → ↑ TIR, no ↑ hypos**
- Provenance: Flo + DiabetesDAO data, HPMP aggregated validation.
- Confidence score: 0.78

*(Show node-graph animation, adding this edge with a glowing highlight)*

---

## 7. Impact Layer (Patient + Researcher)

- **Research agent output:**
    
    “Validated cycle-phase–dependent insulin variability in T1D. Basal adjustment recommended.”
    
- **Patient-facing tip (synthetic):**
    
    > “We noticed your cycle phase may affect your glucose. Consider a 10–20% basal adjustment on luteal nights — this helped many women avoid highs without extra lows.”
    > 

---

## 8. Closing Demo Script

1. Agent formulates hypothesis.
2. HPMP sends structured query.
3. Patients consent via surveys (Flo + DAO).
4. HPMP matches profiles → aggregates results.
5. Findings: Luteal phase = ↑ glucose, ↑ insulin needs.
6. Cycle-aware dosing reduces instability.
7. Knowledge graph updated → future agents can use this link.
8. Output flows to both researchers and patients.


## 🎯 Cohort Definition (Demo)

**Population:**

- **Women with Type 1 Diabetes**
- Age: **18–45 years** (reproductive age range, consistent with cycle studies)
- Data available:
    - **Cycle tracking** (Flo → LMP, phase, regularity)
    - **CGM data** (night glucose metrics, variability)
    - **Insulin logs** (basal units, delivery method)
    - **Sleep + symptoms** (night sweats, awakenings, dizziness, palpitations)

**Sample size (synthetic):**

- Total matched profiles: **187** (k-anonymity safe, demo-friendly size)
- Split into:
    - **120 pump users** (≈65%)
    - **67 injection users** (≈35%)

**Cycle phases (per user):**

- At least **2 complete cycles logged**
- Balanced representation:
    - Follicular data points: ~350
    - Luteal data points: ~350
    - Ensures enough paired comparisons per user

**CGM baseline (synthetic):**

- Follicular: Mean night glucose ~118 mg/dL, TIR ~75%
- Luteal: Mean night glucose ~126 mg/dL, TIR ~68%
- Variability: +3–4% CV in luteal

**Insulin dose (synthetic):**

- Follicular: 14.0 units basal/night (avg)
- Luteal: 16.0 units basal/night (≈+14%)

**Symptoms (self-reported):**

- Luteal nights:
    - Night sweats: 22% vs 12% (follicular)
    - Palpitations: 11% vs 5%
    - Dizziness: 9% vs 4%
- Sleep awakenings: 1.4 vs 0.8 per night

**Subgroup (intervention):**

- 64 users who tried cycle-aware basal adjustment (−10–20% on flagged nights).
- Outcomes:
    - Nighttime TIR ↑ +7.8%
    - Mean glucose ↓ −7.3 mg/dL
    - Hypo rate: unchanged (safe).
