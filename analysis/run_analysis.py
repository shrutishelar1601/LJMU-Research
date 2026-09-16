from __future__ import annotations

import json
import os
import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif

import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBClassifier
from interpret.glassbox import ExplainableBoostingClassifier
import shap
from lime.lime_tabular import LimeTabularExplainer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "feline_public"
OUT = ROOT / "analysis" / "outputs"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
random.seed(42)
np.random.seed(42)

CLINICAL = DATA / "41598_2024_55249_MOESM2_ESM.xlsx"
METAB = DATA / "supplementary" / "pone_2025_s004.xlsx"
METAB_LEGEND = DATA / "supplementary" / "pone_2025_s005.xlsx"


def save_json(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def metric_binary(y, p, threshold=0.5):
    pred = (p >= threshold).astype(int)
    out = {
        "n": int(len(y)),
        "positive": int(np.sum(y)),
        "auroc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "auprc": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else None,
        "brier": float(brier_score_loss(y, p)),
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }
    return out


def metric_multiclass(y, p, classes):
    pred = np.asarray(classes)[np.argmax(p, axis=1)]
    y_int = pd.Categorical(y, categories=classes).codes
    out = {
        "n": int(len(y)),
        "macro_auroc_ovr": None,
        "macro_auprc_ovr": None,
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y, pred, labels=classes).tolist(),
    }
    # Fold-level ROC/PR metrics are undefined when a rare class is absent from the fold.
    if len(np.unique(y_int)) == len(classes):
        out["macro_auroc_ovr"] = float(roc_auc_score(y_int, p, multi_class="ovr", average="macro"))
        out["macro_auprc_ovr"] = float(average_precision_score(pd.get_dummies(pd.Categorical(y, categories=classes)), p, average="macro"))
    # multiclass Brier score using one-vs-rest probabilities
    y_onehot = pd.get_dummies(pd.Categorical(y, categories=classes)).to_numpy()
    out["multiclass_brier"] = float(np.mean(np.sum((p - y_onehot) ** 2, axis=1)))
    return out


def clean_tokens(df):
    df = df.copy()
    tokens = {"-": np.nan, "Unknown": np.nan, "<1": np.nan, ">1.050": np.nan, "1 or 2": np.nan}
    return df.replace(tokens)


def build_xgb(n_classes=2, seed=42):
    if n_classes == 2:
        return XGBClassifier(
            n_estimators=120,
            max_depth=2,
            learning_rate=0.04,
            min_child_weight=2,
            subsample=0.85,
            colsample_bytree=0.8,
            reg_lambda=8.0,
            reg_alpha=0.2,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=seed,
            n_jobs=1,
        )
    return XGBClassifier(
        n_estimators=120,
        max_depth=2,
        learning_rate=0.04,
        min_child_weight=2,
        subsample=0.85,
        colsample_bytree=0.6,
        reg_lambda=8.0,
        reg_alpha=0.2,
        objective="multi:softprob",
        num_class=n_classes,
        eval_metric="mlogloss",
        random_state=seed,
        n_jobs=1,
    )


def clinical_data():
    df = clean_tokens(pd.read_excel(CLINICAL, sheet_name="patient_metadata"))
    df["target_binary"] = (df["CKD Stage (1-4)"].astype(str) != "Healthy").astype(int)
    df["target_stage"] = df["CKD Stage (1-4)"].astype(str)
    # Restrict the main clinical analysis to routine numeric variables; retain missingness through imputation indicators.
    numeric = [
        "Age (years)", "Weight (kg)", "BCS (1-9)", "MCS (0-3)",
        "BP (mmHg)", "HCT (%)", "Creatinine (mg/dL)", "BUN (mg/dL)",
        "SDMA (μg/dL)", "Phosphorus (mg/dL)", "Total Calcium (mg/dL)",
        "Potassium (mEq/L)", "Sodium (mEq/L)", "Albumin (g/dL)",
        "Globulin (g/dL)", "TP (g/dL)", "Cholesterol (mg/dL)",
        "Bicarbonate (mEq/L)", "USG", "Proteinuria (mg/dL)", "TT4 (nmol/L)",
    ]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, numeric


