from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis'/'outputs'/'figures'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})


def box(ax,x,y,w,h,text,fc='#EAF2F8',ec='#1F4E79',fs=10):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.015',facecolor=fc,edgecolor=ec,linewidth=1.5)
    ax.add_patch(p); ax.text(x+w/2,y+h/2,text,ha='center',va='center',wrap=True,fontsize=fs)

def arrow(ax,x1,y1,x2,y2,color='#4C78A8'):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=15,linewidth=1.5,color=color))

# 1 Comparative workflow
fig,ax=plt.subplots(figsize=(12,5)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.5,.95,'Comparative interpretable-ML research workflow',ha='center',va='center',fontsize=16,fontweight='bold',color='#1F4E79')
steps=[('Source freeze','DOI, licence,\nSHA-256 hash'),('Cohort A','56-cat clinical\nstatus/stage'),('Cohort B','195 urine rows;\n41 animal IDs'),('Fold-safe\npreprocessing','Imputation, scaling,\nfeature selection'),('Three model\nfamilies','Logistic, XGBoost,\nEBM'),('Evaluation','OOF metrics,\ngrouped splits'),('Explanation','SHAP, LIME,\nEBM terms'),('Scope control','Ablation, limitations,\nno lead-time claims')]
xs=np.linspace(.03,.88,len(steps))
for x,(t,sub) in zip(xs,steps): box(ax,x,.38,.09,.25,t+'\n'+sub,fs=8.5)
for x in xs[:-1]: arrow(ax,x+.09,.505,x+.12,.505)
ax.text(.5,.18,'Cross-cutting controls: provenance • animal-level grouping • no leakage • reproducible outputs • TRIPOD+AI / PROBAST+AI framing',ha='center',fontsize=10,color='#333')
fig.tight_layout(); fig.savefig(OUT/'comparative_workflow.png',dpi=300,bbox_inches='tight'); plt.close(fig)

# 2 Leakage-safe split
fig,ax=plt.subplots(figsize=(12,5)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.5,.94,'Leakage-safe evaluation for repeated metabolomics observations',ha='center',fontsize=15,fontweight='bold',color='#1F4E79')
# animal rows
animals=[('A',5,'Train'),('B',6,'Train'),('C',8,'Test'),('D',3,'Train'),('E',5,'Test'),('F',6,'Train'),('G',5,'Test')]
for i,(a,n,grp) in enumerate(animals):
 y=.78-i*.09
 ax.text(.05,y+0.02,f'Animal {a}',ha='right',fontsize=9)
 for j in range(n):
  fc='#9ECAE1' if grp=='Train' else '#FDD0A2'
  ax.add_patch(Rectangle((.10+j*.035,y),.025,.045,facecolor=fc,edgecolor='white'))
 ax.text(.43,y+0.02,grp,fontsize=9,color='#1F4E79' if grp=='Train' else '#D95F0E')
ax.text(.58,.79,'✓ All rows from one animal remain together',fontsize=11,fontweight='bold')
ax.text(.58,.69,'✓ Imputation is fitted only on training animals',fontsize=11)
ax.text(.58,.59,'✓ SelectKBest is fitted only on training animals',fontsize=11)
ax.text(.58,.49,'✓ Held-out probabilities are out-of-fold',fontsize=11)
ax.text(.58,.39,'✗ No row-level random split',fontsize=11,color='#B2182B')
ax.text(.5,.12,'Blue = training observations; orange = held-out observations. The actual run used StratifiedGroupKFold with Animal as the grouping key.',ha='center',fontsize=9)
fig.tight_layout(); fig.savefig(OUT/'leakage_safe_group_split.png',dpi=300,bbox_inches='tight'); plt.close(fig)

# 3 model architecture comparison
fig,ax=plt.subplots(figsize=(12,6)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.5,.95,'Model-family comparison and explanation pathway',ha='center',fontsize=15,fontweight='bold',color='#1F4E79')
# shared input
box(ax,.40,.78,.20,.11,'Fold-specific\nfeature matrix',fc='#FFF2CC',fs=11)
for x in [.10,.40,.70]: arrow(ax,.50,.78,x+.10,.68)
box(ax,.05,.48,.22,.20,'Elastic-net\nlogistic regression\n\nLinear coefficients',fc='#E8F5E9',fs=10)
box(ax,.39,.48,.22,.20,'XGBoost\n\nBoosted trees\n\nTreeSHAP / LIME',fc='#FDE9D9',fs=10)
box(ax,.73,.48,.22,.20,'EBM\n\nAdditive shape\nfunctions\n\nNative terms',fc='#E4DFEC',fs=10)
for x in [.16,.50,.84]: arrow(ax,x,.48,x,.33)
box(ax,.20,.12,.60,.12,'Common evaluation layer: AUROC/AUPRC • Brier • balanced accuracy • F1 • calibration • grouped OOF predictions',fc='#D9EAF7',fs=10)
fig.tight_layout(); fig.savefig(OUT/'model_family_comparison.png',dpi=300,bbox_inches='tight'); plt.close(fig)

