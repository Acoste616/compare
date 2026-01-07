import asyncio
import json
import time
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from qdrant_client.http import models

# Imports from your project structure
from backend.database import init_db, get_db, AsyncSessionLocal
from backend.models import Session as DBSession, Message as DBMessage, AnalysisState as DBAnalysisState, FeedbackLog
from backend.rag_engine import rag_engine
from backend.ai_core import ai_core, create_emergency_response
from backend.analysis_engine import analysis_engine, SystemBusyException
from backend.gotham_module import GothamIntelligence, BurningHouseInput, BurningHouseCalculator, CEPiKConnector, CEPiKData, SniperGateway
from backend.dojo_refiner import dojo_refiner

# V5.0: Import UnifiedPipeline (replaces sniper_module)
from asset_sniper.unified_platform import UnifiedPipeline, PipelineConfig, PipelineStats, ProcessingLevel
from asset_sniper.config import GOLDEN_CITY_M2_PRICES, Tier

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

class GothamScoreRequest(BaseModel):
    """Schema for GOTHAM Burning House score calculation"""
    monthly_fuel_cost: float
    current_car_value: float
    annual_tax: float = 225_000
    has_family_card: bool = False
    region: str = "ŚLĄSKIE"

class GothamMarketUpdate(BaseModel):
    """Schema for updating GOTHAM market data (Admin Panel)"""
    region: str
    total_ev_registrations: int
    growth_rate: Optional[float] = None
    top_brand: Optional[str] = None
    trend: Optional[str] = None


# === V5.0: ASYNC JOB STORAGE FOR SNIPER PIPELINE ===
# In-memory storage for job status (use Redis in production)
SNIPER_JOBS: Dict[str, Dict] = {}