def clinical_binary():
    df, numeric = clinical_data()
    X = df[numeric]
    y = df["target_binary"].to_numpy()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)
    models = {
        "elastic_net_logistic": LogisticRegression(
            penalty="elasticnet", solver="saga", l1_ratio=0.25,
            C=0.25, max_iter=5000, random_state=42,
        ),
        "xgboost": build_xgb(2, 42),
        "ebm": ExplainableBoostingClassifier(
            interactions=0, max_bins=32, max_rounds=80,
            learning_rate=0.03, outer_bags=8, validation_size=0.15,
            random_state=42,
        ),
    }
    results, oof = {}, {}
    for name, model in models.items():
        fold_metrics = []
        probs = np.zeros(len(y), dtype=float)
        counts = np.zeros(len(y), dtype=int)
        for fold, (tr, te) in enumerate(cv.split(X, y)):
            imp = SimpleImputer(strategy="median", add_indicator=True)
            Xtr = imp.fit_transform(X.iloc[tr])
            Xte = imp.transform(X.iloc[te])
            if name == "elastic_net_logistic":
                scaler = StandardScaler()
                Xtr = scaler.fit_transform(Xtr)
                Xte = scaler.transform(Xte)
            model_fold = model
            # clone safely without bringing in additional complexity
            from sklearn.base import clone
            model_fold = clone(model)
            model_fold.fit(Xtr, y[tr])
            p = model_fold.predict_proba(Xte)[:, 1]
            probs[te] += p
            counts[te] += 1
            fold_metrics.append(metric_binary(y[te], p))
        probs = probs / counts
        results[name] = {
            "fold_metrics": fold_metrics,
            "oof_metrics": metric_binary(y, probs),
            "mean_auroc": float(np.mean([m["auroc"] for m in fold_metrics])),
            "sd_auroc": float(np.std([m["auroc"] for m in fold_metrics], ddof=1)),
            "mean_auprc": float(np.mean([m["auprc"] for m in fold_metrics])),
            "sd_auprc": float(np.std([m["auprc"] for m in fold_metrics], ddof=1)),
        }
        oof[name] = probs.tolist()
    save_json(results, OUT / "clinical_binary_metrics.json")
    pd.DataFrame({"y": y, **{k: v for k, v in oof.items()}}).to_csv(OUT / "clinical_binary_oof.csv", index=False)
    return df, numeric, results, oof


def clinical_context_ablation(df, numeric):
    """Repeat binary clinical classification after excluding label-defining renal markers."""
    excluded = {"Creatinine (mg/dL)", "BUN (mg/dL)", "SDMA (μg/dL)", "Phosphorus (mg/dL)", "USG", "Proteinuria (mg/dL)"}
    context_numeric = [c for c in numeric if c not in excluded]
    X = df[context_numeric]
    y = df["target_binary"].to_numpy()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)
    models = {
        "elastic_net_logistic": LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.25, C=0.25, max_iter=5000, random_state=42),
        "xgboost": build_xgb(2, 42),
        "ebm": ExplainableBoostingClassifier(interactions=0, max_bins=32, max_rounds=80, learning_rate=0.03, outer_bags=8, validation_size=0.15, random_state=42),
    }
    results, oof = {}, {}
    for name, model in models.items():
        fold_metrics, probs = [], np.zeros(len(y), dtype=float)
        counts = np.zeros(len(y), dtype=int)
        for tr, te in cv.split(X, y):
            imp = SimpleImputer(strategy="median", add_indicator=True)
            Xtr = imp.fit_transform(X.iloc[tr]); Xte = imp.transform(X.iloc[te])
            if name == "elastic_net_logistic":
                scaler = StandardScaler(); Xtr = scaler.fit_transform(Xtr); Xte = scaler.transform(Xte)
            from sklearn.base import clone
            mf = clone(model); mf.fit(Xtr, y[tr]); p = mf.predict_proba(Xte)[:, 1]
            probs[te] += p; counts[te] += 1; fold_metrics.append(metric_binary(y[te], p))
        probs = probs / counts
        results[name] = {"excluded_markers": sorted(excluded), "context_features": context_numeric, "fold_metrics": fold_metrics, "oof_metrics": metric_binary(y, probs), "mean_auroc": float(np.mean([m["auroc"] for m in fold_metrics])), "sd_auroc": float(np.std([m["auroc"] for m in fold_metrics], ddof=1)), "mean_auprc": float(np.mean([m["auprc"] for m in fold_metrics])), "sd_auprc": float(np.std([m["auprc"] for m in fold_metrics], ddof=1))}
        oof[name] = probs.tolist()
    save_json(results, OUT / "clinical_context_ablation_metrics.json")
    pd.DataFrame({"y": y, **oof}).to_csv(OUT / "clinical_context_ablation_oof.csv", index=False)
    return results, oof


