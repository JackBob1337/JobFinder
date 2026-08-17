from app.graphs.state import TailorState
from app.agents.tailor_agent import TailorAgent
from app.agents.ats_check_agent import ATSCheckAgent
from app.schemas.ats_check_result import ATSCheckResult

async def generate_summary_node(state: TailorState, tailor_agent: TailorAgent) -> TailorState:
    feedback = ''
    ats_result = state.get('ats_result')
    if ats_result is not None:
        feedback = build_feedback_text(ats_result)

    new_summary = await tailor_agent.tailor_summary(
        job_title=state['job_title'],
        analysis=state['analysis'],
        match_reasoning=state['match_reasoning'],
        extra_feedback=feedback,        
    )
    return {**state, 'current_summary': new_summary}

async def ats_check_node(state: TailorState, ats_agent: ATSCheckAgent) -> TailorState:
    result = await ats_agent.check(
        summary=state['current_summary'],
        analysis=state['analysis']
    )

def build_feedback_text(ats_result: ATSCheckResult) -> str:
    return f"""
        Previous attempt scored {ats_result.score}/100.
        Issues: {', '.join(ats_result.issues)}
        Missing keywords: {', '.join(ats_result.missing_keywords)}
        Recommendations: {', '.join(ats_result.recommendations)}
    """