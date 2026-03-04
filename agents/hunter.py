import json

def hunter_agent(client, deployment_name, scout_data):

    scout_json = json.dumps(scout_data, indent=2)

    prompt = f"""
You are Hunter Agent.

Based on this structured Scout analysis, detect vulnerabilities.

Return ONLY JSON:

{{
  "vulnerabilities": [
    {{
      "type": "",
      "reason": "",
      "severity": ""
    }}
  ]
}}

Scout Data:
{scout_json}
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