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

    raw_output = response.choices[0].message.content

    try:
        structured_output = json.loads(raw_output)
    except:
        structured_output = {"error": "Invalid JSON returned", "raw": raw_output}

    return structured_output