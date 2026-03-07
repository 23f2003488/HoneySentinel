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

    raw_output = response.choices[0].message.content.strip()

    # Aggressively strip markdown artifacts
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    elif raw_output.startswith("```"):
        raw_output = raw_output[3:]
        
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]

    raw_output = raw_output.strip()

    try:
        structured_output = json.loads(raw_output)
    except Exception as e:
        structured_output = {"error": f"Invalid JSON: {str(e)}", "raw": raw_output}

    return structured_output