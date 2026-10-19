# Q3 Data Analysis Project

A reproducible Python practical for Question 3: AI-powered data analysis and hallucination detection.

The included education dataset is synthetic and contains no real student records. It is designed to demonstrate numeric claim checking. The third AI draft claim about tutoring is intentionally used as a hallucination challenge; the generator does not include tutoring in the exam-score formula.

## Run in VS Code

1. Open this folder in VS Code.
2. In the integrated terminal run:
   ```powershell
   python generate_dataset.py
   python analyze.py
   ```
3. Open `analysis_report.md` and the two `.svg` charts.

Only Python's standard library is required. `analyze.py` reads the CSV, reports missing values and descriptive statistics, computes Pearson correlations and group averages, draws two SVG visualizations, saves a JSON metrics file, and writes the verification report.