def clinical_stage():
    df, numeric = clinical_data()
    classes = ["1", "2", "3", "4", "Healthy"]
    X = df[numeric]
    y = df["target_stage"].to_numpy()
    # exploratory only due very small stage-1 class
    cv = RepeatedStratifiedKFold(n_splits=3, n_repeats=10, random_state=42)
    models = {
        "elastic_net_logistic": LogisticRegression(
            penalty="elasticnet", solver="saga", l1_ratio=0.25,
            C=0.25, max_iter=5000, random_state=42,
        ),
        "xgboost": build_xgb(len(classes), 42),
    }
    results, oof = {}, {}
    for name, model in models.items():
        fold_metrics = []
        probs = np.zeros((len(y), len(classes)), dtype=float)
        counts = np.zeros(len(y), dtype=int)
        for tr, te in cv.split(X, y):
            imp = SimpleImputer(strategy="median", add_indicator=True)
            Xtr = imp.fit_transform(X.iloc[tr])
            Xte = imp.transform(X.iloc[te])
            scaler = StandardScaler()
            Xtr = scaler.fit_transform(Xtr)
            Xte = scaler.transform(Xte)
            from sklearn.base import clone
            mf = clone(model)
            mf.fit(Xtr, pd.Categorical(y[tr], categories=classes).codes)
            p = mf.predict_proba(Xte)
            # Some folds can omit a rare class; align conservatively.
            aligned = np.zeros((len(te), len(classes)))
            for j, c in enumerate(mf.classes_): aligned[:, int(c)] = p[:, j]
            probs[te] += aligned
            counts[te] += 1
            fold_metrics.append(metric_multiclass(y[te], aligned, classes))
        probs = probs / counts[:, None]
        results[name] = {"fold_metrics": fold_metrics, "oof_metrics": metric_multiclass(y, probs, classes)}
        oof[name] = probs.tolist()
    save_json(results, OUT / "clinical_stage_metrics.json")
    pd.DataFrame({"y": y, "p": [json.dumps(x) for x in oof["xgboost"]]}).to_csv(OUT / "clinical_stage_oof.csv", index=False)
    return results


