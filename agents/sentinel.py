import json

def sentinel_agent(client, deployment_name, guardian_data):

    guardian_json = json.dumps(guardian_data, indent=2)

    prompt = f"""
You are Sentinel Agent.

Generate a professional vulnerability report in clean readable format.

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