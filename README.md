# DEGO Project - Team 8
**MSc Business Analytics | Nova SBE | Data Ecosystems and Governance in Organisations (2606)**

---

## Executive Summary

NovaCred is a fintech startup using machine learning to automate credit decisions. Following a regulatory inquiry, our team conducted a full governance audit of the credit application dataset covering data quality, algorithmic fairness, and privacy compliance.

The raw dataset contained **11 documented data quality issues** across completeness, consistency, validity, and accuracy dimensions — all identified and remediated. Bias analysis revealed **statistically significant gender discrimination** (Disparate Impact Ratio of 0.767, below the legal four-fifths threshold) and structural disadvantage for young adults aged 18–25. A proxy variable analysis found that `credit_history_months` acts as a moderate-to-strong proxy for age (r = 0.65), compounding the discriminatory effect. On the privacy side, the dataset contains unprotected PII across 6 fields, with no pseudonymization, audit trail, or data retention policy in place.

Our governance recommendations focus on three priorities: remediating the gender and age bias before any model deployment, implementing pseudonymization and data minimization as baseline GDPR controls, and establishing an audit trail for all automated credit decisions as required under the EU AI Act.

---

## Team Members & Contributions

| Member | Student ID | Role | Contributions |
|---|---|---|---|
| Juan Tobar | 70785 | Data Engineer | Data loading, cleaning pipeline, all quality issue remediation (`01-data-quality.ipynb`), repository structure |
| Javiera Prenafeta | 75087 | Product Lead | README documentation, project coordination, presentation |
| Duarte Carvalho | 59479 | Data Scientist | Bias analysis, fairness metrics, statistical testing, visualisations (`02-bias-analysis.ipynb`) |
| Divakar Santhakumar | 68206 | Governance Officer | GDPR mapping, PII inventory, pseudonymization demo, governance controls (`03-privacy-demo.ipynb`) |

---

## Project Structure

```
dego-project-team8/
├── README.md
├── data/
│   ├── raw_credit_applications.json
│   ├── cleaned_credit_applications.json
│   └── cleaned_credit_data.csv
├── notebooks/
│   ├── 01-data-quality.ipynb
│   ├── 02-bias-analysis.ipynb
│   └── 03-privacy-demo.ipynb
├── output/
│   ├── audit_trail.json
│   ├── credit_data_minimized.csv
│   ├── credit_data_pseudonymized.csv
│   ├── governance_controls_summary.csv
│   ├── pii_inventory.csv
│   └── privacy_governance_summary.csv
├── presentation/
├── reports/
└── src/
    ├── __init__.py
    └── governance_schema.py
```

---

## Notebook 1 — Data Quality Audit
`notebooks/01-data-quality.ipynb`

Identifies and fixes data quality issues in the raw dataset across four dimensions: completeness, consistency, validity, and accuracy.

| # | Issue | Dimension |
|---|---|---|
| 1 | Duplicate records & SSN conflicts | Uniqueness |
| 2 | Malformed SSN formats | Accuracy |
| 3 | Schema drift: `annual_salary` vs `annual_income` | Consistency |
| 4 | Missing / incomplete records | Completeness |
| 5 | Mixed data types in numeric fields | Consistency |
| 6 | Inconsistent gender coding (`M/F` vs `Male/Female`) | Consistency |
| 7 | Heterogeneous date formats (ISO, European, non-standard) | Consistency |
| 8 | Impossible / out-of-range values | Validity |
| 9 | Invalid email addresses | Accuracy |
| 10 | Cross-column logical contradictions | Validity |
| 11 | Age validation (underage, future dates, over-100) | Accuracy |

Output: `data/cleaned_credit_data.csv`

---

## Notebook 2 — Bias Analysis
`notebooks/02-bias-analysis.ipynb`

Audits the cleaned dataset for fairness issues before it feeds into any automated credit scoring logic.

