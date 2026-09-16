# Dataset Audit for the Companion-Animal CKD Research

Date screened: 2026-08-22

## Decision rule
A candidate was considered suitable for the original early-CKD prediction study only if it had:

- dog or cat veterinary data;
- CKD outcome labels or clinically defensible renal outcomes;
- repeated or time-indexed observations sufficient to define prediction horizons;
- enough metadata to identify animals and prevent animal-level leakage;
- verifiable provenance and a licence/access pathway suitable for academic research.

## Candidates screened

| Candidate | Access status | What is available | Suitability |
|---|---|---|---|
| Dog Aging Project | Restricted through application, Data Use Agreement, and Terra credentials | Public GitHub codebooks and survey instruments; participant-level data not in the public repository | Not currently usable for empirical analysis |
| Morris Animal Foundation Golden Retriever Lifetime Study | Application/approval required | Potential longitudinal canine cohort | Secondary/future validation only unless access is granted |
| GEO GSE303653 | Public download | Feline CKD-related transcriptomic expression matrix; 40 samples from 23 cats, cross-sectional tissue data | Usable only for a redesigned molecular CKD-status study; not for lead-time prediction |
| Scientific Reports 2024 feline metabolomics supplementary workbook | Public supplementary XLSX associated with a peer-reviewed feline CKD study | 56 individual cats; 25 healthy and 31 CKD cats across stages 1–4; 33 clinical/demographic variables including creatinine, BUN, SDMA, USG, proteinuria, blood pressure, weight and CKD stage | Leading feline candidate for a small cross-sectional interpretable CKD-stage/status study; not for longitudinal lead-time prediction |
| PLOS One 2025 feline urine metabolomics raw supplementary data | Public CC BY supporting spreadsheet | 195 urine observations, 635 metabolite features, animal ID, condition labels for Healthy/CaOx/CKD; repeated observations per animal | Leading repeated-measures candidate for grouped interpretable metabolomics classification; not routine clinical CKD staging; raw file has 41 IDs although article reports 42 cats |
| Dryad search: feline chronic kidney disease | Public search | No suitable downloadable longitudinal clinical CKD table identified; one age-estimation dataset surfaced | Not suitable for original study |
| Zenodo search: feline CKD / feline kidney disease | Public API/search | Analysis code, reviews, tissue/omics and unrelated records; no suitable longitudinal clinical table identified | Not suitable for original study |
| PetEVAL / SAVSNET | Public code/benchmark materials | Annotated veterinary free-text EHR benchmark for NLP | Not suitable for structured CKD prediction |
| Kaggle: Veteriary Clinical Dataset | Public download; MIT metadata claim | 10,000 rows of demographics/history/symptoms; dataset description says expanded using synthetic data; no CKD target | Reject for clinical CKD paper |
| Kaggle: Animal Veterinary Health Dataset | Public download; CC BY-SA 4.0 metadata claim | 610 rows focused on pregnancy, delivery, Brucella, and Toxoplasma variables | Reject for CKD paper |
| UCI Chronic Kidney Disease | Public download; CC BY 4.0 | 400 human clinical records | Reject: wrong species and not longitudinal |
| VetCompass feline CKD open-access file | Publicly linked anonymised subset associated with the peer-reviewed feline CKD study; repository states it is for validation/learning exercises only, with no ethical permission for further formal research | Direct file request currently redirected/blocked by the RVC repository; terms also preclude treating it as an unrestricted thesis dataset | Useful for exploration or reproducibility exercise only unless written permission is obtained |
| Morris Animal Foundation Clinical Labs | Publicly described longitudinal canine laboratory dataset; unique dog ID, year in study, visit date, test name/value/units, serum biochemistry and urinalysis | Login required for download; outcome labels/diagnosis linkage are not confirmed from the public description | Strong candidate for a canine protocol if access and CKD outcome definition are confirmed |
| SAVSNET / VetCompass / VMDB | Relevant real-world veterinary data | Controlled access, collaboration, fee, ethics, or request-based pathways; SAVSNET currently reports accepting funded applications only | Possible future/partner route |

