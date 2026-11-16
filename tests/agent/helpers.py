from exam_baseline.agent.models import ScreenContext, TurnRequest


def request(message, request_id="r1", context=None, conversation="c1", workspace="w1"):
    return TurnRequest(
        request_id=request_id,
        conversation_id=conversation,
        workspace_session_id=workspace,
        message=message,
        screen_context=context
        or ScreenContext(screen_id="workspace", state_version=1, workspace_session_id=workspace),
    )
