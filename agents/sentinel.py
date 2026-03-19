import json

def sentinel_agent(client, deployment_name, guardian_data):
    guardian_json = json.dumps(guardian_data, indent=2)

    prompt = f"""
    You are Sentinel Agent, a developer-friendly security mentor.

    Based on the Guardian Validated Data below, generate a highly readable, actionable security report. 
    Your audience is fast-moving developers ("vibecoders"). Skip the dense corporate jargon. Use emojis, clear formatting, and focus on immediate fixes.

    You MUST format your response using this strictly structured Markdown template:

    ## 🚨 Security Vibe Check
    [Write a punchy, 2-sentence TL;DR of the codebase's security status. Is it a dumpster fire or mostly solid?]

    ## 🐞 The Bugs (Grouped by File)
    [For each file in the data, create a section:]

    ### 📁 `[File Name]`
    * **🔴 [Vulnerability Type]** (Severity: [Severity Level])
    * **The Risk:** [Explain how it gets hacked in plain English]
    * **How to Fix:** [Provide a short, specific code snippet showing the secure way to write it]
  
    ## 🛠️ Next Steps
    [1-2 bullet points on general best practices to prevent this in the future]

    Guardian Validated Data:
    {guardian_json}
    """

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You generate professional security reports."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            seed=42,
            top_p=0.1,
            timeout=45
        )
        
        raw_output = response.choices[0].message.content.strip()

        # Terminal Logging
        print(f"\n[{'='*40}]\n📄 SENTINEL RAW OUTPUT (REPORT)\n[{'='*40}]")
        print(raw_output)

        return raw_output

    except Exception as e:
        print(f"\n[❌ SENTINEL ERROR]: {str(e)}")
        return "## 🚨 Report Generation Failed\n\nThe Sentinel Agent encountered an error while generating the markdown report. Please check the dashboard metrics for raw data."