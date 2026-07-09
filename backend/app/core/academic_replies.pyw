from .ports import JsonMap


def academic_risk_reply() -> JsonMap:
    return {
        "reply": (
            "先止血，不许空焦虑。立刻列成绩构成、已得分、剩余作业、考试时间，"
            "再联系老师或助教确认补交、补测、补考和重修规则。目标不是满分，是保过线。"
        ),
        "mode": "academic_rescue",
        "steps": ["算成绩缺口", "找可补分项", "联系老师助教", "优先刷高频题", "确认补考重修规则"],
        "boundary": "不替用户作弊，不伪造成绩，不写虚假材料。",
    }
