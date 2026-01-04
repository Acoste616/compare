"""
DOJO-REFINER Module (ULTRA v4.0)
Automatic AI Improvement Engine based on Expert Feedback

CONCEPT:
- Analyzes negative feedback from FeedbackLog
- Groups by module (fast_path, slow_path_m1_dna, etc.)
- Uses AI (Gemini) to generate improvement suggestions
- Saves to suggested_fixes.json (Human-in-the-Loop)

WORKFLOW:
1. scan_and_refine() - Scans DB for unprocessed negative feedback
2. generate_fix() - Uses AI to create improvement suggestions
3. apply_fix() - Saves suggestions to JSON for human review
4. mark_as_processed() - Updates feedback records

Author: Senior Python Developer
Version: 1.0.0
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

import google.generativeai as genai
from dotenv import load_dotenv

from backend.models import FeedbackLog
from backend.database import AsyncSessionLocal

load_dotenv()

# === CONFIGURATION ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SUGGESTED_FIXES_PATH = Path(__file__).parent.parent / "dane" / "suggested_fixes.json"
MIN_FEEDBACK_THRESHOLD = 3  # Minimum negative feedback to trigger refinement


class DojoRefiner:
    """
    DOJO-REFINER: Automatic AI Improvement Engine

    Analyzes expert feedback to generate system improvements.
    Uses Human-in-the-Loop approach for safety.
    """

    def __init__(self):
        """Initialize DojoRefiner with AI configuration"""
        self.model_name = "models/gemini-2.0-flash-exp"
        print(f"[DOJO-REFINER] Initialized with model: {self.model_name}")

    async def scan_and_refine(self) -> Dict[str, Any]:
        """
        Main refinement workflow

        Steps:
        1. Query DB for unprocessed negative feedback
        2. Group by module_name
        3. For modules with 3+ negative feedback, generate fixes
        4. Save suggestions to JSON
        5. Mark feedback as processed

        Returns:
            Dict with refinement results:
            {
                "processed_modules": ["fast_path", "slow_path_m1_dna"],
                "total_feedback_processed": 12,
                "fixes_generated": 2,
                "suggestions_saved_to": "dane/suggested_fixes.json"
            }
        """
        print("[DOJO-REFINER] 🔍 Starting refinement scan...")

        async with AsyncSessionLocal() as db:
            # Step 1: Query unprocessed negative feedback
            feedback_records = await self._fetch_unprocessed_negative_feedback(db)

            if not feedback_records:
                print("[DOJO-REFINER] ✅ No unprocessed negative feedback found")
                return {
                    "processed_modules": [],
                    "total_feedback_processed": 0,
                    "fixes_generated": 0,
                    "message": "No negative feedback to process"
                }

            print(f"[DOJO-REFINER] Found {len(feedback_records)} unprocessed negative feedback records")

            # Step 2: Group by module_name
            grouped_feedback = self._group_feedback_by_module(feedback_records)

            print(f"[DOJO-REFINER] Grouped into {len(grouped_feedback)} modules:")
            for module, records in grouped_feedback.items():
                print(f"  - {module}: {len(records)} feedback(s)")

            # Step 3: Generate fixes for modules with sufficient feedback
            fixes_generated = 0
            processed_modules = []
            all_suggestions = []

            for module_name, feedback_list in grouped_feedback.items():
                if len(feedback_list) < MIN_FEEDBACK_THRESHOLD:
                    print(f"[DOJO-REFINER] ⏭️  Skipping {module_name}: Only {len(feedback_list)} feedback(s) (need {MIN_FEEDBACK_THRESHOLD}+)")
                    continue

                print(f"[DOJO-REFINER] 🧠 Generating fix for {module_name} ({len(feedback_list)} feedback(s))...")

                # Generate fix using AI
                suggestion = await self.generate_fix(module_name, feedback_list)

                if suggestion:
                    all_suggestions.append(suggestion)
                    fixes_generated += 1
                    processed_modules.append(module_name)
                    print(f"[DOJO-REFINER] ✅ Fix generated for {module_name}")

            # Step 4: Save suggestions to JSON
            if all_suggestions:
                saved_path = await self.apply_fix(all_suggestions)
                print(f"[DOJO-REFINER] 💾 Suggestions saved to: {saved_path}")
            else:
                saved_path = None
                print(f"[DOJO-REFINER] ⚠️  No fixes generated (insufficient feedback thresholds)")

            # Step 5: Mark all processed feedback
            feedback_ids = [f.id for f in feedback_records]
            await self._mark_as_processed(db, feedback_ids)

            print(f"[DOJO-REFINER] ✅ Marked {len(feedback_ids)} feedback records as processed")

            return {
                "processed_modules": processed_modules,
                "total_feedback_processed": len(feedback_records),
                "fixes_generated": fixes_generated,
                "suggestions_saved_to": str(saved_path) if saved_path else None,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

    async def generate_fix(self, module_name: str, feedback_list: List[FeedbackLog]) -> Optional[Dict[str, Any]]:
        """
        Generate improvement suggestion using AI

        Args:
            module_name: Module to improve (e.g., "fast_path")
            feedback_list: List of negative feedback for this module

        Returns:
            Dict with suggestion or None if AI fails
            {
                "module": "fast_path",
                "feedback_count": 5,
                "suggested_improvement": "...",
                "rationale": "...",
                "priority": "HIGH",
                "timestamp": 1234567890
            }
        """
        try:
            # Build improvement prompt
            prompt = self._build_improvement_prompt(module_name, feedback_list)

            print(f"[DOJO-REFINER] 📤 Sending prompt to Gemini ({len(prompt)} chars)...")

            # Call Gemini API
            model = genai.GenerativeModel(self.model_name)

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    model.generate_content,
                    prompt
                ),
                timeout=30.0
            )

            raw_text = response.text.strip()

            print(f"[DOJO-REFINER] 📥 Received response ({len(raw_text)} chars)")

            # Parse JSON response
            try:
                # Try to extract JSON from markdown code blocks
                if "```json" in raw_text:
                    json_start = raw_text.find("```json") + 7
                    json_end = raw_text.find("```", json_start)
                    json_text = raw_text[json_start:json_end].strip()
                elif "```" in raw_text:
                    json_start = raw_text.find("```") + 3
                    json_end = raw_text.find("```", json_start)
                    json_text = raw_text[json_start:json_end].strip()
                else:
                    json_text = raw_text

                suggestion_data = json.loads(json_text)

                # Add metadata
                suggestion = {
                    "module": module_name,
                    "feedback_count": len(feedback_list),
                    "suggested_improvement": suggestion_data.get("suggested_improvement", ""),
                    "rationale": suggestion_data.get("rationale", ""),
                    "priority": suggestion_data.get("priority", "MEDIUM"),
                    "implementation_type": suggestion_data.get("implementation_type", "prompt_refinement"),
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "feedback_samples": [
                        {
                            "user_input": f.user_input_snapshot[:200] if f.user_input_snapshot else "",
                            "ai_output": f.ai_output_snapshot[:200] if f.ai_output_snapshot else "",
                            "expert_comment": f.expert_comment[:300] if f.expert_comment else ""
                        }
                        for f in feedback_list[:3]  # Include max 3 samples
                    ]
                }

                print(f"[DOJO-REFINER] ✅ Parsed AI suggestion: Priority={suggestion['priority']}, Type={suggestion['implementation_type']}")

                return suggestion

            except json.JSONDecodeError as e:
                print(f"[DOJO-REFINER] ❌ JSON parsing error: {e}")
                print(f"[DOJO-REFINER] Raw response: {raw_text[:500]}...")
                return None

        except asyncio.TimeoutError:
            print(f"[DOJO-REFINER] ⏱️  Timeout generating fix for {module_name}")
            return None

        except Exception as e:
            print(f"[DOJO-REFINER] ❌ Error generating fix for {module_name}: {e}")
            return None

    async def apply_fix(self, suggestions: List[Dict[str, Any]]) -> Path:
        """
        Save suggestions to JSON file (Human-in-the-Loop)

        Args:
            suggestions: List of improvement suggestions

        Returns:
            Path to saved file
        """
        # Ensure directory exists
        SUGGESTED_FIXES_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load existing suggestions
        existing_suggestions = []
        if SUGGESTED_FIXES_PATH.exists():
            try:
                with open(SUGGESTED_FIXES_PATH, 'r', encoding='utf-8') as f:
                    existing_suggestions = json.load(f)
            except Exception as e:
                print(f"[DOJO-REFINER] ⚠️  Could not load existing suggestions: {e}")

        # Append new suggestions
        all_suggestions = existing_suggestions + suggestions

        # Save to file
        with open(SUGGESTED_FIXES_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_suggestions, f, ensure_ascii=False, indent=2)

        print(f"[DOJO-REFINER] 💾 Saved {len(suggestions)} new suggestion(s) to {SUGGESTED_FIXES_PATH}")
        print(f"[DOJO-REFINER]    Total suggestions in file: {len(all_suggestions)}")

        return SUGGESTED_FIXES_PATH

    # === HELPER METHODS ===

    async def _fetch_unprocessed_negative_feedback(self, db: AsyncSession) -> List[FeedbackLog]:
        """
        Fetch unprocessed negative feedback from database

        Criteria:
        - rating = False (negative)
        - processed = False (not yet processed)
        - expert_comment IS NOT NULL (has correction)
        """
        stmt = select(FeedbackLog).where(
            and_(
                FeedbackLog.rating == False,
                FeedbackLog.processed == False,
                FeedbackLog.expert_comment.isnot(None)
            )
        ).order_by(FeedbackLog.timestamp.desc())

        result = await db.execute(stmt)
        feedback_records = result.scalars().all()

        return list(feedback_records)

    def _group_feedback_by_module(self, feedback_list: List[FeedbackLog]) -> Dict[str, List[FeedbackLog]]:
        """
        Group feedback by module_name

        Returns:
            Dict mapping module_name -> list of feedback
        """
        grouped = defaultdict(list)

        for feedback in feedback_list:
            grouped[feedback.module_name].append(feedback)

        return dict(grouped)

    def _build_improvement_prompt(self, module_name: str, feedback_list: List[FeedbackLog]) -> str:
        """
        Build AI prompt for generating improvements

        Args:
            module_name: Module being improved
            feedback_list: List of negative feedback

        Returns:
            Formatted prompt for Gemini
        """
        # Extract feedback samples
        feedback_samples = []
        for i, feedback in enumerate(feedback_list[:5], 1):  # Max 5 samples
            sample = f"""
