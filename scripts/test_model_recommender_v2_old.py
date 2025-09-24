#!/usr/bin/env python3
"""
Test script for Model Recommender V2 enhancements.

Tests the external data integration for LMSYS Arena and MTEB leaderboards.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "mcp-servers" / "router-mcp" / "src"))

from router_mcp.model_recommender import ModelRecommender, TaskContext


async def test_model_recommender_v2():
    """Test the enhanced model recommender with external data fetching."""
    print("🧪 Testing Model Recommender V2 Enhancements")
    print("=" * 50)
    
    # Enable V2 features for testing
    os.environ["ENABLE_MODEL_RECOMMENDER_V2"] = "true"
    
    # Initialize recommender
    recommender = ModelRecommender()
    
    # Test Arena data fetching
    print("\n📊 Testing LMSYS Arena data fetching...")
    try:
        arena_data = await recommender._fetch_arena_leaderboard()
        print(f"✅ Successfully fetched Arena data for {len(arena_data)} models")
        
        # Show top models
        sorted_models = sorted(arena_data.items(), key=lambda x: x[1], reverse=True)[:5]
        print("🏆 Top 5 models by Arena Elo:")
        for model, elo in sorted_models:
            print(f"  {model}: {elo}")
            
    except Exception as e:
        print(f"❌ Arena data fetching failed: {e}")
    
    # Test MTEB data fetching
    print("\n🔍 Testing MTEB data fetching...")
    try:
        mteb_data = await recommender._fetch_mteb_scores()
        print(f"✅ Successfully fetched MTEB data for {len(mteb_data)} models")
        
        # Show top embedding models
        sorted_models = sorted(mteb_data.items(), key=lambda x: x[1], reverse=True)[:3]
        print("🎯 Top 3 embedding models by MTEB score:")
        for model, score in sorted_models:
            print(f"  {model}: {score:.2f}")
            
    except Exception as e:
        print(f"❌ MTEB data fetching failed: {e}")
    
    # Test model recommendation
    print("\n🎯 Testing model recommendation...")
    try:
        # Test chat task recommendation
        chat_context = TaskContext(
            task_type="chat",
            tenant_id="test-tenant",
            complexity="high",
            max_latency_ms=2000
        )
        
        primary, fallbacks = await recommender.recommend_model(chat_context)
        print(f"💬 Chat recommendation: {primary}")
        print(f"   Fallbacks: {fallbacks}")
        
        # Test embedding task recommendation
        embed_context = TaskContext(
            task_type="embed",
            tenant_id="test-tenant", 
            complexity="medium"
        )
        
        primary, fallbacks = await recommender.recommend_model(embed_context)
        print(f"🔗 Embedding recommendation: {primary}")
        print(f"   Fallbacks: {fallbacks}")
        
    except Exception as e:
        print(f"❌ Model recommendation failed: {e}")
    
    # Test fallback behavior with V2 disabled
    print("\n🔄 Testing fallback behavior (V2 disabled)...")
    os.environ["ENABLE_MODEL_RECOMMENDER_V2"] = "false"
    
    try:
        arena_data_fallback = await recommender._fetch_arena_leaderboard()
        print(f"✅ Fallback Arena data: {len(arena_data_fallback)} models")
        
        mteb_data_fallback = await recommender._fetch_mteb_scores()
        print(f"✅ Fallback MTEB data: {len(mteb_data_fallback)} models")
        
    except Exception as e:
        print(f"❌ Fallback testing failed: {e}")
    
    print("\n🎉 Model Recommender V2 testing completed!")
    
    # Cleanup
    await recommender.client.aclose()


if __name__ == "__main__":
    asyncio.run(test_model_recommender_v2())