#!/usr/bin/env python3
"""
Nightly refresh job for Model Recommender V2.

This script fetches fresh data from LMSYS Arena, MTEB, and internal 
evaluations to update the model performance cache.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the router_mcp package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from router_mcp.model_recommender import ModelRecommender, is_model_recommender_v2_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main refresh job function."""
    logger.info("Starting Model Recommender V2 nightly refresh job")
    
    # Check if V2 is enabled
    if not is_model_recommender_v2_enabled():
        logger.warning("Model Recommender V2 is disabled. Set ENABLE_MODEL_RECOMMENDER_V2=true to enable.")
        return 0
    
    try:
        # Initialize model recommender
        recommender = ModelRecommender()
        logger.info("Initialized model recommender")
        
        # Force refresh performance cache
        logger.info("Refreshing performance cache from external sources...")
        await recommender._refresh_performance_cache()
        
        # Log cache statistics
        cache_size = len(recommender.performance_cache)
        last_update = recommender.last_cache_update
        
        logger.info(f"Refresh completed successfully:")
        logger.info(f"  - Cached models: {cache_size}")
        logger.info(f"  - Last update: {last_update}")
        
        # Log some sample data for verification
        for i, (model_name, perf) in enumerate(list(recommender.performance_cache.items())[:5]):
            logger.info(f"  - {model_name}: arena_elo={perf.arena_elo}, mteb_score={perf.mteb_score}")
            if i >= 4:  # Limit to first 5 models
                break
        
        if cache_size > 5:
            logger.info(f"  ... and {cache_size - 5} more models")
        
        logger.info("Model Recommender V2 refresh job completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Model Recommender V2 refresh job failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)