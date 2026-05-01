from skills.knowledge import KnowledgeSkill
from skills.lists import ListsSkill

SKILLS = {
    skill.name: skill
    for skill in [ListsSkill(), KnowledgeSkill()]
}

FALLBACK_RESPONSE = "Не понял запрос. Попробуй иначе.\nМожешь сохранить заметку, управлять списками.\nНапиши /help чтобы увидеть что я умею."


def dispatch(intent: dict, user_id: int) -> str:
    skill_name = intent.get("skill")
    action = intent.get("action")
    params = intent.get("params", {})
    confidence = intent.get("confidence", 0.0)

    if skill_name == "unknown" or confidence < 0.3:
        return FALLBACK_RESPONSE

    skill = SKILLS.get(skill_name)
    if not skill:
        return f"Навык «{skill_name}» не найден."

    return skill.execute(action, params, user_id)
