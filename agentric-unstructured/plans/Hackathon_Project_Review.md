# Hackathon Project Plan Review & Recommendations

## 1. Database Schema Gaps
- **Missing Fields**: Broker Commission, Quote Due Date, Construction Type, Post Code, Fire Protection Details
- **Action**: Update `Opportunity` model to include these fields from `Data Mapping.txt`

## 2. Decline Scenario Implementation
- **Missing Integration**: 
  - Post-code knockout lists (2060, 3000, 4000)
  - Wood construction exclusion
  - Inception date validation
  - Minimum declared value ($5M)
- **Action**: Implement rule checks before email generation, referencing `Decline Scenarios and Wording.txt`

## 3. Underwriting Guidelines Integration
- **Missing Implementation**:
  - Flood zone risk scoring
  - Deductible adjustments by risk level
  - Construction type risk weighting
  - Historical claims analysis
- **Action**: Incorporate these into the risk scoring algorithm from `Hackathon_Underwriting Guideline Mock Rules.txt`

## 4. Risk Appetite Document Reference
- **Missing Explicit Reference**:
  - Industry-specific criteria (healthcare, manufacturing, etc.)
  - Construction requirements
  - Risk management practices
- **Action**: Add `risk_appetite_rationale` field to store alignment with appetite document from `zurich-risk-appetite_mid-market-property (2).txt`

## 5. Email Processing Enhancements
- **Missing Structured Data Extraction**: 
  - Fields like broker commission and quote dates
- **Action**: Add email parsing step using `Data Mapping.txt` schema

## 6. Audit Trail Requirements
- **Missing Tracking**: Applied underwriting guidelines
- **Action**: Add `guidelines_applied` field to log referenced rules

---

**Questions for Clarification**
1. Should duplicate checks include all fields from `Data Mapping.txt`?
2. Are specific industries in the risk appetite document (e.g., healthcare) require special handling in narratives?