**Chapter 2 — Cleaning Audit:** Verifies the cleaning pipeline worked correctly. A bug was caught here — the process had introduced a 70% spike in missing values for `date_of_birth`, which was flagged and fixed.

**Chapter 3 — Bias Studies:**
- **Gender:** Male applicants have a significantly higher approval rate. Disparate Impact Ratio of **0.767** (below the 0.8 four-fifths threshold), meaning women need stronger financial profiles to get approved.
- **Age:** Young adults (18–25) fall below the Disparate Impact threshold, facing structural disadvantage despite reasonable financial metrics.
- **Proxy bias:** `credit_history_months` correlates with age at **0.65**, effectively penalising younger applicants for time lived rather than financial behaviour.
- **Interaction effects:** Worst-hit groups are young adults and seniors with low income (~31–33% approval) and young women (31.8%).

---

## Notebook 3 — Privacy Demo
`notebooks/03-privacy-demo.ipynb`

Governance Officer deliverable covering privacy engineering controls on the cleaned dataset.

1. **PII Inventory** — classifies every field by identifier type, GDPR category, and risk level
2. **Pseudonymization** — SHA-256 salted hashing on direct identifiers (SSN, email), stored in `*_pseudo` columns
3. **Data Minimisation** — generalises `date_of_birth` to `age_band`, ZIP to `zip3`, aggregates spending indicators
4. **Governance Controls Summary** — maps controls to GDPR articles and EU AI Act requirements
5. **Audit Trail** — timestamped log of every governance action
6. **GDPR Mapping** — academic mapping to Art. 5, 6, 25, 32, 89

---

## Privacy Assessment

The dataset contains PII across 6 fields with varying risk levels:

| Field | Type | Risk | Status |
|---|---|---|---|
| `applicant_info.ssn` | Direct identifier | Critical | Pseudonymized |
| `applicant_info.email` | Direct identifier | High | Pseudonymized |
| `applicant_info.full_name` | Direct identifier | High | Pseudonymized |
| `applicant_info.ip_address` | Quasi-identifier | Medium | Minimized |
| `applicant_info.date_of_birth` | Quasi-identifier | Medium | Generalized → `age_band` |
| `applicant_info.zip_code` | Quasi-identifier | Low | Generalized → `zip3` |

Key GDPR gaps identified in the raw dataset: no pseudonymization on any field, no data retention policy, no consent tracking, no audit trail for automated decisions, and behavioral spending data collected beyond what is necessary for credit decisions (Art. 5(1)(c) — data minimisation).

---

## Governance Recommendations

### Immediate actions (before any model deployment)
1. **Rebalance the training data** to address the gender DI ratio of 0.767 — either through re-sampling or by applying fairness constraints during model training.
2. **Replace `credit_history_months` as a standalone feature** or normalise it by age, to remove its proxy effect on young applicants.
3. **Implement pseudonymization** on all direct identifiers (SSN, email, full name) before data is used for model training — the demo pipeline in Notebook 3 is ready to deploy.

### Short-term controls
4. **Establish a data retention policy** defining how long credit applications are stored and under what lawful basis (GDPR Art. 6 and Art. 5(1)(e)).
5. **Deploy an automated audit trail** for every credit decision, logging the model version, input features used, and outcome — required under EU AI Act obligations for high-risk AI systems.
6. **Add a human oversight step** for borderline decisions and all rejections, with a documented escalation path (EU AI Act Art. 14).

### Long-term governance
7. **Run quarterly bias audits** using the Disparate Impact Ratio as a monitoring metric, with a mandatory review if DI drops below 0.8 for any protected group.
8. **Formalise a consent mechanism** that clearly explains to applicants how their data is used in automated decision-making (GDPR Art. 13/14 and Art. 22).
9. **Conduct a Data Protection Impact Assessment (DPIA)** before any production deployment, as required for high-risk processing under GDPR Art. 35.

---

## Dependencies

```bash
pip install pandas numpy matplotlib seaborn scipy
```

Python 3.9+
