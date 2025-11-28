import asyncio
import json
import time
import logging
from typing import List, Optional, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

# Imports from your project structure
from backend.database import init_db, get_db, AsyncSessionLocal
from backend.models import Session as DBSession, Message as DBMessage, AnalysisState as DBAnalysisState, FeedbackLog
from backend.rag_engine import rag_engine
from backend.ai_core import ai_core, create_emergency_response
from backend.analysis_engine import analysis_engine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELS ===

class RAGNuggetEdit(BaseModel):
    title: str
    content: str
    keywords: List[str]
    language: str

class GoldenStandardAdd(BaseModel):
    trigger_context: str
    golden_response: str
    category: str
    language: str = "PL"


class FeedbackSubmit(BaseModel):
    """Schema for submitting feedback from the frontend"""
    session_id: Optional[str] = None
    module_name: str  # e.g., "fast_path", "slow_path_m1_dna"
    rating: bool  # True = Like, False = Dislike
    user_input_snapshot: Optional[str] = None  # Input context (user message / session summary)
    ai_output_snapshot: Optional[str] = None   # AI output being rated
    expert_comment: Optional[str] = None       # Expert's correction
    message_id: Optional[str] = None

@app.on_event("startup")
async def on_startup():
    await init_db()
    print("[DB] OK - Database initialized")

# === ADMIN ENDPOINTS ===

@app.get("/api/admin/rag/list")
async def list_rag_nuggets():
    """List all RAG nuggets (Proxy to engine)."""
    try:
        return {"nuggets": rag_engine.nuggets if hasattr(rag_engine, 'nuggets') else [], "total": 0}
    except:
        return {"nuggets": [], "total": 0}

@app.put("/api/admin/rag/edit/{nugget_id}")
async def edit_rag_nugget(nugget_id: str, edit_data: RAGNuggetEdit):
    """Edit existing RAG nugget."""
    return {"status": "success", "message": f"Nugget {nugget_id} updated (Simulated)"}

@app.post("/api/admin/golden-standards/add")
async def add_golden_standard(standard: GoldenStandardAdd):
    """Add golden standard response."""
    return {"status": "success", "message": "Golden standard added (Simulated)"}


# === FEEDBACK LOOP (AI DOJO) ENDPOINTS ===

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackSubmit, db: AsyncSession = Depends(get_db)):
    """
    AI DOJO: Submit expert feedback on AI responses.
    Used for continuous learning and model improvement.
    """
    import uuid
    
    feedback_id = str(uuid.uuid4())
    
    new_feedback = FeedbackLog(
        id=feedback_id,
        session_id=feedback.session_id,
        module_name=feedback.module_name,
        rating=feedback.rating,
        user_input_snapshot=feedback.user_input_snapshot,
        ai_output_snapshot=feedback.ai_output_snapshot,
        expert_comment=feedback.expert_comment,
        message_id=feedback.message_id
    )
    
    db.add(new_feedback)
    await db.commit()
    
    rating_emoji = "👍" if feedback.rating else "👎"
    print(f"[DOJO] {rating_emoji} New expert feedback received for {feedback.module_name}")
    if feedback.expert_comment:
        print(f"[DOJO] Comment: {feedback.expert_comment[:100]}...")
    
    return {
        "status": "success",
        "id": feedback_id,
        "message": f"Feedback saved for {feedback.module_name}"
    }


