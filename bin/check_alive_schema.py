#!/usr/bin/env python3
"""Verify an ALIVE h5ad against docs/alive_schema.md (T-14 DoD). Exit 1 on any mismatch."""
import sys, numpy as np, anndata as ad, scipy.sparse as sp
EXPECTED = ["cell_barcode", "gene", "guide_id", "target_gene", "assignment_status", "assignment_confidence", "assignment_method",
            "top1_umi", "top2_umi", "total_guide_umi", "sample_id"]
a = ad.read_h5ad(sys.argv[1])
errors = []
if list(a.obs.columns) != EXPECTED:
    errors.append(f"obs columns {list(a.obs.columns)} != {EXPECTED}")
X = a.X if sp.issparse(a.X) else np.asarray(a.X)
data = X.data if sp.issparse(X) else X
if not np.all(np.isfinite(data)) or (data < 0).any(): errors.append("X has non-finite or negative values")
if not np.all(np.equal(np.mod(data, 1), 0)): errors.append("X is not integer-valued")
if a.obs["gene"].isna().any() or (a.obs["gene"].astype(str).str.strip() == "").any(): errors.append("blank/NaN gene labels")
if (a.obs["gene"] == "non-targeting").sum() == 0: errors.append("no non-targeting control cells")
if a.var_names.has_duplicates or (a.var_names == "").any(): errors.append("var index not unique/non-empty")
if a.obs["assignment_confidence"].dtype != np.float32: errors.append(f"assignment_confidence dtype {a.obs['assignment_confidence'].dtype}")
print(f"{sys.argv[1]}: {a.n_obs} cells x {a.n_vars} genes; labels={a.obs['gene'].nunique()}; control={(a.obs['gene']=='non-targeting').sum()}; "
      f"status={a.obs['assignment_status'].value_counts().to_dict()}")
if errors:
    print("SCHEMA ERRORS:\n  " + "\n  ".join(errors)); sys.exit(1)
print("schema OK")
