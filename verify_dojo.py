#!/usr/bin/env python3
"""
ULTRA v3.0 - AI Dojo Verification Script

This script verifies the Feedback Loop data flow:
1. Simulates adding a feedback entry via API
2. Queries the database to show the last 3 feedback entries
3. Displays: Module | Input Snapshot | AI Output | Expert Comment

Usage:
    python verify_dojo.py
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


async def submit_test_feedback():
    """Submit a test feedback entry via API"""
    print("\n" + "=" * 60)
    print("📤 STEP 1: Submitting Test Feedback via API")
    print("=" * 60)
    
    test_feedback = {
        "session_id": "TEST-VERIFY-001",
        "module_name": "fast_path",
        "rating": False,  # Negative feedback for testing
        "user_input_snapshot": "User asked: 'What is the range of Tesla Model 3 in winter?'",
        "ai_output_snapshot": json.dumps({
            "response": "Tesla Model 3 has great range even in winter.",
            "confidence": 0.85
        }),
        "expert_comment": "Response lacks specific numbers. Should mention 10-20% range reduction and Heat Pump benefits."
    }
    
    print(f"\nPayload:")
    print(json.dumps(test_feedback, indent=2))
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/feedback",
                json=test_feedback,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"\n✅ Feedback submitted successfully!")
                    print(f"   ID: {result.get('id')}")
                    print(f"   Message: {result.get('message')}")
                    return True
                else:
                    print(f"\n❌ Failed to submit feedback: {result}")
                    return False
    except aiohttp.ClientError as e:
        print(f"\n❌ Connection error: {e}")
        print("   Make sure the backend is running: python -m uvicorn backend.main:app --reload")
        return False


async def fetch_feedback_stats():
    """Fetch feedback statistics"""
    print("\n" + "=" * 60)
    print("📊 STEP 2: Fetching Feedback Statistics")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/api/feedback/stats") as response:
                stats = await response.json()
                
                print(f"\n📈 Feedback Statistics:")
                print(f"   Total Entries: {stats.get('total', 0)}")
                print(f"   Positive (👍): {stats.get('positive', 0)}")
                print(f"   Negative (👎): {stats.get('negative', 0)}")
                print(f"   Approval Rate: {stats.get('approval_rate', 0)}%")
                
                if stats.get('by_module'):
                    print(f"\n   By Module:")
                    for module, count in stats.get('by_module', {}).items():
                        print(f"      - {module}: {count}")
                
                return stats
    except aiohttp.ClientError as e:
        print(f"\n❌ Connection error: {e}")
        return None


async def fetch_last_feedback_entries(limit=3):
    """Fetch the last N feedback entries from the API"""
    print("\n" + "=" * 60)
    print(f"📋 STEP 3: Fetching Last {limit} Feedback Entries")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/api/feedback?limit={limit}"
            ) as response:
                data = await response.json()
                items = data.get('items', [])
                
                if not items:
                    print("\n⚠️  No feedback entries found in database.")
                    return []
                
                print(f"\n✅ Found {len(items)} feedback entries:\n")
                
                for i, item in enumerate(items, 1):
                    rating_emoji = "👍" if item.get('rating') else "👎"
                    timestamp = datetime.fromtimestamp(
                        item.get('timestamp', 0) / 1000
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"{'─' * 58}")
                    print(f"📝 Entry #{i} | {rating_emoji} | {item.get('module_name', 'unknown')}")
                    print(f"{'─' * 58}")
                    print(f"   Session: {item.get('session_id', 'N/A')}")
                    print(f"   Timestamp: {timestamp}")
                    
                    # Input Snapshot
                    user_input = item.get('user_input_snapshot')
                    if user_input:
                        # Truncate if too long
                        display_input = user_input[:150] + "..." if len(user_input) > 150 else user_input
                        print(f"\n   📥 INPUT CONTEXT:")
                        print(f"      {display_input}")
                    else:
                        print(f"\n   📥 INPUT CONTEXT: (not captured)")
                    
                    # AI Output
                    ai_output = item.get('ai_output_snapshot')
                    if ai_output:
                        # Try to parse JSON, fallback to raw
                        try:
                            parsed = json.loads(ai_output)
                            display_output = json.dumps(parsed, indent=2)[:200]
                        except:
                            display_output = ai_output[:200]
                        if len(ai_output) > 200:
                            display_output += "..."
                        print(f"\n   🤖 AI OUTPUT:")
                        for line in display_output.split('\n'):
                            print(f"      {line}")
                    else:
                        print(f"\n   🤖 AI OUTPUT: (not captured)")
                    
                    # Expert Comment
                    comment = item.get('expert_comment')
                    if comment:
                        print(f"\n   💡 EXPERT COMMENT:")
                        print(f"      {comment}")
                    else:
                        print(f"\n   💡 EXPERT COMMENT: (none)")
                    
                    print()
                
                return items
                
    except aiohttp.ClientError as e:
        print(f"\n❌ Connection error: {e}")
        return []


async def main():
    """Main verification flow"""
    print("\n" + "🎯" * 30)
    print("   ULTRA v3.0 - AI DOJO VERIFICATION SCRIPT")
    print("🎯" * 30)
    print("\nThis script verifies the Feedback Loop data flow.\n")
    
    # Step 1: Submit test feedback
    success = await submit_test_feedback()
    
    if not success:
        print("\n⚠️  Skipping remaining steps due to connection failure.")
        print("   Please ensure the backend is running and try again.")
        return
    
    # Small delay to allow database write
    await asyncio.sleep(0.5)
    
    # Step 2: Fetch stats
    await fetch_feedback_stats()
    
    # Step 3: Fetch last entries
    await fetch_last_feedback_entries(limit=3)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
    print("""
The feedback system is working correctly if you see:
1. A successful POST response with feedback ID
2. Statistics showing at least 1 entry
3. The last 3 feedback entries with:
   - Module name
   - Input context (user message)
   - AI output (response being rated)
   - Expert comment (if negative feedback)

The database (ultra.db) is now accumulating training data!
""")


if __name__ == "__main__":
    asyncio.run(main())

