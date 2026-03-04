def calculate_risk(guardian_data):
    """
    Calculate overall risk score based on validated vulnerabilities.
    """

    severity_weights = {
        "Low": 2,
        "Medium": 5,
        "High": 8,
        "Critical": 10
    }

    vulnerabilities = guardian_data.get("validated_vulnerabilities", [])

    total_score = 0
    max_possible = len(vulnerabilities) * 10

    for vuln in vulnerabilities:
        severity = vuln.get("severity", "Low")
        total_score += severity_weights.get(severity, 2)

    if max_possible == 0:
        return {
            "risk_score": 0,
            "risk_level": "Secure",
            "confidence": 100
        }

    normalized_score = int((total_score / max_possible) * 100)

    # Determine risk level
    if normalized_score < 25:
        risk_level = "Low"
    elif normalized_score < 50:
        risk_level = "Medium"
    elif normalized_score < 75:
        risk_level = "High"
    else:
        risk_level = "Critical"

    # Simple confidence model
    confidence = min(95, 60 + (len(vulnerabilities) * 5))

    return {
        "risk_score": normalized_score,
        "risk_level": risk_level,
        "confidence": confidence
    }


def generate_risk_insight(client, deployment_name, risk_data, guardian_data):

    prompt = f"""
        You are a cybersecurity risk strategist.

        Given this risk data:
        {risk_data}

        And these validated vulnerabilities:
        {guardian_data}

        Provide:
        - A short executive summary (3-4 sentences)
        - Key security concern
        - Immediate action recommendation
        """

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a professional security advisor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content