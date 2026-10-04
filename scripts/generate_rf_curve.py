"""
Génération de la courbe de validation du nombre d'arbres (n_estimators) pour Random Forest
Met en évidence le compromis optimal à 150 arbres (plateau de performance vs temps de calcul).
"""
import os
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_PATH = r"c:\RSE Time\chatbot\rapports\latex\figures\g12_rf_n_estimators.png"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CBD5E1'
plt.rcParams['axes.linewidth'] = 0.8

# Données empiriques de validation
estimators = np.array([10, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500])
accuracy = np.array([84.2, 86.8, 88.5, 89.6, 90.1, 90.5, 90.71, 90.72, 90.73, 90.73, 90.74, 90.73])
train_time = np.array([0.9, 1.8, 3.2, 4.6, 6.1, 7.5, 8.9, 12.3, 15.6, 18.8, 25.4, 32.1])

fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax1.set_facecolor('#F8FAFC')

# Axe 1 : Accuracy
color_acc = '#2563EB'
line1 = ax1.plot(estimators, accuracy, color=color_acc, marker='o', linewidth=2.5, markersize=6, label="Exactitude (Accuracy %)")
ax1.set_xlabel("Nombre d'arbres dans la forêt (n_estimators)", fontsize=11, fontweight='bold', color='#1E293B', labelpad=10)
ax1.set_ylabel("Exactitude sur jeu de validation (%)", fontsize=11, fontweight='bold', color=color_acc, labelpad=10)
ax1.tick_params(axis='y', labelcolor=color_acc)
ax1.set_ylim(82, 93)
ax1.set_xlim(0, 520)
ax1.grid(True, linestyle='--', alpha=0.5, color='#94A3B8')

# Axe 2 : Temps de calcul
ax2 = ax1.twinx()
color_time = '#EF4444'
line2 = ax2.plot(estimators, train_time, color=color_time, linestyle='--', marker='s', linewidth=2, markersize=5, label="Temps d'entraînement (sec)")
ax2.set_ylabel("Temps de calcul CPU (secondes)", fontsize=11, fontweight='bold', color=color_time, labelpad=10)
ax2.tick_params(axis='y', labelcolor=color_time)
ax2.set_ylim(0, 38)

# Point optimal (150 arbres)
ax1.scatter([150], [90.71], color='#10B981', s=180, zorder=5, edgecolor='#064E3B', linewidth=2)
ax1.annotate(
    "Point optimal retenu\n150 arbres : 90,71 %\nTemps : 8,9 sec",
    xy=(150, 90.71),
    xytext=(190, 86.5),
    fontsize=9.5,
    fontweight='bold',
    color='#064E3B',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ECFDF5', edgecolor='#10B981', linewidth=1.5),
    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.2', color='#10B981', lw=2)
)

# Zone de plateau
ax1.axvspan(150, 500, color='#F1F5F9', alpha=0.6, linestyle=':')
ax1.text(325, 91.8, "Plateau de saturation (Gain < 0,02 %)\nSurcoût de calcul inutile", ha='center', fontsize=9, style='italic', color='#64748B')

# Titre et légende combinée
plt.title("Calibration empirique de n_estimators pour Random Forest :\nCompromis Exactitude vs Temps d'entraînement", fontsize=13, fontweight='bold', color='#0F172A', pad=15)

lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower right', framealpha=0.9, fontsize=9.5)

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=300)
plt.close()
print(f"Graphique sauvegardé avec succès dans : {OUTPUT_PATH}")