class SniperJobStatus:
    """Job status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


async def process_csv_job(job_id: str, df, enable_deep: bool):
    """
    Background task to process CSV through UnifiedPipeline.

    Updates SNIPER_JOBS with progress and results.
    """
    import io
    import time

    try:
        SNIPER_JOBS[job_id]["status"] = SniperJobStatus.PROCESSING
        SNIPER_JOBS[job_id]["progress"] = 10
        logger.info(f"[SNIPER JOB {job_id}] Starting processing...")

        # Initialize UnifiedPipeline
        config = PipelineConfig(
            enable_gotham=True,
            enable_bigdecoder=enable_deep,
            bigdecoder_tier_threshold="AAA" if enable_deep else "S"
        )

        pipeline = UnifiedPipeline(
            config=config,
            analysis_engine=analysis_engine if enable_deep else None
        )

        SNIPER_JOBS[job_id]["progress"] = 20

        # Process through pipeline
        level = ProcessingLevel.LEVEL_3_BIGDECODER if enable_deep else ProcessingLevel.LEVEL_2_GOTHAM
        df_enriched, stats = await pipeline.process(df, level=level)

        SNIPER_JOBS[job_id]["progress"] = 80

        # Convert to CSV
        output = io.StringIO()
        df_enriched.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        # Store results
        SNIPER_JOBS[job_id]["status"] = SniperJobStatus.COMPLETED
        SNIPER_JOBS[job_id]["progress"] = 100
        SNIPER_JOBS[job_id]["result_csv"] = output.getvalue()
        SNIPER_JOBS[job_id]["stats"] = {
            "total_rows": stats.total_rows,
            "cleaned_rows": stats.cleaned_rows,
            "enriched_rows": stats.enriched_rows,
            "scored_rows": stats.scored_rows,
            "tier_counts": stats.tier_counts,
            "avg_wealth_score": stats.avg_wealth_score,
            "avg_total_score": stats.avg_total_score,
            "processing_time_ms": stats.processing_time_ms,
            "dna_profiles_generated": stats.dna_profiles_generated
        }
        SNIPER_JOBS[job_id]["completed_at"] = int(time.time() * 1000)

        logger.info(f"[SNIPER JOB {job_id}] ✅ Completed! {stats.scored_rows} rows processed")

    except Exception as e:
        logger.error(f"[SNIPER JOB {job_id}] ❌ Failed: {e}")
        import traceback
        traceback.print_exc()

        SNIPER_JOBS[job_id]["status"] = SniperJobStatus.FAILED
        SNIPER_JOBS[job_id]["error"] = str(e)


@app.on_event("startup")
async def on_startup():
    await init_db()
    print("[DB] OK - Database initialized")

    # Load custom GOTHAM market data (if available)
    CEPiKConnector.load_custom_data()
    print("[GOTHAM] OK - Market data loaded")

    # Initialize fuel price scraper (preload with fresh data)
    try:
        from backend.services.gotham.scraper import FuelPriceScraper
        prices = FuelPriceScraper.get_prices_with_cache(force_refresh=False)
        print(f"[GOTHAM] Fuel Prices Loaded: Pb95={prices.get('Pb95', 6.05)} PLN, ON={prices.get('ON', 6.15)} PLN, LPG={prices.get('LPG', 2.85)} PLN")
    except Exception as e:
        print(f"[GOTHAM] WARNING - Fuel scraper initialization failed: {e}")

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
    """
    Edit existing RAG nugget in Qdrant.

    Steps:
    1. Find point in Qdrant by ID
    2. Update payload with new content
    3. Optionally recalculate embedding if content changed
    """
    try:
        if not rag_engine.client or not rag_engine.model:
            raise HTTPException(status_code=503, detail="RAG engine not available")

        # 1. Search for the point by source_id in payload
        scroll_result = rag_engine.client.scroll(
            collection_name=rag_engine.collection,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id",
                        match=models.MatchValue(value=nugget_id)
                    )
                ]
            ),
            limit=1
        )

        points, _ = scroll_result

        if not points:
            raise HTTPException(status_code=404, detail=f"Nugget {nugget_id} not found in Qdrant")

        point = points[0]
        point_uuid = point.id

        # 2. Prepare new payload (preserve original structure)
        new_payload = {
            'source': 'rag_nuggets',
            'source_id': nugget_id,
            'title': edit_data.title,
            'content': edit_data.content,
            'keywords': ' '.join(edit_data.keywords) if isinstance(edit_data.keywords, list) else edit_data.keywords,
            'language': edit_data.language,
            'type': point.payload.get('type', 'general'),
            'tags': point.payload.get('tags', []),
            'archetype_filter': point.payload.get('archetype_filter', [])
        }

        # 3. Recalculate embedding (content changed) - ASYNC to avoid blocking event loop
        text_to_embed = f"{edit_data.title} {edit_data.content} {new_payload['keywords']}"
        loop = asyncio.get_event_loop()
        new_embedding = await loop.run_in_executor(None, rag_engine._get_embedding, text_to_embed)

        # 4. Update point in Qdrant
        rag_engine.client.upsert(
            collection_name=rag_engine.collection,
            points=[
                models.PointStruct(
                    id=point_uuid,
                    vector=new_embedding,
                    payload=new_payload
                )
            ]
        )

        logger.info(f"[ADMIN] Nugget {nugget_id} updated successfully in Qdrant (UUID: {point_uuid})")

        return {
            "status": "success",
            "message": f"Nugget {nugget_id} updated successfully",
            "data": {
                "id": nugget_id,
                "uuid": str(point_uuid),
                "title": edit_data.title,
                "embedding_recalculated": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] ERROR updating nugget {nugget_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update nugget: {str(e)}")

@app.post("/api/admin/golden-standards/add")
async def add_golden_standard(standard: GoldenStandardAdd):
    """
    Add golden standard response to both JSON file and Qdrant.

    Steps:
    1. Load existing golden_standards_final.json
    2. Add new standard with unique ID
    3. Save back to JSON file
    4. Add to Qdrant for semantic search
    """
    try:
        import uuid as uuid_lib
        from pathlib import Path

        # 1. Load existing standards from JSON
        json_path = Path(__file__).parent.parent / "dane" / "golden_standards_final.json"

        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                standards = json.load(f)
        else:
            standards = []

        # 2. Create new standard with unique ID
        new_id = f"GS-{str(uuid_lib.uuid4())[:8].upper()}"
        new_standard = {
            "id": new_id,
            "trigger_context": standard.trigger_context,
            "golden_response": standard.golden_response,
            "category": standard.category,
            "language": standard.language,
            "tags": [],
            "created_at": int(time.time() * 1000)
        }

        # 3. Add to list and save to JSON
        standards.append(new_standard)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(standards, f, ensure_ascii=False, indent=2)

        logger.info(f"[ADMIN] Golden standard {new_id} saved to JSON ({len(standards)} total)")

        # 4. Add to Qdrant (if available)
        if rag_engine.client and rag_engine.model:
            try:
                # Combine trigger + response for embedding
                text_to_embed = f"{standard.trigger_context} {standard.golden_response}"
                embedding = rag_engine._get_embedding(text_to_embed)

                # Prepare payload
                payload = {
                    'source': 'golden_standards',
                    'source_id': new_id,
                    'trigger_context': standard.trigger_context,
                    'golden_response': standard.golden_response,
                    'tags': [],
                    'category': standard.category,
                    'language': standard.language
                }

                # Generate UUID for Qdrant point
                point_uuid = str(uuid_lib.uuid4())

                # Insert to Qdrant
                rag_engine.client.upsert(
                    collection_name=rag_engine.collection,
                    points=[
                        models.PointStruct(
                            id=point_uuid,
                            vector=embedding,
                            payload=payload
                        )
                    ]
                )

                logger.info(f"[ADMIN] Golden standard {new_id} added to Qdrant (UUID: {point_uuid})")

                return {
                    "status": "success",
                    "message": f"Golden standard {new_id} added successfully",
                    "data": {
                        "id": new_id,
                        "uuid": point_uuid,
                        "saved_to_json": True,
                        "saved_to_qdrant": True,
                        "total_standards": len(standards)
                    }
                }

            except Exception as qdrant_error:
                logger.warning(f"[ADMIN] Qdrant insert failed for {new_id}: {qdrant_error}")
                # Still return success since JSON save succeeded
                return {
                    "status": "success",
                    "message": f"Golden standard {new_id} added to JSON (Qdrant failed)",
                    "data": {
                        "id": new_id,
                        "saved_to_json": True,
                        "saved_to_qdrant": False,
                        "total_standards": len(standards),
                        "warning": str(qdrant_error)
                    }
                }
        else:
            # RAG engine not available - JSON only
            return {
                "status": "success",
                "message": f"Golden standard {new_id} added to JSON (Qdrant not available)",
                "data": {
                    "id": new_id,
                    "saved_to_json": True,
                    "saved_to_qdrant": False,
                    "total_standards": len(standards)
                }
            }

    except Exception as e:
        logger.error(f"[ADMIN] ERROR adding golden standard: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to add golden standard: {str(e)}")


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


# === GOTHAM ENDPOINTS (NEW in v4.0) ===

@app.post("/api/gotham/score")
async def calculate_gotham_score(request: GothamScoreRequest):
    """
    GOTHAM: Calculate Burning House Score

    Returns financial urgency analysis for switching to Tesla.
    """
    try:
        full_context = GothamIntelligence.get_full_context(
            monthly_fuel_cost=request.monthly_fuel_cost,
            current_car_value=request.current_car_value,
            annual_tax=request.annual_tax,
            has_family_card=request.has_family_card,
            region=request.region
        )

        print(f"[GOTHAM] Score calculated - Urgency: {full_context['urgency_level']}")

        return {
            "status": "success",
            "data": full_context
        }

    except Exception as e:
        print(f"[GOTHAM] ERROR - {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"GOTHAM calculation failed: {str(e)}")


@app.get("/api/gotham/market/{region}")
async def get_market_data(region: str):
    """
    GOTHAM: Get CEPiK market data for a region

    Returns regional EV registration statistics.
    """
    try:
        from backend.gotham_module import CEPiKConnector

        data = CEPiKConnector.get_regional_data(region)
        context = CEPiKConnector.get_market_context(region)

        if not data:
            raise HTTPException(status_code=404, detail=f"No data for region: {region}")

        return {
            "status": "success",
            "data": data.dict(),
            "context": context
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[GOTHAM] ERROR - {e}")
        raise HTTPException(status_code=500, detail=f"Market data fetch failed: {str(e)}")


@app.put("/api/admin/gotham/market")
async def update_market_data(update: GothamMarketUpdate):
    """
    ADMIN: Update GOTHAM market data for a region

    Allows manual updates when real CEPiK API is unavailable.
    Data is saved to JSON and persists across restarts.
    """
    try:
        updated_data = CEPiKConnector.update_market_data(
            region=update.region,
            total_ev_registrations=update.total_ev_registrations,
            growth_rate=update.growth_rate,
            top_brand=update.top_brand,
            trend=update.trend
        )

        logger.info(f"[ADMIN] Market data updated for {update.region}: {update.total_ev_registrations} EVs")

        return {
            "status": "success",
            "message": f"Market data for {update.region} updated successfully",
            "data": updated_data.dict()
        }

    except Exception as e:
        logger.error(f"[ADMIN] ERROR updating market data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update market data: {str(e)}")


@app.post("/api/admin/dojo/run-refine")
async def run_dojo_refinement():
    """
    ADMIN: Run DOJO-REFINER - AI Auto-Improvement Engine

    V4.0 FEATURE: Analyzes negative expert feedback and generates improvement suggestions.

    Workflow:
    1. Scans FeedbackLog for unprocessed negative feedback (rating=False, processed=False)
    2. Groups by module_name (fast_path, slow_path_m1_dna, etc.)
    3. For modules with 3+ negative feedback, uses AI to generate fixes
    4. Saves suggestions to dane/suggested_fixes.json (Human-in-the-Loop)
    5. Marks feedback as processed

    Returns:
        {
            "processed_modules": ["fast_path", "slow_path_m1_dna"],
            "total_feedback_processed": 12,
            "fixes_generated": 2,
            "suggestions_saved_to": "dane/suggested_fixes.json",
            "timestamp": 1234567890
        }
    """
    try:
        logger.info("[ADMIN] 🧠 DOJO-REFINER requested by admin")

        # Run refinement
        result = await dojo_refiner.scan_and_refine()

        logger.info(f"[ADMIN] ✅ DOJO-REFINER completed: {result['fixes_generated']} fix(es) generated")

        return {
            "status": "success",
            "message": "DOJO-REFINER completed successfully",
            **result
        }

    except Exception as e:
        logger.error(f"[ADMIN] ❌ DOJO-REFINER ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"DOJO-REFINER failed: {str(e)}")


@app.get("/api/v1/gotham/market-overview")
async def get_market_overview(region: str = "ŚLĄSKIE"):
    """
    GOTHAM: Market Overview - Lead Sniper Data

    Returns real-time data about expiring leases (potential leads) from CEPiK API.
    This powers the "Lead Sniper" widget on the dashboard.

    Args:
        region: Voivodeship name (default: ŚLĄSKIE)

    Returns:
        {
            "total_expiring_leases": 824,
            "competitor_breakdown": {"BMW": 245, "MERCEDES-BENZ": 312, ...},
            "opportunity_score": 85,
            "urgency_level": "HIGH",
            "insight": "824 premium car leases expiring - strong sales opportunity",
            "region": "ŚLĄSKIE",
            "last_updated": "2026-01-04T10:30:00"
        }
    """
    try:
        from datetime import datetime

        print(f"[GOTHAM] 🎯 Fetching market overview for {region}...")

        # Get opportunity score (includes leasing expiry data)
        opportunity_data = CEPiKConnector.get_opportunity_score(region=region)

        # Add metadata
        opportunity_data["region"] = region
        opportunity_data["last_updated"] = datetime.now().isoformat()

        print(f"[GOTHAM] Market Overview: {opportunity_data['total_expiring_leases']} expiring leases, Score: {opportunity_data['opportunity_score']}")

        return opportunity_data

    except Exception as e:
        logger.error(f"[GOTHAM] ERROR fetching market overview: {e}")
        import traceback
        traceback.print_exc()

        # Return safe fallback data
        from datetime import datetime
        return {
            "total_expiring_leases": 0,
            "competitor_breakdown": {},
            "opportunity_score": 0,
            "urgency_level": "UNKNOWN",
            "insight": "Data temporarily unavailable",
            "region": region,
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        }


# === ASSET SNIPER v5.0 ENDPOINTS (UnifiedPipeline + Async Jobs) ===

@app.post("/api/sniper/upload")
async def sniper_upload_csv(
    file: UploadFile = File(...),
    enable_deep_enrichment: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    ASSET SNIPER v5.0: Upload CSV and start async processing job.

    Returns job_id immediately - use /api/sniper/status/{id} to check progress.

    Pipeline:
    - UnifiedPipeline with Golden City Set M² pricing
    - BigDecoder Full Bridge integration
    - GOTHAM Engine (wealth, tax, chargers)
    - Scoring Matrix (Tier S-E classification)

    Args:
        file: CSV file with CEIDG leads
        enable_deep_enrichment: Whether to run BigDecoder AI profiling

    Returns:
        {"job_id": "...", "status": "pending", "message": "..."}
    """
    import io

    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="pandas is not installed. Run: pip install pandas"
        )

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV file."
        )

    logger.info(f"[SNIPER v5.0] 📥 Received file: {file.filename}")
    logger.info(f"[SNIPER v5.0] Deep enrichment: {enable_deep_enrichment}")

    # Read CSV content
    content = await file.read()

    # Try different encodings
    df = None
    for encoding in ['utf-8', 'cp1250', 'iso-8859-2', 'latin1']:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding, sep=None, engine='python')
            logger.info(f"[SNIPER] Successfully parsed CSV with encoding: {encoding}")
            break
        except Exception:
            continue

    if df is None:
        raise HTTPException(
            status_code=400,
            detail="Could not parse CSV file. Please check the file format and encoding."
        )

    logger.info(f"[SNIPER] Loaded {len(df)} rows, {len(df.columns)} columns")

    # Generate job_id
    job_id = f"JOB-{str(uuid.uuid4())[:8].upper()}"

    # Initialize job status
    SNIPER_JOBS[job_id] = {
        "status": SniperJobStatus.PENDING,
        "progress": 0,
        "filename": file.filename,
        "total_rows": len(df),
        "enable_deep": enable_deep_enrichment,
        "created_at": int(time.time() * 1000),
        "result_csv": None,
        "stats": None,
        "error": None
    }

    # Start background processing
    if background_tasks:
        background_tasks.add_task(process_csv_job, job_id, df, enable_deep_enrichment)
    else:
        # Fallback: create asyncio task
        asyncio.create_task(process_csv_job(job_id, df, enable_deep_enrichment))

    logger.info(f"[SNIPER v5.0] Created job {job_id} for {len(df)} rows")

    return {
        "job_id": job_id,
        "status": SniperJobStatus.PENDING,
        "message": f"Job created. Processing {len(df)} rows with {'deep' if enable_deep_enrichment else 'local'} enrichment.",
        "total_rows": len(df)
    }


