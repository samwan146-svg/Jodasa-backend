import decimal

class CBCAIEngine:
    @staticmethod
    def generate_remarks_and_predictions(student_profile, subject, current_results):
        """
        Analyzes historical marks to write a professional CBC remark 
        and predict future performance risks.
        """
        if not current_results or len(current_results) == 0:
            return "No assessment records available for analysis.", "Stable"

        # Extract scores and calculate trends
        scores = [float(r.raw_score / r.assessment.max_marks * 100) for r in current_results]
        latest_score = scores[-1]
        
        # 1. Generate Custom Smart Remark based on Competency Level
        if latest_score >= 80:
            remark = f"Exhibits exemplary mastery in {subject}. Demonstrates strong critical thinking and problem-solving capabilities."
        elif latest_score >= 50:
            remark = f"Displays steady understanding of core competencies in {subject}. Capable of executing tasks with minimal supervision."
        elif latest_score >= 30:
            remark = f"Approaching expected standards in {subject}. Shows good effort, but requires more structured practice in foundational concepts."
        else:
            remark = f"Requires close guidance and targeted remediation in {subject} to build essential core competencies."

        # 2. Predictive Analytics (The Standout Early Warning Feature)
        prediction_flag = "Stable"
        if len(scores) >= 2:
            trend = scores[-1] - scores[0]
            if trend <= -7:
                remark += f" ⚠️ Performance tracking indicates a downward trend over recent assessments. Early intervention recommended."
                prediction_flag = "At Risk"
            elif trend >= 7:
                remark += " 🚀 Demonstrates remarkable upward academic growth trajectory this term."
                prediction_flag = "Accelerating"

        return remark, prediction_flag