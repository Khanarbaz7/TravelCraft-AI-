import re, json

def parse_llm_output(llm_text: str):
    """
    Parse LLM output safely into JSON.
    Handles minor formatting issues (missing commas, code fences).
    """
    try:
        cleaned = llm_text.strip()

        
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```json")[-1].split("```")[0].strip()
            cleaned = cleaned.replace("```", "").strip()

        
        cleaned = re.sub(r'"\s*"(?!\s*:)', '", "', cleaned)

        
        if '"budget_breakdown"' in cleaned:
            cleaned = re.sub(
                r'("flights":\s*".+?")\s*("stay")',
                r'\1, \2', cleaned, flags=re.DOTALL
            )
            cleaned = re.sub(
                r'("stay":\s*".+?")\s*("food")',
                r'\1, \2', cleaned, flags=re.DOTALL
            )
            cleaned = re.sub(
                r'("food":\s*".+?")\s*("activities")',
                r'\1, \2', cleaned, flags=re.DOTALL
            )

        return json.loads(cleaned)

    except json.JSONDecodeError:
        
        try:
            parsed = eval(cleaned, {"__builtins__": None}, {})
            return json.loads(json.dumps(parsed))
        except Exception as e:
            return {"error": f"Failed to parse LLM output: {e}", "raw": llm_text}
