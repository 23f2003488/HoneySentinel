import json

def sentinel_agent(client, deployment_name, guardian_data):

    guardian_json = json.dumps(guardian_data, indent=2)

    prompt = f"""
    You are Sentinel Agent, an expert cybersecurity analyst.

    Based on the Guardian Validated Data below, generate a professional vulnerability report.
    You MUST format your response using the following strictly structured Markdown template:

    ## 🛡️ Executive Summary
    [Write a 2-3 sentence overview of the security posture]

    ## 🚨 Validated Vulnerabilities
    [For each vulnerability, use this format:]
    ### 1. [Vulnerability Type]
    * **Severity:** [Severity Level]
    * **Reason:** [Detailed explanation of the risk]
    * **Location:** `[File Name]` (if provided)

    ## 💡 Recommended Remediation
    [Provide 2-3 actionable steps to secure the code]

    Guardian Validated Data:
    {guardian_json}
    """

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You generate professional security reports."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content