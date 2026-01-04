"""
DOJO VERIFICATION SCRIPT
========================
This script tests the feedback loop to ensure it works end-to-end.

Steps:
1. Connect to database
2. Create a test feedback entry
3. Read it back from the database
4. Verify data integrity
5. Clean up test data

Author: Lead Fullstack Developer
Version: 1.0.0
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db, init_db
from backend.models import FeedbackLog, Session
from sqlalchemy import select


async def verify_dojo():
    """Main verification function."""
    print("=" * 60)
    print("🥋 DOJO FEEDBACK LOOP VERIFICATION")
    print("=" * 60)
    print()

    # Step 1: Initialize database
    print("[1/5] Initializing database...")
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

    print()

    # Step 2: Create test session (optional, for FK constraint)
    print("[2/5] Creating test session...")
    test_session_id = "test_session_dojo_verify"
    test_feedback_id = None

    try:
        async for db in get_db():
            # Check if test session exists
            result = await db.execute(select(Session).where(Session.id == test_session_id))
            existing_session = result.scalar_one_or_none()

            if not existing_session:
                # Create test session
                test_session = Session(
                    id=test_session_id,
                    status="active",
                    journey_stage="DISCOVERY"
                )
                db.add(test_session)
                await db.commit()
                print(f"✅ Test session created: {test_session_id}")
            else:
                print(f"ℹ️  Test session already exists: {test_session_id}")

            break  # Exit after first iteration
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 3: Create test feedback entry
    print("[3/5] Creating test feedback entry...")
    try:
        async for db in get_db():
            # Create feedback entry
            test_feedback = FeedbackLog(
                session_id=test_session_id,
                module_name="fast_path",
                rating=False,  # Thumbs down
                user_input_snapshot="User: I'm interested in Tesla Model 3. What's the price?",
                ai_output_snapshot="AI: The Tesla Model 3 starts at $40,000 USD.",
                expert_comment="CORRECTION: Should mention Polish pricing (from ~180,000 PLN) and available subsidies (Dotacja: 27k-40k PLN). Also mention leasing options.",
                timestamp=int(time.time() * 1000)
            )

            db.add(test_feedback)
            await db.commit()
            await db.refresh(test_feedback)

            test_feedback_id = test_feedback.id
            print(f"✅ Feedback entry created: {test_feedback_id}")
            print(f"   Module: {test_feedback.module_name}")
            print(f"   Rating: {'👍 Positive' if test_feedback.rating else '👎 Negative'}")
            print(f"   Expert Comment: {test_feedback.expert_comment[:80]}...")

            break
    except Exception as e:
        print(f"❌ Feedback creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 4: Read feedback back from database
    print("[4/5] Reading feedback from database...")
    try:
        async for db in get_db():
            # Query the feedback we just created
            result = await db.execute(
                select(FeedbackLog).where(FeedbackLog.id == test_feedback_id)
            )
            retrieved_feedback = result.scalar_one_or_none()

            if not retrieved_feedback:
                print(f"❌ Feedback not found in database!")
                return False

            # Verify data integrity
            print(f"✅ Feedback retrieved successfully")
            print(f"   ID: {retrieved_feedback.id}")
            print(f"   Module: {retrieved_feedback.module_name}")
            print(f"   Rating: {'👍' if retrieved_feedback.rating else '👎'}")
            print(f"   User Input: {retrieved_feedback.user_input_snapshot[:60]}...")
            print(f"   AI Output: {retrieved_feedback.ai_output_snapshot[:60]}...")
            print(f"   Expert Comment: {retrieved_feedback.expert_comment[:60]}...")
            print(f"   Timestamp: {retrieved_feedback.timestamp}")

            # Verify fields match
            assert retrieved_feedback.session_id == test_session_id
            assert retrieved_feedback.module_name == "fast_path"
            assert retrieved_feedback.rating == False
            assert "Tesla Model 3" in retrieved_feedback.user_input_snapshot
            assert "Polish pricing" in retrieved_feedback.expert_comment

            print("✅ Data integrity verified")

            break
    except Exception as e:
        print(f"❌ Feedback retrieval/verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 5: Query all feedback for the module
    print("[5/5] Querying all feedback for module 'fast_path'...")
    try:
        async for db in get_db():
            result = await db.execute(
                select(FeedbackLog)
                .where(FeedbackLog.module_name == "fast_path")
                .order_by(FeedbackLog.timestamp.desc())
                .limit(5)
            )
            all_feedback = result.scalars().all()

            print(f"✅ Found {len(all_feedback)} feedback entries for 'fast_path'")

            for idx, fb in enumerate(all_feedback, 1):
                print(f"   [{idx}] {fb.id[:8]}... - {'👍' if fb.rating else '👎'} - {fb.module_name}")

            break
    except Exception as e:
        print(f"❌ Feedback query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 60)
    print("🎉 DOJO VERIFICATION COMPLETE!")
    print("=" * 60)
    print()
    print("SUMMARY:")
    print(f"✅ Database connection: OK")
    print(f"✅ Feedback creation: OK")
    print(f"✅ Feedback retrieval: OK")
    print(f"✅ Data integrity: OK")
    print(f"✅ Query functionality: OK")
    print()
    print("🥋 The Dojo feedback loop is fully operational!")
    print()

    # Cleanup option
    print("CLEANUP:")
    print(f"   Test session ID: {test_session_id}")
    print(f"   Test feedback ID: {test_feedback_id}")
    print()
    cleanup = input("Delete test data? (y/n): ").strip().lower()

    if cleanup == 'y':
        try:
            async for db in get_db():
                # Delete feedback
                if test_feedback_id:
                    result = await db.execute(
                        select(FeedbackLog).where(FeedbackLog.id == test_feedback_id)
                    )
                    fb = result.scalar_one_or_none()
                    if fb:
                        await db.delete(fb)
                        print(f"   Deleted feedback: {test_feedback_id}")

                # Delete session
                result = await db.execute(
                    select(Session).where(Session.id == test_session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    await db.delete(session)
                    print(f"   Deleted session: {test_session_id}")

                await db.commit()
                print("✅ Cleanup complete")
                break
        except Exception as e:
            print(f"⚠️  Cleanup failed (not critical): {e}")
    else:
        print("   Test data preserved for inspection")

    return True


if __name__ == "__main__":
    print()
    result = asyncio.run(verify_dojo())

    if result:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Verification failed!")
        sys.exit(1)