@app.get("/api/sniper/status/{job_id}")
async def sniper_job_status(job_id: str):
    """
    ASSET SNIPER v5.0: Check job processing status.

    Args:
        job_id: Job ID returned from /api/sniper/upload

    Returns:
        {
            "job_id": "JOB-XXXX",
            "status": "processing|completed|failed",
            "progress": 0-100,
            "stats": {...} (if completed)
        }
    """
    if job_id not in SNIPER_JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = SNIPER_JOBS[job_id]

    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "filename": job.get("filename"),
        "total_rows": job.get("total_rows"),
        "enable_deep": job.get("enable_deep"),
        "created_at": job.get("created_at")
    }

    if job["status"] == SniperJobStatus.COMPLETED:
        response["stats"] = job.get("stats")
        response["completed_at"] = job.get("completed_at")

    if job["status"] == SniperJobStatus.FAILED:
        response["error"] = job.get("error")

    return response


@app.get("/api/sniper/download/{job_id}")
async def sniper_download_result(job_id: str):
    """
    ASSET SNIPER v5.0: Download enriched CSV result.

    Args:
        job_id: Job ID returned from /api/sniper/upload

    Returns:
        Streaming CSV response with enriched data
    """
    import io
    from datetime import datetime

    if job_id not in SNIPER_JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = SNIPER_JOBS[job_id]

    if job["status"] != SniperJobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not completed. Status: {job['status']}"
        )

    if not job.get("result_csv"):
        raise HTTPException(status_code=500, detail="Result CSV not available")

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    enrichment_suffix = "_deep" if job.get("enable_deep") else "_local"
    output_filename = f"sniper_enriched{enrichment_suffix}_{timestamp}.csv"

    # Return streaming response
    return StreamingResponse(
        io.BytesIO(job["result_csv"].encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={output_filename}",
            "X-Sniper-Stats": json.dumps(job.get("stats", {}))
        }
    )