FEEDBACK #{i}:
User Input: {feedback.user_input_snapshot[:300] if feedback.user_input_snapshot else 'N/A'}
AI Output: {feedback.ai_output_snapshot[:300] if feedback.ai_output_snapshot else 'N/A'}
Expert Correction: {feedback.expert_comment[:500] if feedback.expert_comment else 'N/A'}
---
            """.strip()
            feedback_samples.append(sample)

        feedback_text = "\n\n".join(feedback_samples)

        prompt = f"""
You are an AI System Improvement Expert for ULTRA v4.0 (Tesla Sales Bot).

TASK: Analyze negative feedback for the "{module_name}" module and suggest improvements.

MODULE CONTEXT:
- fast_path: Quick AI responses (Gemini 2.0) with tactical next steps
- slow_path_m1_dna: Deep client DNA analysis (personality synthesis)
- slow_path_m2_indicators: Purchase temperature, churn risk
- slow_path_m3_psychometrics: DISC, Big Five, Schwartz profiles
- slow_path_m4_motivation: Key insights and Tesla hooks
- slow_path_m5_predictions: Scenario planning
- slow_path_m6_playbook: Tactical playbook (SSR framework)
- slow_path_m7_decision: Decision maker identification

NEGATIVE FEEDBACK ({len(feedback_list)} total):
{feedback_text}

