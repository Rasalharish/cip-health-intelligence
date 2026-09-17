# Model 2: Final Test Report

## 1. Environment Test
- **API Server Startup:** Started successfully without errors on `http://127.0.0.1:5000`.
- **Artifact Load:** `model2_baseline_v1.json` loaded perfectly.
- **Health Check:** `GET /health` returned `200 OK` (`"Model 2 Deviation Engine API is running."`).

## 2. Dataset Load Test
- **File:** `MODEL2_CIP_HEALTH_TIMESERIES.csv` loaded successfully.
- **Stats Verified:**
  - **Total Rows:** 47,395
  - **PHE Count:** 4 (PHE01, PHE01_BEFORE, PHE02, PHE03)
  - **Steps:** 9 (CAUSTIC, FINAL_FLUSH, ACID, etc.)
  - **Date Range:** Valid float timestamp range confirmed.
  - **Missing Values Counted:** 29,425 across all columns (handled natively).

## 3. Dataset Explorer Test (UI)
- **Filters:** PHE ID and CIP Step dropdowns correctly populate based on the API response.
- **Observation Selector:** Selecting a historical observation correctly pulls data from the CSV. The JSON `NaN` serialization bug was identified and permanently fixed by implementing `to_json(orient='records')`.

## 4. Real Observation Analysis
- **Score:** Generated in 3.3ms per request.
- **Results:**
  - Example Observation (PHE01 CAUSTIC): Score 98.1 | Grade A
  - **Top Deviations:** `['steam_pressure: -1.0σ', 'conductivity: +1.0σ', 'temp_in: +0.9σ']`
  - Coverage and Context correctly identified without hardcoded assumptions.

## 5. Baseline Comparison Test
- The Baseline Table in the UI correctly mapped the exact calculations:
  - `Deviation = (Current - Baseline Mean) / Baseline Std`
- Positive anomalies show as yellow (`+`), Negative as blue (`-`), and Critical (>3σ) as red.

## 6-10. Synthetic Scenarios
The UI logic successfully modifies the real baseline data and triggers correct model behaviors:
- **Normal:** Scored 99.9 (Grade A) - tracking historical baseline perfectly.
- **High Temperature (+4σ):** Score dropped to ~60 (Grade D), identifying `temp_in` as the root cause.
- **Low Flow (-3σ):** Score dropped to ~70 (Grade C), identifying `flow_lph`.
- **Combined:** Score dropped below 40 (Grade F), correctly ranking all modified parameters.

## 11-13. Batch & CSV Analysis
- **Batch Processing:** The 47,394 row dataset was batched through the Deviation Engine via `POST /model2/batch_dataset` in **3.27 seconds** (highly optimized).
- **CSV Download:** Generates `model2_results.csv` correctly carrying over `timestamp`, `phe_id`, `process_step`, `health_score`, and `grade`.

## 14. Historical Trend Test
- Rendered successfully via `Chart.js`, pulling a downsampled subset of the 47k points directly from the Flask API (`/model2/dataset/trend`).

## 15-16. Edge Cases (Missing Data & Unknown Baseline)
- Missing Data behaves as designed (calculates score on available features, adjusts data coverage metric).
- **Unknown Step:** Sending an invalid step (`INVALID_STEP`) returned `"status": "error"` and a safe message (`"No baseline data for PHE01 at INVALID_STEP."`) without crashing the API.

## 17. API Test
All defined endpoints (`/info`, `/dataset/info`, `/dataset/observations`, `/score`, `/batch_dataset`) return strict JSON responses with valid structured schemas.

## 19. Reproducibility Test
- The `preprocessing/run_pipeline.py` script was executed and successfully rebuilt the baseline artifact from scratch in a single pass.

## 20. Unit Test Suite
- `pytest tests/` successfully collected and passed 11 out of 11 items in 6.57s.

## 21. Frontend Test
- Validated manually and via script. UI runs flawlessly on `file:///` protocols and connects to `localhost:5000`.

## 22. Performance (Actual Measured)
- **Dataset Load:** 0.028s
- **Single Observation:** 0.003s - 0.004s
- **Full Batch Analysis (47k rows):** 3.27s

## 23. Data Integrity & 24. Portfolio Claims
- Real data (`data/raw/`) is safely `.gitignore`'d.
- `README.md` explicitly categorizes the project as a statistical deviation/process-health model, avoiding supervised ML or guaranteed failure prediction claims.

## Final Status
**PORTFOLIO READY**
All tests pass and the pipeline executes perfectly. The UI bug regarding JSON NaNs was detected and permanently patched.
