import json

def guardian_agent(client, deployment_name, hunter_data):

    hunter_json = json.dumps(hunter_data, indent=2)

    prompt = f"""
You are Guardian Agent.

Validate these vulnerability findings.

Remove false positives.
Refine severity if needed.

Return ONLY JSON:

{{
  "validated_vulnerabilities": [
    {{
      "type": "",
      "reason": "",
      "severity": ""
    }}
  ]
}}

Hunter Findings:
{hunter_json}
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "Return only JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_output = response.choices[0].message.content

    try:
        structured_output = json.loads(raw_output)
    except:
        structured_output = {"error": "Invalid JSON", "raw": raw_output}

    return structured_output