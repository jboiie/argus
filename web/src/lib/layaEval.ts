/** Static Step 3/4 evaluation results for the Laya cascade experiment
 *  (PROJECT_DESC.md's "Laya cascade" section) - not live Supabase data,
 *  since these numbers come from a one-time offline eval over saved
 *  Laya/RAGAS scores (redteam/laya_eval.py, redteam/laya_threshold_sweep.py).
 *  Regenerate by hand from those scripts' output if the eval is rerun. */

export const OPERATING_POINTS = {
  cost: { t: 0.5, label: "Cost point" },
  accuracy: { t: 0.8, label: "Accuracy point" },
} as const;

export interface SweepCurvePoint {
  t: number;
  balancedAccuracy: number;
  pctHandledAlone: number;
}

// data/laya_faithfulness_threshold_sweep.jsonl, sweep split (134 rows).
export const SWEEP_CURVE: SweepCurvePoint[] = [
  { t: 0.50, balancedAccuracy: 0.7744, pctHandledAlone: 1.0000 },
  { t: 0.51, balancedAccuracy: 0.7744, pctHandledAlone: 1.0000 },
  { t: 0.52, balancedAccuracy: 0.7883, pctHandledAlone: 0.9851 },
  { t: 0.53, balancedAccuracy: 0.7953, pctHandledAlone: 0.9776 },
  { t: 0.54, balancedAccuracy: 0.8091, pctHandledAlone: 0.9627 },
  { t: 0.55, balancedAccuracy: 0.8230, pctHandledAlone: 0.9403 },
  { t: 0.56, balancedAccuracy: 0.8300, pctHandledAlone: 0.9179 },
  { t: 0.57, balancedAccuracy: 0.8300, pctHandledAlone: 0.9179 },
  { t: 0.58, balancedAccuracy: 0.8439, pctHandledAlone: 0.8955 },
  { t: 0.59, balancedAccuracy: 0.8439, pctHandledAlone: 0.8881 },
  { t: 0.60, balancedAccuracy: 0.8358, pctHandledAlone: 0.8806 },
  { t: 0.61, balancedAccuracy: 0.8336, pctHandledAlone: 0.8507 },
  { t: 0.62, balancedAccuracy: 0.8405, pctHandledAlone: 0.8284 },
  { t: 0.63, balancedAccuracy: 0.8544, pctHandledAlone: 0.8134 },
  { t: 0.64, balancedAccuracy: 0.8463, pctHandledAlone: 0.7985 },
  { t: 0.65, balancedAccuracy: 0.8591, pctHandledAlone: 0.7388 },
  { t: 0.66, balancedAccuracy: 0.8730, pctHandledAlone: 0.7090 },
  { t: 0.67, balancedAccuracy: 0.8649, pctHandledAlone: 0.6940 },
  { t: 0.68, balancedAccuracy: 0.8649, pctHandledAlone: 0.6716 },
  { t: 0.69, balancedAccuracy: 0.8649, pctHandledAlone: 0.6567 },
  { t: 0.70, balancedAccuracy: 0.8649, pctHandledAlone: 0.6418 },
  { t: 0.71, balancedAccuracy: 0.8488, pctHandledAlone: 0.6269 },
  { t: 0.72, balancedAccuracy: 0.8488, pctHandledAlone: 0.6194 },
  { t: 0.73, balancedAccuracy: 0.8477, pctHandledAlone: 0.5821 },
  { t: 0.74, balancedAccuracy: 0.8546, pctHandledAlone: 0.5746 },
  { t: 0.75, balancedAccuracy: 0.8546, pctHandledAlone: 0.5597 },
  { t: 0.76, balancedAccuracy: 0.8616, pctHandledAlone: 0.5224 },
  { t: 0.77, balancedAccuracy: 0.8754, pctHandledAlone: 0.5000 },
  { t: 0.78, balancedAccuracy: 0.8824, pctHandledAlone: 0.4851 },
  { t: 0.79, balancedAccuracy: 0.8743, pctHandledAlone: 0.4552 },
  { t: 0.80, balancedAccuracy: 0.8732, pctHandledAlone: 0.4179 },
  { t: 0.81, balancedAccuracy: 0.8651, pctHandledAlone: 0.3955 },
  { t: 0.82, balancedAccuracy: 0.8582, pctHandledAlone: 0.3507 },
  { t: 0.83, balancedAccuracy: 0.8501, pctHandledAlone: 0.3284 },
  { t: 0.84, balancedAccuracy: 0.8340, pctHandledAlone: 0.2687 },
  { t: 0.85, balancedAccuracy: 0.8179, pctHandledAlone: 0.2239 },
  { t: 0.86, balancedAccuracy: 0.8179, pctHandledAlone: 0.2015 },
  { t: 0.87, balancedAccuracy: 0.8179, pctHandledAlone: 0.1493 },
  { t: 0.88, balancedAccuracy: 0.8098, pctHandledAlone: 0.1194 },
  { t: 0.89, balancedAccuracy: 0.8098, pctHandledAlone: 0.0970 },
  { t: 0.90, balancedAccuracy: 0.8098, pctHandledAlone: 0.0821 },
  { t: 0.91, balancedAccuracy: 0.8098, pctHandledAlone: 0.0522 },
  { t: 0.92, balancedAccuracy: 0.8098, pctHandledAlone: 0.0149 },
  { t: 0.93, balancedAccuracy: 0.8098, pctHandledAlone: 0.0075 },
  { t: 0.94, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 0.95, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 0.96, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 0.97, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 0.98, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 0.99, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
  { t: 1.00, balancedAccuracy: 0.8098, pctHandledAlone: 0.0000 },
];

export interface TestComparisonRow {
  method: string;
  balancedAccuracy: number;
  faithfulPrecision: number;
  faithfulRecall: number;
  unfaithfulPrecision: number;
  unfaithfulRecall: number;
}

// data/laya_faithfulness_eval.json, test split (84 rows, 4 claims).
export const TEST_COMPARISON: TestComparisonRow[] = [
  { method: "RAGAS-only @ 0.7", balancedAccuracy: 0.8646, faithfulPrecision: 0.9643, faithfulRecall: 0.7500, unfaithfulPrecision: 0.8393, unfaithfulRecall: 0.9792 },
  { method: "RAGAS-only, sweep-tuned (t=1.0)", balancedAccuracy: 0.8368, faithfulPrecision: 0.9615, faithfulRecall: 0.6944, unfaithfulPrecision: 0.8103, unfaithfulRecall: 0.9792 },
  { method: "Laya-only / cost point (t=0.50)", balancedAccuracy: 0.8889, faithfulPrecision: 0.8095, faithfulRecall: 0.9444, unfaithfulPrecision: 0.9524, unfaithfulRecall: 0.8333 },
  { method: "Cascade accuracy point (t=0.80)", balancedAccuracy: 0.9340, faithfulPrecision: 0.9697, faithfulRecall: 0.8889, unfaithfulPrecision: 0.9216, unfaithfulRecall: 0.9792 },
];

export const TEST_CLAIMS = 4;