@app.get("/api/feedback")
async def list_feedback(
    module_name: Optional[str] = None,
    rating: Optional[bool] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    AI DOJO: List feedback entries for training dashboard.
    Optionally filter by module_name or rating.
    """
    from sqlalchemy import desc
    
    query = select(FeedbackLog)
    
    if module_name:
        query = query.where(FeedbackLog.module_name == module_name)
    if rating is not None:
        query = query.where(FeedbackLog.rating == rating)
    
    query = query.order_by(desc(FeedbackLog.timestamp)).limit(limit)
    
    result = await db.execute(query)
    feedback_items = result.scalars().all()
    
    return {
        "total": len(feedback_items),
        "items": [
            {
                "id": f.id,
                "session_id": f.session_id,
                "module_name": f.module_name,
                "rating": f.rating,
                "user_input_snapshot": f.user_input_snapshot,
                "ai_output_snapshot": f.ai_output_snapshot,
                "expert_comment": f.expert_comment,
                "message_id": f.message_id,
                "timestamp": f.timestamp
            }
            for f in feedback_items
        ]
    }


@app.get("/api/feedback/stats")
async def feedback_stats(db: AsyncSession = Depends(get_db)):
    """
    AI DOJO: Get feedback statistics for the dashboard.
    """
    from sqlalchemy import func
    
    # Total counts
    total_query = select(func.count(FeedbackLog.id))
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0
    
    # Positive count
    positive_query = select(func.count(FeedbackLog.id)).where(FeedbackLog.rating == True)
    positive_result = await db.execute(positive_query)
    positive_count = positive_result.scalar() or 0
    
    # Negative count
    negative_count = total_count - positive_count
    
    # Count by module
    module_query = select(
        FeedbackLog.module_name,
        func.count(FeedbackLog.id).label('count')
    ).group_by(FeedbackLog.module_name)
    module_result = await db.execute(module_query)
    module_counts = {row.module_name: row.count for row in module_result}
    
    return {
        "total": total_count,
        "positive": positive_count,
        "negative": negative_count,
        "approval_rate": round((positive_count / total_count * 100) if total_count > 0 else 0, 1),
        "by_module": module_counts
    }

# === SESSION ENDPOINTS ===

@app.post("/api/sessions")
async def create_session(db: AsyncSession = Depends(get_db)):
    """Create new session."""
    import uuid
    session_id = f"S-{str(uuid.uuid4())[:8].upper()}"
    
    new_session = DBSession(id=session_id, created_at=int(time.time() * 1000))
    
    # Initialize empty analysis state
    initial_analysis = DBAnalysisState(
        session_id=session_id,
        data={
             "m1_dna": { "summary": "Initializing...", "mainMotivation": "Unknown", "communicationStyle": "Analytical" },
             "m2_indicators": { "purchaseTemperature": 0, "churnRisk": "Low", "funDriveRisk": "Low" },
             "m3_psychometrics": {
                "disc": { "dominance": 50, "influence": 50, "steadiness": 50, "compliance": 50 },
                "bigFive": { "openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50 },
                "schwartz": { "opennessToChange": 50, "selfEnhancement": 50, "conservation": 50, "selfTranscendence": 50 }
              },
             "m4_motivation": { "keyInsights": [], "teslaHooks": [] },
             "m5_predictions": { "scenarios": [], "estimatedTimeline": "Unknown" },
             "m6_playbook": { "suggestedTactics": [], "ssr": [] },
             "m7_decision": { "decisionMaker": "Unknown", "influencers": [], "criticalPath": "Unknown" },
             "journeyStageAnalysis": { "currentStage": "DISCOVERY", "confidence": 0, "reasoning": "Initializing..." },
             "isAnalyzing": False,
             "lastUpdated": int(time.time() * 1000)
        }
    )
    
    db.add(new_session)
    db.add(initial_analysis)
    await db.commit()
    
    return {"id": session_id}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get session with messages and analysis."""
    stmt = select(DBSession).where(DBSession.id == session_id).options(
        selectinload(DBSession.messages),
        selectinload(DBSession.analysis_state)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "createdAt": session.created_at,
        "status": session.status,
        "outcome": session.outcome,
        "journeyStage": session.journey_stage,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "confidence": m.confidence,
                "confidenceReason": m.confidence_reason,
                "clientStyle": m.client_style,
                "contextNeeds": m.context_needs,
                "suggestedActions": m.suggested_actions,
                "feedback": m.feedback,
                "feedbackDetails": m.feedback_details
            } for m in session.messages
        ],
        "analysisState": session.analysis_state.data if session.analysis_state else {}
    }

# === BACKGROUND TASKS (SLOW PATH) ===

