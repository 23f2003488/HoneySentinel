import json
import time # 🌟 Required for the sleep function

def hunter_agent(client, deployment_name, scout_data, file_name="unknown_file.py"):
    scout_json = json.dumps(scout_data, indent=2)

    prompt = f"""
    You are Hunter Agent, an offensive security researcher.
    Based on this structured attack surface map for the file `{file_name}`, detect exploitable vulnerabilities.

    Methodology:
    - Look for untrusted "user_inputs" flowing into "dangerous_calls" without sanitization.
    - Check for common Python flaws: Command Injection, SQLi, Path Traversal, Insecure Deserialization, and unsafe YAML parsing.
    
    If you find a vulnerability, explain exactly HOW an attacker could trigger it in the "reason" field.

    Return ONLY valid JSON with this exact structure:
    {{
      "vulnerabilities": [
        {{
          "file": "{file_name}",
          "type": "",
          "reason": "",
          "severity": "Low|Medium|High|Critical"
        }}
      ]
    }}

    Scout Data:
    {scout_json}
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
                max_tokens=4000, # 🌟 Prevents truncation
                timeout=60       # 🌟 Extended to prevent silent drops
            )

            raw_output = response.choices[0].message.content.strip()

            # Terminal Logging
            print(f"\n[{'='*40}]\n🎯 HUNTER RAW OUTPUT FOR: {file_name}\n[{'='*40}]")
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
            print(f"\n[⚠️ HUNTER WARNING on {file_name}]: Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2) # 🌟 Pause before retrying

    # 🌟 Fallback if all 3 attempts fail
    print(f"\n[❌ HUNTER FATAL ERROR on {file_name}]: Failed after 3 attempts.")
    return {"vulnerabilities": []}