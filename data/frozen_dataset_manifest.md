# Frozen Dataset Manifest

Created: 2026-08-22

## Dataset A: routine clinical feline CKD metadata

- Local file: `/Users/anuraagd/Downloads/research/data/feline_public/41598_2024_55249_MOESM2_ESM.xlsx`
- Sheet: `patient_metadata`
- Source article DOI: `10.1038/s41598-024-55249-5`
- Source URL: `https://www.nature.com/articles/s41598-024-55249-5`
- Supplement URL: `https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41598-024-55249-5/MediaObjects/41598_2024_55249_MOESM2_ESM.xlsx`
- License metadata: Creative Commons Attribution 4.0 (verified through Crossref)
- SHA-256: `c8a8176af20197cdcb489631b193e17379cac906e32f3196c2c57c424feae1d6`
- Shape: 56 rows x 33 columns
- Labels: Healthy 25; CKD stage 1: 3; stage 2: 14; stage 3: 9; stage 4: 5
- Identifiers: patient ID present
- Dates: no visit date present
- Role in thesis: cross-sectional clinical cohort; binary Healthy vs CKD and exploratory ordinal/stage analyses

## Dataset B: repeated feline urine metabolomics

- Local file: `/Users/anuraagd/Downloads/research/data/feline_public/supplementary/pone_2025_s004.xlsx`
- Sheet: `Metabolite data`
- Source article DOI: `10.1371/journal.pone.0329999`
- Source URL: `https://pmc.ncbi.nlm.nih.gov/articles/PMC12360560/`
- Supplement URL: `https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0329999.s004`
- License metadata: Creative Commons Attribution 4.0 (verified through Crossref)
- SHA-256: `016d2e1028c86529b9b3449e6f6b6fea6d454bb485e2da4bdd008b0826c47572`
- Shape: 195 rows x 637 columns
- Labels: Healthy 97; CaOx 54; CKD 44
- Animal IDs: 41 distinct IDs in the downloaded file; the paper reports 42 cats. This discrepancy is retained as a data-quality limitation and will be investigated in preprocessing.
- Repeated measurements: 1–8 observations per animal; median 5
- Features: 635 metabolite columns plus animal ID and condition
- Role in thesis: grouped repeated-measures three-class classification; all splits are by animal ID, never by row

## Scope boundary

Neither dataset contains a suitable prospective future-onset clinical cohort with routine longitudinal visits. Therefore, no lead-time, future-onset, or pre-diagnosis performance claim will be made. Literature-reported early-detection results will be kept separate from results generated in this thesis.
