from app.models.entities import StudentProfile, Job
from app.schemas.domain import EligibilityResponse

def evaluate_eligibility(student: StudentProfile, job: Job) -> EligibilityResponse:
    reasons = []

    # 1. CGPA Check
    if student.cgpa < job.min_cgpa:
        reasons.append(
            f"Minimum CGPA required is {float(job.min_cgpa)}, but your CGPA is {float(student.cgpa)}"
        )

    # 2. 10th Percentage Check
    if student.tenth_pct < job.min_tenth_pct:
        reasons.append(
            f"Minimum 10th percentage required is {float(job.min_tenth_pct)}%, but yours is {float(student.tenth_pct)}%"
        )

    # 3. 12th Percentage Check
    if student.twelfth_pct < job.min_twelfth_pct:
        reasons.append(
            f"Minimum 12th percentage required is {float(job.min_twelfth_pct)}%, but yours is {float(student.twelfth_pct)}%"
        )

    # 4. Active Backlogs Check
    if student.active_backlogs > job.max_backlogs:
        reasons.append(
            f"Maximum allowable backlogs is {job.max_backlogs}, but you currently have {student.active_backlogs}"
        )

    # 5. Skills Matching Check
    if job.required_skills:
        student_skills_lower = {skill.strip().lower() for skill in student.skills}
        missing_skills = [
            skill for skill in job.required_skills
            if skill.strip().lower() not in student_skills_lower
        ]
        if missing_skills:
            reasons.append(f"Missing required skills: {', '.join(missing_skills)}")

    is_eligible = len(reasons) == 0
    return EligibilityResponse(eligible=is_eligible, reasons=reasons)
