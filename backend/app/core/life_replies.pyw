from .ports import JsonMap


def life_strangeness_reply() -> JsonMap:
    return {
        "reply": (
            "先别急着给自己下结论。把怪分成五类：睡眠、身体、学业压力、人际关系、现实感。"
            "如果出现伤害自己的念头、分不清现实、连续多天明显失控，要立刻找可信的人或专业帮助。"
        ),
        "mode": "life_check",
        "checks": ["睡眠", "饮食和身体", "学业压力", "人际关系", "现实感"],
        "boundary": "不诊断，不吓人；先陪用户把异常感拆成可观察事实。",
    }