def explain_clinical(df, numeric):
    X = df[numeric].copy()
    y = df["target_binary"].to_numpy()
    imp = SimpleImputer(strategy="median", add_indicator=True)
    Xi = imp.fit_transform(X)
    feature_names = list(numeric) + [f"missing__{c}" for c in numeric if X[c].isna().any()]
    # Imputer feature names are ordered by sklearn; robustly obtain them if available.
    try:
        feature_names = list(imp.get_feature_names_out(numeric))
    except Exception:
        feature_names = [f"f{i}" for i in range(Xi.shape[1])]
    xgb = build_xgb(2, 42).fit(Xi, y)
    shap_values = shap.TreeExplainer(xgb)(Xi)
    sv = np.asarray(shap_values.values if hasattr(shap_values, "values") else shap_values)
    if sv.ndim == 3: sv = sv[:, :, 1]
    mean_abs = np.mean(np.abs(sv), axis=0)
    order = np.argsort(mean_abs)[::-1]
    shap_imp = pd.DataFrame({"feature": np.array(feature_names)[order], "mean_abs_shap": mean_abs[order]})
    shap_imp.to_csv(OUT / "clinical_xgb_shap_importance.csv", index=False)
    # EBM on the raw numeric matrix after imputation.
    ebm = ExplainableBoostingClassifier(interactions=0, max_bins=32, max_rounds=100, outer_bags=8, random_state=42)
    ebm.fit(Xi, y)
    ebm_scores = np.asarray(ebm.term_importances())
    ebm_imp = pd.DataFrame({"feature": feature_names, "ebm_importance": ebm_scores}).sort_values("ebm_importance", ascending=False)
    ebm_imp.to_csv(OUT / "clinical_ebm_importance.csv", index=False)
    # Logistic coefficients.
    lr = LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.25, C=0.25, max_iter=5000, random_state=42)
    lr.fit(StandardScaler().fit_transform(Xi), y)
    lr_imp = pd.DataFrame({"feature": feature_names, "abs_coefficient": np.abs(lr.coef_[0]), "coefficient": lr.coef_[0]}).sort_values("abs_coefficient", ascending=False)
    lr_imp.to_csv(OUT / "clinical_lr_importance.csv", index=False)
    # LIME explanations for three deterministic examples.
    explainer = LimeTabularExplainer(Xi, feature_names=feature_names, class_names=["Healthy", "CKD"], mode="classification", random_state=42)
    lime_rows = []
    for idx in [0, min(2, len(Xi)-1), len(Xi)-1]:
        exp = explainer.explain_instance(Xi[idx], xgb.predict_proba, num_features=min(10, Xi.shape[1]), num_samples=1000)
        for feat, weight in exp.as_list(label=1): lime_rows.append({"row": idx, "feature": feat, "weight": weight})
    pd.DataFrame(lime_rows).to_csv(OUT / "clinical_lime_examples.csv", index=False)
    return shap_imp, ebm_imp, lr_imp


def metabolomics_data():
    df = pd.read_excel(METAB, sheet_name="Metabolite data")
    legend = pd.read_excel(METAB_LEGEND, sheet_name="Metabolite Legend")
    mapping = dict(zip(legend["Metabolite_id"].astype(str), legend["BIOCHEMICAL"].astype(str)))
    rename_map = {c: mapping.get(str(c), c) for c in df.columns if str(c).startswith("COL")}
    # Preserve IDs even if a legend contains duplicate biochemical names.
    df = df.rename(columns=rename_map)
    df["Animal"] = df["Animal"].astype(str).str.strip()
    features = [c for c in df.columns if c not in ["Animal", "Condition"]]
    X = df[features].apply(pd.to_numeric, errors="coerce")
    y = df["Condition"].astype(str).to_numpy()
    groups = df["Animal"].to_numpy()
    return df, features, X, y, groups


