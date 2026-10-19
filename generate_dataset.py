from pathlib import Path
import csv
import random

OUT = Path(__file__).parent / "student_performance.csv"
random.seed(2026)

fields = [
    "Student_ID",
    "Study_Hours_Per_Week",
    "Attendance_Percent",
    "Assignment_Completion_Percent",
    "Tutoring_Hours_Per_Week",
    "Exam_Score",
]

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for i in range(1, 151):
        study = round(random.uniform(1, 15), 1)
        attendance = random.randint(55, 100)
        assignments = random.randint(40, 100)
        tutoring = random.choice([0, 0, 0, 1, 2, 3, 4])

        # Synthetic exam scores are based on study, attendance, assignments, and noise.
        # Tutoring is deliberately excluded to test whether an AI invents its effect.
        score = 33 + 2.2 * study + 0.35 * (attendance - 55) + 0.18 * (assignments - 40)
        score += random.gauss(0, 5)
        score = round(min(100, max(0, score)), 1)

        writer.writerow({
            "Student_ID": f"S{i:03d}",
            "Study_Hours_Per_Week": f"{study:.1f}",
            "Attendance_Percent": attendance,
            "Assignment_Completion_Percent": assignments,
            "Tutoring_Hours_Per_Week": tutoring,
            "Exam_Score": f"{score:.1f}",
        })

print(f"Created {OUT.name} with 150 synthetic student records.")
