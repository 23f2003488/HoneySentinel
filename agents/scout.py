import json
import time # 🌟 ADDED: Required for the sleep function

def scout_agent(client, deployment_name, code_content, file_name="unknown_file.py"):
    prompt = f"""
    You are Scout Agent, a precise static analysis engine. 
    Analyze the Python file named: `{file_name}`.
    Your job is to map the attack surface deterministically.

    Extract a UNIQUE, deduplicated list of exact function, method, or variable names found in the code that match these security categories. Do not explain, describe, or guess. Output ONLY the raw code snippets.

    1. "functions": All defined function/class names.
    2. "imports": All imported modules and libraries.
    3. "user_inputs" (Sources): Any point where external or untrusted data enters the application. Look for web framework request objects (e.g., Django, Flask, FastAPI), CLI arguments, environment variables, file reads, network sockets, or UI input widgets. (Extract the specific method used in the code, e.g., `request.POST.get`, `sys.argv`, `file.read`).
    4. "dangerous_calls" (Sinks): Any function that interacts with the underlying OS, executes logic dynamically, or handles raw data. Look for OS command executions, dynamic evaluation (`eval`/`exec`), raw database query executions, file system writes, or deserialization. (Extract the specific method used in the code, e.g., `subprocess.Popen`, `cursor.execute`, `yaml.load`).

    Return ONLY valid JSON with this exact structure:
    {{
      "file_name": "{file_name}",
      "functions": [],
      "imports": [],
      "user_inputs": [],
      "dangerous_calls": []
    }}

    Code:
    {code_content}
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "You return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                seed=42,
                top_p=0.1,
                max_tokens=4000, # 🌟 ADDED: Gives the AI room to write long JSONs
                timeout=60       # 🌟 CHANGED: Doubled to 60 seconds to prevent silent drops
            )

            raw_output = response.choices[0].message.content.strip()
            
            # Terminal Logging
            print(f"\n[{'='*40}]\n🛰️ SCOUT RAW OUTPUT FOR: {file_name}\n[{'='*40}]")
            print(raw_output)

            # Aggressively strip markdown artifacts
            if raw_output.startswith("```json"):
                raw_output = raw_output[7:]
            elif raw_output.startswith("```"):
                raw_output = raw_output[3:]
                
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]

            structured_output = json.loads(raw_output.strip())
            
            # Fallback to ensure file_name is never lost
            if "file_name" not in structured_output:
                structured_output["file_name"] = file_name
                
            return structured_output # 🌟 SUCCESS: Exits the loop and returns the data

        except Exception as e:
            print(f"\n[⚠️ SCOUT WARNING on {file_name}]: Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2) # 🌟 ADDED: Waits 2 seconds before trying the API again

    # 🌟 ADDED: If it fails all 3 times, it falls back to this safe error state
    print(f"\n[❌ SCOUT FATAL ERROR on {file_name}]: Failed after 3 attempts.")
    return {
        "file_name": file_name,
        "functions": [], "imports": [], "user_inputs": [], "dangerous_calls": [],
        "error": "Scout analysis failed."
    }