def metabolomics_cv():
    df, features, X, y, groups = metabolomics_data()
    classes = ["Healthy", "CaOx", "CKD"]
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    model_names = ["elastic_net_logistic", "xgboost", "ebm"]
    results = {n: {"fold_metrics": []} for n in model_names}
    oof = {n: np.zeros((len(y), len(classes))) for n in model_names}
    selected_counts = []
    for fold, (tr, te) in enumerate(cv.split(X, y, groups)):
        imp = SimpleImputer(strategy="median", add_indicator=True)
        Xtr0 = imp.fit_transform(X.iloc[tr])
        Xte0 = imp.transform(X.iloc[te])
        # Select features using training data only; keep a compact representation for n=41 groups.
        selector = SelectKBest(f_classif, k=min(40, Xtr0.shape[1]))
        Xtr = selector.fit_transform(Xtr0, pd.Categorical(y[tr], categories=classes).codes)
        Xte = selector.transform(Xte0)
        names = np.array(features)[selector.get_support()]
        selected_counts.extend(names.tolist())
        scaler = StandardScaler()
        Xtr_s = scaler.fit_transform(Xtr)
        Xte_s = scaler.transform(Xte)
        models = {
            "elastic_net_logistic": LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.25, C=0.15, max_iter=5000, random_state=42),
            "xgboost": build_xgb(len(classes), 42 + fold),
            "ebm": ExplainableBoostingClassifier(interactions=0, max_bins=24, max_rounds=80, learning_rate=0.03, outer_bags=6, validation_size=0.15, random_state=42 + fold),
        }
        for name, model in models.items():
            mf = model
            if name == "ebm":
                mf.fit(Xtr, pd.Categorical(y[tr], categories=classes).codes)
                p = mf.predict_proba(Xte)
            else:
                mf.fit(Xtr_s, pd.Categorical(y[tr], categories=classes).codes)
                p = mf.predict_proba(Xte_s)
            aligned = np.zeros((len(te), len(classes)))
            for j, c in enumerate(mf.classes_): aligned[:, int(c)] = p[:, j]
            oof[name][te] = aligned
            results[name]["fold_metrics"].append(metric_multiclass(y[te], aligned, classes))
    for name in model_names:
        results[name]["oof_metrics"] = metric_multiclass(y, oof[name], classes)
        valid_auroc = [m["macro_auroc_ovr"] for m in results[name]["fold_metrics"] if m["macro_auroc_ovr"] is not None]
        results[name]["macro_auroc_mean"] = float(np.mean(valid_auroc)) if valid_auroc else None
        results[name]["macro_auroc_sd"] = float(np.std(valid_auroc, ddof=1)) if len(valid_auroc) > 1 else None
    save_json(results, OUT / "metabolomics_metrics.json")
    pd.DataFrame({"y": y, **{k: [json.dumps(v.tolist()) for v in oof[k]] for k in model_names}, "Animal": groups}).to_csv(OUT / "metabolomics_oof.csv", index=False)
    pd.Series(selected_counts).value_counts().rename_axis("feature").reset_index(name="fold_selection_count").to_csv(OUT / "metabolomics_feature_selection_frequency.csv", index=False)
    return df, features, X, y, groups, results, oof


def explain_metabolomics(df, features, X, y):
    classes = ["Healthy", "CaOx", "CKD"]
    imp = SimpleImputer(strategy="median")
    Xi = imp.fit_transform(X)
    selector = SelectKBest(f_classif, k=min(40, Xi.shape[1]))
    Xs = selector.fit_transform(Xi, pd.Categorical(y, categories=classes).codes)
    names = np.array(features)[selector.get_support()]
    scaler = StandardScaler()
    Xss = scaler.fit_transform(Xs)
    yint = pd.Categorical(y, categories=classes).codes
    xgb = build_xgb(3, 42).fit(Xss, yint)
    shap_values = shap.TreeExplainer(xgb)(Xss)
    vals = shap_values.values if hasattr(shap_values, "values") else shap_values
    vals = np.asarray(vals)
    # Shape: n x p x classes. Aggregate absolute attribution across rows/classes.
    if vals.ndim == 3: mean_abs = np.mean(np.abs(vals), axis=(0, 2))
    else: mean_abs = np.mean(np.abs(vals), axis=0)
    order = np.argsort(mean_abs)[::-1]
    pd.DataFrame({"feature": names[order], "mean_abs_shap": mean_abs[order]}).to_csv(OUT / "metabolomics_xgb_shap_importance.csv", index=False)
    ebm = ExplainableBoostingClassifier(interactions=0, max_bins=24, max_rounds=100, outer_bags=8, random_state=42)
    ebm.fit(Xs, yint)
    ebm_imp = np.asarray(ebm.term_importances())
    pd.DataFrame({"feature": names, "ebm_importance": ebm_imp}).sort_values("ebm_importance", ascending=False).to_csv(OUT / "metabolomics_ebm_importance.csv", index=False)
    return names