async def run_slow_analysis_safe(websocket_manager, session_id: str, history: list, rag_context: str, journey_stage: str, language: str = "PL"):
    """
    ULTRA V3.1 LITE: Safe Guard for Slow Path (Background)
    """
    try:
        print(f"[SLOW PATH] Starting analysis for {session_id} (Language: {language})...")
        
        # 1. Run deep analysis
        analysis_result = await analysis_engine.run_deep_analysis(
            session_id=session_id,
            chat_history=history,
            language=language
        )
        
        if not analysis_result:
            print(f"[SLOW PATH] Analysis skipped or failed safely.")
            return
        
        # 2. Save to DB
        async with AsyncSessionLocal() as db:
            stmt = select(DBAnalysisState).where(DBAnalysisState.session_id == session_id)
            result = await db.execute(stmt)
            db_analysis = result.scalar_one_or_none()
            
            if db_analysis:
                current_data = db_analysis.data
                current_data.update(analysis_result)
                current_data["isAnalyzing"] = False
                current_data["lastUpdated"] = int(time.time() * 1000)
                
                db_analysis.data = dict(current_data)
                await db.commit()
                
                # 3a. AUTO-UPDATE JOURNEY STAGE if AI is confident
                if analysis_result.get('journeyStageAnalysis'):
                    stage_analysis = analysis_result['journeyStageAnalysis']
                    suggested_stage = stage_analysis.get('currentStage', '')
                    stage_confidence = stage_analysis.get('confidence', 0)
                    
                    # If AI is 75%+ confident AND stage changed
                    if stage_confidence >= 75 and suggested_stage:
                        stmt_sess = select(DBSession).where(DBSession.id == session_id)
                        res_sess = await db.execute(stmt_sess)
                        session_obj = res_sess.scalar_one_or_none()
                        
                        if session_obj and session_obj.journey_stage != suggested_stage:
                            old_stage = session_obj.journey_stage
                            session_obj.journey_stage = suggested_stage
                            await db.commit()
                            print(f"[AUTO-STAGE] {session_id}: {old_stage} -> {suggested_stage} (Confidence: {stage_confidence}%)")
                        else:
                            print(f"[AUTO-STAGE] Stage unchanged: {suggested_stage} (Confidence: {stage_confidence}%)")
                
                # 3b. Send WebSocket Update to Frontend
                print(f"[SLOW PATH] Sending update to UI: {list(current_data.keys())}")
                await websocket_manager.broadcast({
                    "type": "analysis_update",
                    "session_id": session_id,
                    "data": current_data
                })
                
                print(f"[SLOW PATH] OK - Analysis saved and broadcasted for {session_id}")

    except Exception as e:
        print(f"[SLOW PATH] ERROR - {e}")
        import traceback
        traceback.print_exc()
        
        # Notify frontend of failure
        try:
            await websocket_manager.broadcast({
                "type": "analysis_error",
                "session_id": session_id,
                "error": str(e)
            })
        except Exception as broadcast_err:
            print(f"[SLOW PATH] ERROR - Broadcast notification failed: {broadcast_err}")


