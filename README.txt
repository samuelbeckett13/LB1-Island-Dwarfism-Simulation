LB1 DEVELOPMENTAL PHYSIOLOGY WEBSITE — VERSION 13.1 AUDITED FINAL

This website matches:
LB1_Developmental_Physiology_Model_v13_1_AUDITED_FINAL.py

PARAMETER-AUDIT CHANGES
1. Normalized IGF-pathway perturbation: 0.20–1.00 -> 0.00–1.00
2. Intergenerational growth-state transmission: 0.05–0.50 -> 0.10–0.29

These changes were made for parameter provenance, not to improve model fit.

Unchanged:
- iodine burden remains a normalized 0–1 latent deficiency index;
- Flores body scale remains a broad fossil-constrained sensitivity prior;
- brain allometry remains a comparative-allometry-derived sensitivity range;
- five-trait score and model architecture remain unchanged.

The browser simulator is explanatory. Definitive thesis inference comes from the Python Monte Carlo model.

GITHUB UPDATE
Replace index.html, styles.css, app.js, and the old V13 Python file with the files in this package.
Then hard-refresh:
Mac: Command + Shift + R
Windows: Ctrl + Shift + R