def make_figures(clin_df, clin_binary, clin_oof, meta_df, meta_results, meta_oof):
    sns.set_theme(style="whitegrid", context="paper")
    # class distributions
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    clin_df["target_binary"].map({0: "Healthy", 1: "CKD"}).value_counts().reindex(["Healthy", "CKD"]).plot.bar(ax=axes[0], color=["#4C78A8", "#F58518"])
    axes[0].set_title("Clinical cohort")
    axes[0].set_ylabel("Cats")
    meta_df["Condition"].value_counts().reindex(["Healthy", "CaOx", "CKD"]).plot.bar(ax=axes[1], color=["#4C78A8", "#72B7B2", "#F58518"])
    axes[1].set_title("Urine metabolomics cohort")
    axes[1].set_ylabel("Observations")
    fig.tight_layout(); fig.savefig(FIG / "cohort_distributions.png", dpi=300); plt.close(fig)
    # Clinical ROC
    fig, ax = plt.subplots(figsize=(6, 5))
    y = clin_df["target_binary"].to_numpy()
    for name, p in clin_oof.items():
        fpr, tpr, _ = roc_curve(y, p)
        ax.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y,p):.3f})")
    ax.plot([0,1],[0,1],"k--",alpha=.5); ax.set(xlabel="False-positive rate", ylabel="True-positive rate", title="Clinical cohort out-of-fold ROC")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "clinical_roc.png", dpi=300); plt.close(fig)
    # Clinical PR/calibration
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, p in clin_oof.items():
        prec, rec, _ = precision_recall_curve(y, p)
        ax.plot(rec, prec, label=f"{name} (AP={average_precision_score(y,p):.3f})")
    ax.set(xlabel="Recall", ylabel="Precision", title="Clinical cohort precision-recall")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "clinical_pr.png", dpi=300); plt.close(fig)
    # Metabolomics confusion matrices
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    classes=["Healthy","CaOx","CKD"]
    ymeta=meta_df["Condition"].to_numpy()
    for ax,(name,p) in zip(axes,meta_oof.items()):
        pred=np.array(classes)[np.argmax(p,axis=1)]
        cm=confusion_matrix(ymeta,pred,labels=classes)
        sns.heatmap(cm,annot=True,fmt="d",cmap="Blues",cbar=False,ax=ax,xticklabels=classes,yticklabels=classes)
        ax.set_title(name); ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    fig.tight_layout(); fig.savefig(FIG / "metabolomics_confusion_matrices.png", dpi=300); plt.close(fig)


def main():
    clin_df, clin_numeric, cb_results, cb_oof = clinical_binary()
    context_results, context_oof = clinical_context_ablation(clin_df, clin_numeric)
    cs_results = clinical_stage()
    explain_clinical(clin_df, clin_numeric)
    meta_df, meta_features, meta_X, meta_y, meta_groups, mm_results, mm_oof = metabolomics_cv()
    explain_metabolomics(meta_df, meta_features, meta_X, meta_y)
    make_figures(clin_df, cb_results, cb_oof, meta_df, mm_results, mm_oof)
    summary = {
        "clinical_binary": cb_results,
        "clinical_context_ablation": context_results,
        "clinical_stage": cs_results,
        "metabolomics": mm_results,
        "files": [str(x) for x in OUT.rglob("*") if x.is_file()],
    }
    save_json(summary, OUT / "analysis_summary.json")
    print(json.dumps({
        "clinical_binary_oof": {k:v["oof_metrics"] for k,v in cb_results.items()},
        "clinical_stage": {k:v["oof_metrics"] for k,v in cs_results.items()},
        "metabolomics_oof": {k:v["oof_metrics"] for k,v in mm_results.items()},
        "output_dir": str(OUT),
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
