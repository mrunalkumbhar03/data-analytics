from pathlib import Path
import csv
import json
import math
import statistics
from html import escape

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "student_performance.csv"

with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    columns = reader.fieldnames or []

numeric_columns = [c for c in columns if c != "Student_ID"]
for row in rows:
    for column in numeric_columns:
        row[column] = float(row[column])


def mean(values):
    return statistics.fmean(values) if values else float("nan")


def pearson(xs, ys):
    xbar, ybar = mean(xs), mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    return numerator / (denom_x * denom_y) if denom_x and denom_y else 0.0

scores = [r["Exam_Score"] for r in rows]
study = [r["Study_Hours_Per_Week"] for r in rows]
attendance = [r["Attendance_Percent"] for r in rows]
assignments = [r["Assignment_Completion_Percent"] for r in rows]

low_study = [r["Exam_Score"] for r in rows if r["Study_Hours_Per_Week"] < 5]
high_study = [r["Exam_Score"] for r in rows if r["Study_Hours_Per_Week"] >= 10]
no_tutor = [r["Exam_Score"] for r in rows if r["Tutoring_Hours_Per_Week"] == 0]
any_tutor = [r["Exam_Score"] for r in rows if r["Tutoring_Hours_Per_Week"] > 0]

attendance_bins = [(50, 64), (65, 74), (75, 84), (85, 94), (95, 100)]
attendance_summary = []
for low, high in attendance_bins:
    subset = [r["Exam_Score"] for r in rows if low <= r["Attendance_Percent"] <= high]
    attendance_summary.append({
        "label": f"{low}-{high}%",
        "low": low,
        "high": high,
        "count": len(subset),
        "mean_score": mean(subset),
    })

missing = {c: sum(1 for r in rows if r[c] in (None, "")) for c in columns}
metrics = {
    "rows": len(rows),
    "columns": columns,
    "missing_values_by_column": missing,
    "score_mean": mean(scores),
    "score_median": statistics.median(scores),
    "score_min": min(scores),
    "score_max": max(scores),
    "study_score_correlation": pearson(study, scores),
    "attendance_score_correlation": pearson(attendance, scores),
    "assignment_score_correlation": pearson(assignments, scores),
    "low_study_count": len(low_study),
    "low_study_mean": mean(low_study),
    "high_study_count": len(high_study),
    "high_study_mean": mean(high_study),
    "study_group_gap": mean(high_study) - mean(low_study),
    "no_tutoring_count": len(no_tutor),
    "no_tutoring_mean": mean(no_tutor),
    "tutoring_count": len(any_tutor),
    "tutoring_mean": mean(any_tutor),
    "tutoring_group_gap": mean(any_tutor) - mean(no_tutor),
    "attendance_summary": attendance_summary,
}
(ROOT / "analysis_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

# SVG chart 1: study hours versus exam score, with a least-squares trend line.
def scatter_svg():
    width, height = 980, 640
    left, right, top, bottom = 100, 40, 95, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    xmin, xmax, ymin, ymax = 0, 16, 0, 100
    xmap = lambda x: left + (x - xmin) / (xmax - xmin) * plot_w
    ymap = lambda y: top + (ymax - y) / (ymax - ymin) * plot_h
    xbar, ybar = mean(study), mean(scores)
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(study, scores)) / sum((x - xbar) ** 2 for x in study)
    intercept = ybar - slope * xbar
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#fbfcf8"/>',
             '<text x="100" y="42" font-family="Arial" font-size="25" font-weight="700" fill="#23332b">Weekly study time and exam score</text>',
             '<text x="100" y="68" font-family="Arial" font-size="14" fill="#68766d">Synthetic education dataset · one dot per simulated student</text>']
    for y in range(0, 101, 20):
        yy = ymap(y)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="#e0e7df"/>')
        parts.append(f'<text x="{left - 14}" y="{yy + 5:.1f}" text-anchor="end" font-family="Arial" font-size="13" fill="#6b776f">{y}</text>')
    for x in range(0, 17, 2):
        xx = xmap(x)
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top + plot_h}" stroke="#eef1eb"/>')
        parts.append(f'<text x="{xx:.1f}" y="{top + plot_h + 25}" text-anchor="middle" font-family="Arial" font-size="13" fill="#6b776f">{x}</text>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#718078" stroke-width="1.5"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#718078" stroke-width="1.5"/>')
    for r in rows:
        parts.append(f'<circle cx="{xmap(r["Study_Hours_Per_Week"]):.1f}" cy="{ymap(r["Exam_Score"]):.1f}" r="4.2" fill="#4e8b70" fill-opacity=".63"/>')
    y1, y2 = intercept + slope * xmin, intercept + slope * xmax
    parts.append(f'<line x1="{xmap(xmin):.1f}" y1="{ymap(y1):.1f}" x2="{xmap(xmax):.1f}" y2="{ymap(y2):.1f}" stroke="#ca8b3b" stroke-width="3"/>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 28}" text-anchor="middle" font-family="Arial" font-size="15" fill="#34443a">Study hours per week</text>')
    parts.append(f'<text x="27" y="{top + plot_h / 2}" text-anchor="middle" transform="rotate(-90 27 {top + plot_h / 2})" font-family="Arial" font-size="15" fill="#34443a">Exam score (0–100)</text>')
    parts.append(f'<circle cx="{left + plot_w - 180}" cy="85" r="5" fill="#4e8b70"/><text x="{left + plot_w - 168}" y="90" font-family="Arial" font-size="13" fill="#59665e">Student</text>')
    parts.append(f'<line x1="{left + plot_w - 105}" y1="85" x2="{left + plot_w - 80}" y2="85" stroke="#ca8b3b" stroke-width="3"/><text x="{left + plot_w - 74}" y="90" font-family="Arial" font-size="13" fill="#59665e">Trend</text>')
    parts.append('</svg>')
    (ROOT / "study_hours_vs_score.svg").write_text("\n".join(parts), encoding="utf-8")

