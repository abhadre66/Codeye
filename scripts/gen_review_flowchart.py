"""Generate a styled flowchart PNG for the 'paste/upload code review' flow,
matching the visual style of reviewmind_backend_architecture.png."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

BG = "#0d1117"
COLORS = {
    "user": "#7c5cff",       # purple - user action
    "transport": "#3fb68b",  # teal - transport/adapter
    "analysis": "#5aa7e6",   # blue - analysis
    "storage": "#e0c189",    # cream - storage/aggregation
    "ai": "#e08a5a",         # orange - AI
    "done": "#7bbf6a",       # green - completion
}

fig, ax = plt.subplots(figsize=(7.5, 13))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 10)
ax.set_ylim(0, 26)
ax.axis("off")

# title
ax.text(5, 25.3, "ReviewMind — paste / upload code flow", ha="center",
        color="white", fontsize=15, fontweight="bold")
ax.text(5, 24.7, "From raw code to a finished review", ha="center",
        color="#9aa4b2", fontsize=9)


def box(cx, cy, w, h, title, subtitle, color, fontsize=10.5):
    b = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.12",
        linewidth=1.3, edgecolor=color, facecolor=color + "22",
    )
    ax.add_patch(b)
    if subtitle:
        ax.text(cx, cy + h * 0.16, title, ha="center", va="center",
                color="white", fontsize=fontsize, fontweight="bold")
        ax.text(cx, cy - h * 0.26, subtitle, ha="center", va="center",
                color="#c7ccd4", fontsize=8.3)
    else:
        ax.text(cx, cy, title, ha="center", va="center",
                color="white", fontsize=fontsize, fontweight="bold")
    return b


def arrow(x1, y1, x2, y2, color="#5b6472"):
    a = FancyArrowPatch((x1, y1), (x2, y2),
                         arrowstyle="-|>", mutation_scale=14,
                         linewidth=1.2, color=color, shrinkA=0, shrinkB=0)
    ax.add_patch(a)


# 1. User pastes/uploads
box(5, 24, 6.6, 1.3, "You paste code or upload a file",
    "330 lines, several functions", COLORS["user"])
arrow(5, 23.35, 5, 22.85)

# 2. Input adapter
box(5, 22.2, 7.2, 1.3, "Input Adapter",
    "normalize into CodeInput { filename, text }", COLORS["transport"])
arrow(5, 21.55, 5, 21.05)

# 3. Chunking
box(5, 20.4, 7.2, 1.3, "Step 1 · Chunking",
    "AST split -> one chunk per function / class", COLORS["analysis"])
arrow(5, 19.75, 5, 19.25)

# 4. Tagging
box(5, 18.6, 7.2, 1.3, "Step 2 · Tagging",
    "label each chunk: function / test / config / module", COLORS["analysis"])
arrow(5, 17.95, 5, 17.45)

# fan-out label
ax.text(5, 17.15, "for each chunk, run 3 checks in parallel", ha="center",
        color="#9aa4b2", fontsize=8.5, style="italic")

# 5. Three parallel engines
y_eng = 15.7
box(2.0, y_eng, 3.6, 1.9, "Security Engine",
    "secrets · SQLi · unsafe deserialization\nmissing validation · bad deps", COLORS["analysis"], fontsize=9.5)
box(5.5, y_eng, 3.6, 1.9, "Style Engine",
    "reviewmind.yaml rules:\nnaming · line length · docstrings", COLORS["analysis"], fontsize=9.5)
box(9.0, y_eng, 3.6, 1.9, "Complexity Score",
    "count if/for/while/and/or\nper function", COLORS["analysis"], fontsize=9.5)

# arrows from tagging down to each engine
for x in (2.0, 5.5, 9.0):
    arrow(5, 17.95 - 1.5, x, y_eng + 0.95, color="#3a4250")

# converge into findings pile
y_pile = 13.3
arrow(2.0, y_eng - 0.95, 5, y_pile + 0.65, color="#3a4250")
arrow(5.5, y_eng - 0.95, 5, y_pile + 0.65, color="#3a4250")
arrow(9.0, y_eng - 0.95, 5, y_pile + 0.65, color="#3a4250")

box(5, y_pile, 7.2, 1.3, "Collect Findings",
    "SecurityFinding + StyleFinding, tagged with file & line", COLORS["storage"])
arrow(5, y_pile - 0.65, 5, y_pile - 1.15)

# Aggregate + rank
y_rank = y_pile - 1.8
box(5, y_rank, 7.2, 1.3, "Aggregate · Dedup · Rank",
    "worst (security) bubbles to top", COLORS["storage"])
arrow(5, y_rank - 0.65, 5, y_rank - 1.15)

# Send to Claude
y_claude1 = y_rank - 1.8
box(5, y_claude1, 7.2, 1.3, "Send structured findings to Claude",
    "organized pile, function-by-function", COLORS["ai"])
arrow(5, y_claude1 - 0.65, 5, y_claude1 - 1.15)

# Claude writes review
y_claude2 = y_claude1 - 1.8
box(5, y_claude2, 7.2, 1.5, "Claude writes the review",
    "summary + inline comments per function", COLORS["ai"])
arrow(5, y_claude2 - 0.75, 5, y_claude2 - 1.25)

# Final
y_final = y_claude2 - 1.9
box(5, y_final, 7.2, 1.3, "You see the review in the UI",
    "ready to act on", COLORS["done"])

# Legend
legend_items = [
    ("User action", COLORS["user"]),
    ("Input transport", COLORS["transport"]),
    ("Analysis engines", COLORS["analysis"]),
    ("Aggregation / storage", COLORS["storage"]),
    ("AI synthesis (Claude)", COLORS["ai"]),
    ("Completion", COLORS["done"]),
]
handles = [Line2D([0], [0], marker="s", linestyle="", markersize=10,
                   markerfacecolor=c, markeredgecolor=c) for _, c in legend_items]
labels = [l for l, _ in legend_items]
leg = ax.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.045),
                 ncol=3, frameon=False, fontsize=8.5, labelcolor="#c7ccd4")

plt.tight_layout()
plt.savefig("/Users/abhishekbhadre/Documents/Project/Codeye/reviewmind_paste_upload_flow.png",
            dpi=180, facecolor=BG, bbox_inches="tight")
print("saved")