# 4 XAI triangulation
fig,ax=plt.subplots(figsize=(12,5)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.5,.94,'Triangulated explanation analysis',ha='center',fontsize=15,fontweight='bold',color='#1F4E79')
box(ax,.05,.55,.20,.18,'Prediction\nmodel',fc='#FFF2CC',fs=11)
box(ax,.40,.70,.20,.15,'SHAP\nGlobal attribution',fc='#D9EAF7',fs=10)
box(ax,.40,.48,.20,.15,'LIME\nLocal surrogate',fc='#D9EAF7',fs=10)
box(ax,.40,.26,.20,.15,'EBM\nNative terms',fc='#D9EAF7',fs=10)
for y in [.78,.55,.33]: arrow(ax,.25,.64,.40,y)
box(ax,.75,.52,.20,.22,'Triangulation\n\nAgreement\nStability\nFaithfulness\nClinical plausibility',fc='#E8F5E9',fs=10)
for y in [.78,.55,.33]: arrow(ax,.60,y,.75,.63)
ax.text(.5,.08,'Interpretations are descriptive attributions, not causal effects or proof of clinical validity.',ha='center',fontsize=10,color='#B2182B')
fig.tight_layout(); fig.savefig(OUT/'xai_triangulation.png',dpi=300,bbox_inches='tight'); plt.close(fig)

# 5 circularity ablation
fig,ax=plt.subplots(figsize=(12,4.8)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.text(.5,.93,'Clinical-marker circularity check',ha='center',fontsize=15,fontweight='bold',color='#1F4E79')
box(ax,.04,.48,.25,.22,'Published clinical\nlabel / CKD stage\n\nUses renal evidence',fc='#FDE0DD',ec='#B2182B',fs=10)
box(ax,.38,.48,.25,.22,'Full-marker model\n\nCreatinine, BUN,\nSDMA, USG, proteinuria',fc='#FDE0DD',ec='#B2182B',fs=10)
box(ax,.71,.48,.25,.22,'Near-rule\nreproduction risk\n\nHigh AUROC is not\nindependent novelty',fc='#FDE0DD',ec='#B2182B',fs=10)
arrow(ax,.29,.59,.38,.59,color='#B2182B');arrow(ax,.63,.59,.71,.59,color='#B2182B')
box(ax,.25,.12,.50,.18,'Context-only ablation: remove six label-defining renal markers; evaluate age, weight, body condition, blood pressure, haematology and broader context.',fc='#E8F5E9',ec='#238B45',fs=10)
arrow(ax,.50,.48,.50,.30,color='#238B45')
fig.tight_layout(); fig.savefig(OUT/'clinical_circularity_ablation.png',dpi=300,bbox_inches='tight'); plt.close(fig)

# 6 results comparison bars
fig,axes=plt.subplots(1,2,figsize=(12,4.8))
models=['Logistic','XGBoost','EBM']
full=[clinical_metrics for clinical_metrics in [0.9922580645,0.9819354839,0.9896774194]]
ctx=[0.8954838709,0.8941935484,0.88]
axes[0].bar(models,full,color=['#4C78A8','#F58518','#54A24B']); axes[0].set_ylim(.75,1.02); axes[0].set_title('Clinical full-marker AUROC'); axes[0].set_ylabel('OOF AUROC')
axes[1].bar(models,ctx,color=['#4C78A8','#F58518','#54A24B']); axes[1].set_ylim(.75,1.02); axes[1].set_title('Clinical context-only AUROC'); axes[1].set_ylabel('OOF AUROC')
for ax,vals in zip(axes,[full,ctx]):
 for i,v in enumerate(vals): ax.text(i,v+.008,f'{v:.3f}',ha='center',fontsize=9)
fig.suptitle('Performance changes after removing label-defining renal markers',fontsize=15,fontweight='bold',color='#1F4E79')
fig.tight_layout(); fig.savefig(OUT/'clinical_ablation_comparison.png',dpi=300,bbox_inches='tight'); plt.close(fig)

print('created',len(list(OUT.glob('*.png'))),'diagrams in',OUT)
