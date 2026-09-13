from typing import List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models import CVProfile, JobItem
from app.services.autonomous_agent import AutonomousAgent

router = APIRouter(prefix="/agent", tags=["Autonomous Agent"])

class AgentBatchRequest(BaseModel):
    profile: CVProfile
    jobs: List[JobItem]

@router.post("/stream-apply")
async def start_autonomous_batch_stream(payload: AgentBatchRequest):
    agent = AutonomousAgent(profile=payload.profile, jobs=payload.jobs)
    return StreamingResponse(
        agent.run_batch_with_logs(),
        media_type="text/event-stream"
    )