@app.post("/api/sniper/analyze")
async def sniper_analyze_csv(
    file: UploadFile = File(...),
    include_intelligence: bool = False
):
    """
    ASSET SNIPER v5.0: Quick CSV analysis (preview before full processing).

    Uses UnifiedPipeline Level 2 (GOTHAM) for fast results.

    Args:
        file: CSV file with CEIDG leads
        include_intelligence: Include Golden City Set pricing data

    Returns:
        Statistics and sample Tier S leads
    """
    import io

    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(status_code=500, detail="pandas not installed")

    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Invalid file type")

        content = await file.read()

        # Parse CSV
        df = None
        for encoding in ['utf-8', 'cp1250', 'iso-8859-2', 'latin1']:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding, sep=None, engine='python')
                break
            except Exception:
                continue

        if df is None:
            raise HTTPException(status_code=400, detail="Could not parse CSV")

        # Process with UnifiedPipeline (Level 2 GOTHAM - fast)
        pipeline = UnifiedPipeline()
        df_enriched, stats = pipeline.process_sync(df, level=ProcessingLevel.LEVEL_2_GOTHAM)

        # Get sample Tier S leads
        tier_s_df = df_enriched[df_enriched['target_tier'] == Tier.S.value].head(5) if 'target_tier' in df_enriched.columns else pd.DataFrame()

        # Find relevant columns
        name_col = None
        city_col = None

        for col in df_enriched.columns:
            col_lower = col.lower()
            if 'name' in col_lower or 'nazwa' in col_lower:
                name_col = col
            if 'city' in col_lower or 'miasto' in col_lower or 'miejscow' in col_lower:
                city_col = col

        sample_leads = []
        for _, row in tier_s_df.iterrows():
            company = str(row.get(name_col, "Unknown")) if name_col else "Unknown"
            city = str(row.get(city_col, "")) if city_col else ""

            lead_data = {
                "company": company,
                "total_score": int(row.get('total_score', 0)),
                "target_tier": str(row.get('target_tier', 'E')),
                "wealth_score": int(row.get('wealth_score', 5)),
                "priority": str(row.get('priority', 'ARCHIWUM')),
                "next_action": str(row.get('next_action', ''))
            }

            # Add Golden City Set pricing if requested
            if include_intelligence and city:
                lead_data["m2_price_golden"] = GOLDEN_CITY_M2_PRICES.get(city.strip().title(), 11_500)

            sample_leads.append(lead_data)

        return {
            "status": "success",
            "filename": file.filename,
            "total_rows": stats.total_rows,
            "cleaned_rows": stats.cleaned_rows,
            "scored_rows": stats.scored_rows,
            "tier_distribution": stats.tier_counts,
            "top_industries": stats.top_pkd_industries,
            "top_cities": stats.top_cities,
            "avg_wealth_score": round(stats.avg_wealth_score, 1),
            "avg_total_score": round(stats.avg_total_score, 1),
            "processing_time_ms": stats.processing_time_ms,
            "sample_tier_s": sample_leads,
            "intelligence_included": include_intelligence
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SNIPER] ERROR analyzing CSV: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sniper/charger-check/{city}")
async def sniper_charger_check(city: str):
    """
    ASSET SNIPER: Check charger infrastructure for a city
    
    Returns charging infrastructure data for EV sales pitch.
    """
    try:
        data = SniperGateway.check_charger_infrastructure(city=city)
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"[SNIPER] ERROR checking chargers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sniper/tax-potential")
async def sniper_tax_potential(
    pkd_code: str = None,
    legal_form: str = None,
    estimated_annual_km: int = 25000
):
    """
    ASSET SNIPER: Calculate tax savings potential for a lead
    
    Returns detailed tax benefit analysis for EV switch.
    """
    try:
        data = SniperGateway.calculate_tax_potential(
            pkd_code=pkd_code,
            legal_form=legal_form,
            estimated_annual_km=estimated_annual_km
        )
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"[SNIPER] ERROR calculating tax: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    ULTRA V4.0: Safe Guard for Slow Path (Background) with Queue Management

    V4.0 FIX: Handles SystemBusyException and notifies user via WebSocket
    """
    try:
        print(f"[SLOW PATH] Starting analysis for {session_id} (Language: {language})...")

        # 1. Run deep analysis (with queue-based concurrency control)
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

    except SystemBusyException as busy_err:
        # V4.0 FIX: Handle queue timeout - notify user instead of silent failure
        print(f"[SLOW PATH] SYSTEM BUSY - {busy_err.message}")
        try:
            await websocket_manager.broadcast({
                "type": "system_busy",
                "session_id": session_id,
                "message": busy_err.message,
                "code": "ANALYSIS_QUEUE_FULL",
                "retry_after": int(busy_err.timeout)
            })
        except Exception as broadcast_err:
            print(f"[SLOW PATH] ERROR - Failed to notify user of system busy: {broadcast_err}")

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

            # 3.5. GOTHAM Intelligence (NEW in v4.0) - LIVE Smart Detection
            gotham_context = None

            # EXPANDED keyword detection (PL + EN)
            financial_keywords = [
                # Polish
                "paliwo", "benzyna", "diesel", "lpg", "olej", "tankowanie",
                "oszczędności", "oszczędzić", "taniej", "drożej",
                "koszt", "koszty", "wydatek", "wydatki", "płacę", "płaci",
                "podatek", "opłata", "rata", "leasing",
                "spalanie", "pali", "zużycie", "zużywa",
                "tco", "całkowity koszt", "utrzymanie",
                # English
                "fuel", "gas", "petrol", "gasoline", "diesel", "lpg",
                "savings", "save", "cheaper", "expensive",
                "cost", "costs", "expense", "expenses", "paying", "payment",
                "tax", "fee", "lease", "leasing",
                "consumption", "burns", "mpg",
                "tco", "total cost", "maintenance"
            ]

            # Check if conversation contains financial keywords (last 5 messages)
            recent_messages = " ".join([msg['content'].lower() for msg in history[-5:]])
            intent_detected = any(keyword in recent_messages for keyword in financial_keywords)

            if intent_detected:
                try:
                    print(f"[GOTHAM] 🔥 Financial intent detected! Triggering Burning House calculation...")

                    # Generate GOTHAM context with live fuel prices
                    # TODO: In production, extract these values from session metadata or client profile
                    gotham_context = GothamIntelligence.get_full_context(
                        monthly_fuel_cost=1200,  # Default: 1,200 PLN/month
                        current_car_value=80_000,  # Default: 80k PLN
                        annual_tax=225_000,  # Default: high emission tax (alternative: 0)
                        has_family_card=False,  # Default: no family card
                        region="ŚLĄSKIE"  # Default: Śląskie region
                    )
                    print(f"[GOTHAM] Context generated - Urgency: {gotham_context['urgency_level']}")
                    print(f"[GOTHAM] Annual savings: {gotham_context['burning_house_score']['annual_savings']:,.0f} PLN")

                    # BROADCAST to Frontend immediately (before AI response)
                    # This triggers the red "Burning House" alert on Dashboard
                    await websocket.send_json({
                        "type": "gotham_update",
                        "data": gotham_context
                    })
                    print(f"[GOTHAM] ✅ Broadcasted to Frontend - Widget should appear NOW!")

                except Exception as e:
                    print(f"[GOTHAM] WARNING - Calculation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    gotham_context = None

            # 4. FAST PATH (AI Core)
            try:
                fast_response = await ai_core.fast_path_secure(
                    history=history,
                    rag_context=rag_context_str,
                    stage=current_stage,
                    language=message_language,
                    gotham_context=gotham_context
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