ANALYSIS INSTRUCTIONS:
1. Identify COMMON PATTERNS in the negative feedback
2. Determine ROOT CAUSE of issues (prompt quality, context, logic errors)
3. Suggest CONCRETE IMPROVEMENTS (prompt refinement, RAG enhancement, logic fixes)
4. Prioritize by IMPACT (HIGH/MEDIUM/LOW)

OUTPUT FORMAT (JSON only):
{{
  "suggested_improvement": "Detailed improvement description (max 500 words)",
  "rationale": "Why this improvement addresses the feedback",
  "priority": "HIGH | MEDIUM | LOW",
  "implementation_type": "prompt_refinement | rag_enhancement | logic_fix | context_expansion"
}}

CRITICAL: Output ONLY valid JSON. No markdown, no explanations outside JSON.
        """.strip()

        return prompt

    async def _mark_as_processed(self, db: AsyncSession, feedback_ids: List[str]) -> None:
        """
        Mark feedback records as processed

        Args:
            db: Database session
            feedback_ids: List of feedback IDs to mark
        """
        if not feedback_ids:
            return

        # Fetch records
        stmt = select(FeedbackLog).where(FeedbackLog.id.in_(feedback_ids))
        result = await db.execute(stmt)
        records = result.scalars().all()

        # Update processed flag
        for record in records:
            record.processed = True

        await db.commit()

        print(f"[DOJO-REFINER] ✅ Marked {len(records)} feedback(s) as processed")


# === GLOBAL INSTANCE ===
dojo_refiner = DojoRefiner()