# SVG chart 2: mean exam score by attendance band, with sample sizes.
def attendance_svg():
    width, height = 980, 620
    left, right, top, bottom = 100, 45, 100, 105
    plot_w, plot_h = width - left - right, height - top - bottom
    ymap = lambda y: top + (100 - y) / 100 * plot_h
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#fbfcf8"/>',
             '<text x="100" y="42" font-family="Arial" font-size="25" font-weight="700" fill="#23332b">Average exam score by attendance band</text>',
             '<text x="100" y="68" font-family="Arial" font-size="14" fill="#68766d">Bars show group averages; labels show the number of students in each band</text>']
    for y in range(0, 101, 20):
        yy = ymap(y)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="#e0e7df"/>')
        parts.append(f'<text x="{left - 14}" y="{yy + 5:.1f}" text-anchor="end" font-family="Arial" font-size="13" fill="#6b776f">{y}</text>')
    gap = 35
    bar_w = (plot_w - gap * (len(attendance_summary) + 1)) / len(attendance_summary)
    colors = ["#95b7a1", "#75a58b", "#5f9277", "#4d8068", "#396c57"]
    for i, item in enumerate(attendance_summary):
        x = left + gap + i * (bar_w + gap)
        y = ymap(item["mean_score"])
        h = top + plot_h - y
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="8" fill="{colors[i]}"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#34443a">{item["mean_score"]:.1f}</text>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{top + plot_h + 27}" text-anchor="middle" font-family="Arial" font-size="13" fill="#59665e">{escape(item["label"])}</text>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{top + plot_h + 47}" text-anchor="middle" font-family="Arial" font-size="12" fill="#8a958e">n={item["count"]}</text>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#718078" stroke-width="1.5"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#718078" stroke-width="1.5"/>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 20}" text-anchor="middle" font-family="Arial" font-size="15" fill="#34443a">Attendance percentage</text>')
    parts.append(f'<text x="27" y="{top + plot_h / 2}" text-anchor="middle" transform="rotate(-90 27 {top + plot_h / 2})" font-family="Arial" font-size="15" fill="#34443a">Average exam score</text>')
    parts.append('</svg>')
    (ROOT / "attendance_bands_vs_score.svg").write_text("\n".join(parts), encoding="utf-8")

scatter_svg()
attendance_svg()

