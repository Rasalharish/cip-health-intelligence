# Phase 1: Data Audit, Preprocessing & Golden Baseline

## 1. Dataset Characteristics

**Size**: 47,395 observations (rows).
**Equipment/PHE Coverage**: PHE01, PHE01_BEFORE, PHE02, PHE03
**Sampling Behavior**: The median sampling interval is 1.0 second.

## 2. CIP States Identified
The dataset was verified to contain observations from actual CIP-related states. We observed the following process steps:
- CAUSTIC
- FINAL_FLUSH
- FLUSHING
- SANITISATION
- ACID
- CIP_STEP_7
- HOLD
- CIP_ACTIVE_UNKNOWN
- INITIAL_FLUSH

> [!WARNING]
> Some states like `CIP_STEP_7` and `CIP_ACTIVE_UNKNOWN` represent undefined phases. In future iterations, these should be confirmed against plant logic to map them to specific cleanings phases or ignored if irrelevant.

## 3. Data-Quality Issues
We audited missingness and suspicious values across the dataset:

**Missing Values:**
- `step_code`: 14,710 missing
- `temp_in`: 14,710 missing
- `status`: 1 missing
- `sample_interval_s`: 4 missing

> [!NOTE]
> Missing values have been retained rather than zero-filled, preserving the data's raw structure and preventing skewed statistical baselines.

**Suspicious Values:**
We generated a `suspicious_values.csv` report flagging physical anomalies:
- Flow dropping below 0.
- Implausible temperatures (e.g., `< 0` or `> 150`).
- Implausible conductivity values (`< 0`).

**Constant Columns:**
Several setpoint and configuration columns remained constant across the dataset, including `caustic_time`, `caustic_cond`, `acid_time`, `acid_cond`, `initial_flush`, `final_flush`, and `sterilization_sp`.

## 4. Features Selected
We engineered targeted process variables and then selected a core set of features for Model 2. 

**Selected Core Features:**
`timestamp`, `phe_id`, `cip_run_id`, `process_step`, `segment_id`, `step_duration_s`, `flow_lph`, `temp_in`, `sterilization_sp`, `temp_error`, `conductivity`, `steam_pressure`, `flow_rolling_mean`, `flow_rolling_std`, `temp_in_rolling_mean`, `cond_rolling_mean`, `temp_in_roc`

**Reasoning:**
Features were chosen to include core flow, temperature, conductivity, and pressure tags, paired with critical engineered variables such as target deviation (`temp_error`), step progression (`step_duration_s`), and rolling statistics.

## 5. Baseline Methodology
The Model 2 deviation engine compares live runs against a Golden Baseline. 

- **Grouping:** The baseline groups statistics by `PHE_ID + CIP_STEP`. This acknowledges that 'normal' behaves differently across different heat exchangers and chemical phases.
- **Statistics Derived:** We compute the Mean, Median, Standard Deviation, Min, Max, and Sample Count for all core features within each group.
- **Artifact:** The baselines and health logic configurations were exported to `models/model2_baseline_v1.json`. 
- **Minimum Data Requirement:** We enforced a rule to only calculate baseline statistics if a minimum of 10 samples are available for a given group and feature.

## 6. Limitations & Required Factory Verifications
> [!IMPORTANT]
> The current Golden Baseline is provisional. It assumes that the historical observations reflect successful, "normal" completed CIP cycles. To finalize the baseline for production monitoring, we require plant-verified normal cycle IDs to ensure the baseline represents the true intended standard of quality.
> Furthermore, any anomalies flagged as `NEEDS FACTORY TAG VALIDATION` in the suspicious values report must be cross-checked to confirm if the issue stems from a sensor scaling fault, a PLC communication error, or real operational variance.
