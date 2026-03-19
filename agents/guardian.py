import json
import time # 🌟 Required for the sleep function

def guardian_agent(client, deployment_name, hunter_data):
    hunter_json = json.dumps(hunter_data, indent=2)

    prompt = f"""
    You are Guardian Agent, a senior security triage engineer.
    Review these raw vulnerability findings. Your job is to aggressively filter out false positives.
    
    Validation Rules:
    1. If a "dangerous_call" uses hardcoded, safe values (no user input), DROP IT.
    2. If the code clearly sanitizes or casts the input (e.g., int() conversion before DB query), DROP IT.
    3. Downgrade severity if the vulnerability requires highly unlikely local access.
    
    CRITICAL INSTRUCTIONS: 
    - You MUST retain the exact "file" name provided in the Hunter Findings.
    - You MUST evaluate EVERY SINGLE vulnerability in the list. Do not stop early. Do not summarize. 
    - If there are 5 findings in the input, you must verify all 5.

    Return ONLY valid JSON containing ONLY the confirmed, exploitable vulnerabilities:
    {{
      "validated_vulnerabilities": [
        {{
          "file": "exact_filename_here.py",
          "type": "",
          "reason": "",
          "severity": ""
        }}
      ]
    }}

    Hunter Findings:
    {hunter_json}
    """

    # 🌟 The Retry Loop
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                seed=42,
                top_p=0.1,
                max_tokens=4000, 
                timeout=60       
            )

            raw_output = response.choices[0].message.content.strip()

            # Terminal Logging
            print(f"\n[{'='*40}]\n🛡️ GUARDIAN RAW OUTPUT\n[{'='*40}]")
            print(raw_output)

            # Aggressively strip markdown artifacts
            if raw_output.startswith("```json"):
                raw_output = raw_output[7:]
            elif raw_output.startswith("```"):
                raw_output = raw_output[3:]
                
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]

            structured_output = json.loads(raw_output.strip())
            return structured_output # 🌟 SUCCESS: Exit the loop

        except Exception as e:
            print(f"\n[⚠️ GUARDIAN WARNING]: Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2) # 🌟 Pause before retrying

    # 🌟 Fallback if all 3 attempts fail
    print(f"\n[❌ GUARDIAN FATAL ERROR]: Failed after 3 attempts. Passing raw Hunter data through.")
    safe_fallback = hunter_data.get("vulnerabilities", [])
    return {"validated_vulnerabilities": safe_fallback, "error": "Guardian validation failed, showing raw Hunter data."}