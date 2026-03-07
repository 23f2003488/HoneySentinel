import json

def scout_agent(client, deployment_name, code_content):
    prompt = f"""
You are Scout Agent.

Analyze the Python code and return ONLY valid JSON with this structure:

{{
  "functions": [],
  "imports": [],
  "user_inputs": [],
  "dangerous_calls": []
}}

Do NOT add explanation text.
Only return JSON.

Code:
{code_content}
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You return only JSON."},
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