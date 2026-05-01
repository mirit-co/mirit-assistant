import json
import os
import re

import anthropic

from config import ANTHROPIC_API_KEY, ROUTER_MODEL, SKILLS_REGISTRY_PATH

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an intent router for a personal assistant bot.

Given a user message, determine which skill to call and what parameters to pass.

Available skills:
{skills_context}

Respond ONLY with valid JSON in this exact format:
{{
  "skill": "<skill_name>",
  "action": "<action_name>",
  "params": {{<key>: <value>}},
  "confidence": <0.0-1.0>
}}

If the message doesn't match any skill, respond:
{{
  "skill": "unknown",
  "action": "none",
  "params": {{}},
  "confidence": 0.0
}}

Rules:
- skill must be one of the defined skill names
- action must be one of the actions defined for that skill
- params must match the params defined for that action
- Be generous with confidence — prefer routing over rejecting
- User messages may be in Russian or English
"""


def load_skills_context() -> str:
    parts = []
    for fname in sorted(os.listdir(SKILLS_REGISTRY_PATH)):
        if fname.endswith(".md"):
            with open(os.path.join(SKILLS_REGISTRY_PATH, fname)) as f:
                parts.append(f.read())
    return "\n\n---\n\n".join(parts)


def route(user_message: str) -> dict:
    skills_context = load_skills_context()
    system = SYSTEM_PROMPT.format(skills_context=skills_context)

    response = client.messages.create(
        model=ROUTER_MODEL,
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"skill": "unknown", "action": "none", "params": {}, "confidence": 0.0}