report = f'''# Q.3 — AI-Powered Data Analysis and Hallucination Detection

## Dataset and method

This practical uses a **synthetic education dataset** of {len(rows)} simulated student records. It contains no real student information. The reproducible data-generation script is `generate_dataset.py`; run it before the analysis if you want to recreate the CSV. The analysis uses Python's standard library, so no package installation is required.

| Field | Meaning |
|---|---|
| `Student_ID` | Anonymous simulated record ID |
| `Study_Hours_Per_Week` | Weekly study hours |
| `Attendance_Percent` | Attendance percentage |
| `Assignment_Completion_Percent` | Percentage of assignments completed |
| `Tutoring_Hours_Per_Week` | Weekly tutoring hours |
| `Exam_Score` | Exam score from 0 to 100 |

The CSV has **{len(rows)} rows and {len(columns)} columns**. Missing values: **{sum(missing.values())}**. Exam score mean: **{metrics['score_mean']:.1f}**, median: **{metrics['score_median']:.1f}**, range: **{metrics['score_min']:.1f}–{metrics['score_max']:.1f}**.

## Visualizations

1. **Study hours vs. exam score:** each point is one record; the line is a fitted linear trend. Pearson correlation is **r = {metrics['study_score_correlation']:.2f}**.

![Study hours and exam score](study_hours_vs_score.svg)

2. **Average score by attendance band:** bar labels show each band's mean; `n` is the number of records in the band.

![Attendance bands and exam score](attendance_bands_vs_score.svg)

## AI prompt and generated draft

**Prompt used with ChatGPT:** “You are an education data analyst. Review the student performance dataset. Give three concise patterns with numeric evidence, distinguish association from causation, and mention when the data does not support a conclusion.”

**Draft insights for review:**

1. Students studying at least 10 hours per week scored higher on average than students studying under 5 hours per week.
2. Attendance percentage has a positive association with exam score.
3. Tutoring raises exam scores by 10 points.

The third statement is included as a hallucination-detection challenge claim; it must be checked against the data before being accepted.

## Claim verification

| AI claim | Check against the CSV | Result |
|---|---|---|
| Study ≥10 hours is associated with higher scores than study <5 hours. | ≥10 hours: **{metrics['high_study_mean']:.1f}** average (`n={metrics['high_study_count']}`); <5 hours: **{metrics['low_study_mean']:.1f}** (`n={metrics['low_study_count']}`); difference **{metrics['study_group_gap']:.1f}** points. | **Supported as an association.** This does not by itself prove that study hours caused the difference. |
| Attendance is positively associated with exam score. | Pearson correlation **r = {metrics['attendance_score_correlation']:.2f}**; the attendance-band averages are plotted above. | **Supported as an association** in this synthetic dataset. |
| Tutoring raises scores by 10 points. | Any tutoring: **{metrics['tutoring_mean']:.1f}** average (`n={metrics['tutoring_count']}`); no tutoring: **{metrics['no_tutoring_mean']:.1f}** (`n={metrics['no_tutoring_count']}`); observed gap **{metrics['tutoring_group_gap']:+.1f}** points. The generator deliberately does not use tutoring hours in its score formula. | **Incorrect for this dataset.** The claimed 10-point effect is not present; tutoring's measured difference here is a random-group comparison, not a causal estimate. |

## Conclusion and limitations

The dataset shows positive associations between exam score and study hours, and between exam score and attendance. The tutoring claim fails verification. The analysis is a classroom demonstration using simulated data: it cannot support conclusions about real students, and correlations from real observational data would not establish causation. Demographic factors and prior academic performance are not included.

## Run it in VS Code

1. Open this folder in VS Code.
2. Run `python generate_dataset.py` to recreate the CSV.
3. Run `python analyze.py` to regenerate the metrics, charts, and this report.
'''
(ROOT / "analysis_report.md").write_text(report, encoding="utf-8")

print(f"Loaded {len(rows)} rows and {len(columns)} columns")
print(f"Missing values: {sum(missing.values())}")
print(f"Exam score mean={metrics['score_mean']:.2f}, median={metrics['score_median']:.2f}, min={metrics['score_min']:.1f}, max={metrics['score_max']:.1f}")
print(f"Correlation: study={metrics['study_score_correlation']:.3f}, attendance={metrics['attendance_score_correlation']:.3f}, assignments={metrics['assignment_score_correlation']:.3f}")
print(f"Study group means: <5 h={metrics['low_study_mean']:.2f} (n={len(low_study)}), >=10 h={metrics['high_study_mean']:.2f} (n={len(high_study)}), gap={metrics['study_group_gap']:.2f}")
print(f"Tutoring comparison: any={metrics['tutoring_mean']:.2f} (n={len(any_tutor)}), none={metrics['no_tutoring_mean']:.2f} (n={len(no_tutor)}), gap={metrics['tutoring_group_gap']:.2f}")
print("Wrote two SVG charts, analysis_metrics.json, and analysis_report.md")
