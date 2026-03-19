def calculate_risk(guardian_data):
    """
    Calculate overall risk score based on validated vulnerabilities.
    Avoids risk dilution by using a max-severity baseline.
    """
    severity_weights = {
        "Low": 2,
        "Medium": 5,
        "High": 8,
        "Critical": 10
    }

    vulnerabilities = guardian_data.get("validated_vulnerabilities", [])

    if not vulnerabilities:
        return {
            "risk_score": 0,
            "risk_level": "Secure",
            "confidence": 100
        }

    # 1. Find the highest single vulnerability score to set the baseline
    max_severity_val = max(severity_weights.get(v.get("severity", "Low"), 2) for v in vulnerabilities)
    
    # 2. Calculate a baseline score out of 100 based strictly on the highest severity
    base_score = max_severity_val * 10 
    
    # 3. Add a small penalty for every additional vulnerability
    additional_penalty = (len(vulnerabilities) - 1) * 2
    
    # 4. Cap the final score at 100
    final_score = min(100, base_score + additional_penalty)

    # Determine risk level
    if final_score < 30:
        risk_level = "Low"
    elif final_score < 60:
        risk_level = "Medium"
    elif final_score < 85:
        risk_level = "High"
    else:
        risk_level = "Critical"

    confidence = min(95, 70 + (len(vulnerabilities) * 5))

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "confidence": confidence
    }

def generate_risk_insight(client, deployment_name, risk_data, guardian_data):
    prompt = f"""
        You are a cybersecurity risk strategist.

        Given this risk data: {risk_data}
        And these validated vulnerabilities: {guardian_data}

        Provide:
        - A short executive summary (3-4 sentences)
        - Key security concern
        - Immediate action recommendation
    """

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a professional security advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            seed=42,
            top_p=0.1,
            timeout=20
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Risk Insight LLM Call Failed: {e}")
        return "⚠️ **Executive insight temporarily unavailable.** Please review the raw metrics and validated vulnerabilities in the dashboard to assess the system's security posture."