# === WEBSOCKET MANAGER (IMPROVED WITH MESSAGE QUEUE) ===

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # CRITICAL FIX #3: Store task references to prevent GC
        self.active_tasks: Dict[str, asyncio.Task] = {}
        # CRITICAL FIX #6: Queue messages when no active connections
        self.pending_messages: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] OK - Client connected: {client_id} (Total: {len(self.active_connections)})")
        
        # FIX #6: Send queued messages on connect
        if client_id in self.pending_messages:
            print(f"[WS] Sending {len(self.pending_messages[client_id])} queued messages to {client_id}")
            for msg in self.pending_messages[client_id]:
                try:
                    await websocket.send_json(msg)
                except Exception as e:
                    print(f"[WS] ERROR - Failed to send queued message: {e}")
            del self.pending_messages[client_id]

    def disconnect(self, websocket: WebSocket, client_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 [WS] Client disconnected: {client_id} (Remaining: {len(self.active_connections)})")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        """
        FIX #6: Queue messages if no active connections
        """
        session_id = message.get("session_id")
        
        if not self.active_connections:
            # Queue for later delivery
            if session_id:
                if session_id not in self.pending_messages:
                    self.pending_messages[session_id] = []
                self.pending_messages[session_id].append(message)
                print(f"[WS] WARN - No active connections - queued message for {session_id} (Type: {message.get('type')})")
            return
        
        # Broadcast to all
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] ERROR - Send failed to connection: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# === WEBSOCKET ENDPOINT (WITH GC FIX) ===

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    ULTRA V3.1 LITE: Main Orchestrator
    """
    await manager.connect(websocket, session_id)
    print(f"[WS] Client connected: {session_id}")
    
    try:
        while True:
            # 1. Receive
            data = await websocket.receive_text()
            
            # Parse (handling both JSON and raw strings)
            try:
                payload = json.loads(data)
                content = payload.get("content", data)
                # Extract language from payload (default to PL for backward compatibility)
                message_language = payload.get("language", "PL")
            except:
                content = data
                message_language = "PL"
            
            print(f"[WS] Received: {content[:50]}... (Language: {message_language})")
            
            # Send "Processing" ack
            await websocket.send_json({"type": "processing", "data": {"status": "started"}})

            # 2. Get/Create Session & Save User Message
            current_stage = "DISCOVERY"
            history = []
            
            async with AsyncSessionLocal() as db:
                # Find or Create Session
                stmt = select(DBSession).where(DBSession.id == session_id).options(selectinload(DBSession.messages))
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                
                if not session:
                    session = DBSession(id=session_id, journey_stage="DISCOVERY", created_at=int(time.time()*1000))
                    db.add(session)
                    db.add(DBAnalysisState(session_id=session_id, data={"isAnalyzing": False}))
                    await db.commit()
                
                current_stage = session.journey_stage
                
                # Save User Message
                user_msg = DBMessage(
                    id=str(int(time.time()*1000)),
                    session_id=session_id,
                    role="user",
                    content=content,
                    timestamp=int(time.time() * 1000)
                )
                db.add(user_msg)
                await db.commit()
                
                # Refresh history
                await db.refresh(session, ["messages"])
                history = [{"role": m.role, "content": m.content} for m in session.messages]

            # 3. RAG Search (Context)
            rag_context_str = ""
            try:
                rag_results = await rag_engine.search_async(content, limit=3)
                if rag_results:
                    chunks = []
                    for r in rag_results:
                        chunks.append(f"[{r.get('title','Info')}]: {r.get('content','')}")
                    rag_context_str = "\n".join(chunks)
                    print(f"[RAG] Found {len(rag_results)} nuggets")
            except Exception as e:
                print(f"[RAG] Warning: {e}")

            # 4. FAST PATH (AI Core)
            try:
                fast_response = await ai_core.fast_path_secure(
                    history=history,
                    rag_context=rag_context_str,
                    stage=current_stage,
                    language=message_language
                )
                # Log if fallback was used
                if "FALLBACK" in fast_response.confidence_reason:
                    print(f"[FAST PATH] ⚠️ FALLBACK MODE: {fast_response.confidence_reason}")
            except Exception as e:
                print(f"[FAST PATH] ERROR - {e}")
                import traceback
                traceback.print_exc()
                fast_response = create_emergency_response(message_language)
                print(f"[FAST PATH] ⚠️ EMERGENCY_FALLBACK triggered due to exception")

            # 5. SAVE AI RESPONSE & MAP NEW FIELDS
            async with AsyncSessionLocal() as db:
                ai_msg = DBMessage(
                    id=str(int(time.time()*1000) + 1),
                    session_id=session_id,
                    role="ai",
                    content=fast_response.response,
                    timestamp=int(time.time() * 1000),
                    confidence=fast_response.confidence,
                    confidence_reason=fast_response.confidence_reason,
                    client_style="Analytical",
                    context_needs=fast_response.tactical_next_steps,
                    suggested_actions=fast_response.knowledge_gaps
                )
                db.add(ai_msg)
                await db.commit()

            # 6. SEND TO FRONTEND
            await websocket.send_json({
                "type": "fast_response",
                "data":  {
                    "id": ai_msg.id,
                    "role": "ai",
                    "content": ai_msg.content,
                    "timestamp": ai_msg.timestamp,
                    "confidence": ai_msg.confidence,
                    "confidenceReason": ai_msg.confidence_reason,
                    "clientStyle": ai_msg.client_style,
                    "contextNeeds": ai_msg.context_needs,
                    "suggestedActions": ai_msg.suggested_actions
                }
            })
            print(f"[FAST PATH] OK - Sent response to {session_id}")

            # 7. TRIGGER SLOW PATH (Background) - FIX #3: STORE TASK REFERENCE
            await websocket.send_json({
                "type": "analysis_status",
                "data": {"status": "analyzing", "session_id": session_id}
            })
            
            task = asyncio.create_task(
                run_slow_analysis_safe(
                    manager, 
                    session_id, 
                    history, 
                    rag_context_str, 
                    current_stage,
                    message_language
                )
            )
            
            # CRITICAL FIX #3: Store reference to prevent GC
            manager.active_tasks[session_id] = task
            print(f"[TASK] Stored reference for {session_id} (Active tasks: {len(manager.active_tasks)})")

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        print(f"🔌 Client disconnected: {session_id}")
    except Exception as e:
        print(f"[WS] CRITICAL ERROR - {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