## Files downloaded

- `/Users/anuraagd/Downloads/research/data/dap_public/dataRelease/`
  - Public DAP codebooks, survey instruments, and supporting documentation; no participant-level data.
- `/Users/anuraagd/Downloads/research/data/feline_public/GSE303653_select1104.tsv.gz`
  - Public GEO supplementary expression matrix.
- `/Users/anuraagd/Downloads/research/data/feline_public/41598_2024_55249_MOESM2_ESM.xlsx`
  - Public supplementary clinical metadata workbook from a peer-reviewed feline CKD metabolomics study; 56 rows and 33 columns.
- `/Users/anuraagd/Downloads/research/data/feline_public/41598_2025_90019_MOESM1_ESM.docx`
  - Public supplementary tables, formulas, protocols, and performance summaries from a 2025 feline early-detection study; no raw individual-level cohort identified in the file.
- `/Users/anuraagd/Downloads/research/data/feline_public/supplementary/pone_2025_s004.xlsx`
  - Public raw urine metabolomics table associated with a 2025 PLOS One feline renal-disease study; 195 observations, 635 metabolite columns, animal IDs and condition labels.
- `/Users/anuraagd/Downloads/research/data/kaggle_candidates/veteriary-clinical-dataset.zip`
  - Rejected after provenance/target inspection.
- `/Users/anuraagd/Downloads/research/data/kaggle_candidates/animal-veterinary-health-dataset.zip`
  - Rejected as unrelated to CKD.
- `/Users/anuraagd/Downloads/research/data/peteval/repo/`
  - Public PetEVAL code repository; benchmark data are not a structured CKD table.

## Candidates identified but not downloaded

- VetCompass feline CKD survival file: `https://researchonline.rvc.ac.uk/id/eprint/11927/6/Survival_data.xlsx`
  - Search metadata confirms the file and its association with the 2019 VetCompass feline CKD study.
  - Automated download was blocked by a repository redirect/HTTP 403 on 22 August 2026.
  - VetCompass terms state that open-access data are for validation and learning exercises and have no ethical permissions for further formal research.
- Morris Animal Foundation Clinical Labs: `https://datacommons.morrisanimalfoundation.org/artisanal_dataset/111`
  - Public metadata confirms an 11.24 MB clinical-laboratory resource with repeated dog identifiers, study year, visit date, test names/values/units, serum biochemistry, CBC, and urinalysis.
  - Download currently requires a Data Commons login; no credentials were supplied.
  - The public metadata does not confirm a CKD outcome-label table or diagnosis linkage.

## Current conclusion

No immediately downloadable, authentic, longitudinal feline clinical CKD dataset matching the proposal was identified. However, two stronger public feline candidates now exist for redesigned empirical work:

- a 56-cat clinical workbook for CKD status/stage classification;
- a 195-observation repeated urine-metabolomics table with 41 animal IDs and Healthy/CaOx/CKD labels.

The original early-identification and lead-time question cannot be answered with either file because neither provides an appropriate future-onset clinical cohort with routine longitudinal records. The PLOS metabolomics file has repeated samples but is not a routine clinical longitudinal CKD dataset, and its animal-count discrepancy must be investigated.

The defensible choices are:

1. use the 56-cat clinical workbook for a small, clinically grounded CKD status/stage classification thesis;
2. use the PLOS urine-metabolomics file for a grouped, repeated-measures interpretable metabolomics classification thesis;
3. combine both as two separate datasets in a comparative methodology thesis, without pretending they are a single cohort;
4. retain the original early-identification question as a protocol/methodological dissertation with no empirical results;
5. obtain approved access to DAP, Morris, VetCompass, SAVSNET, Banfield, RVC, or another controlled clinical cohort before making early-prediction claims.
