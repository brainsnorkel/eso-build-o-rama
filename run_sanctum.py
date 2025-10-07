"""Run ESO Build-O-Rama for Sanctum Ophidia."""
import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.main import ESOBuildORM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("="*60)
    logger.info("Running ESO Build-O-Rama for Sanctum Ophidia")
    logger.info("="*60)
    
    app = ESOBuildORM(use_cache=True, clear_cache=False)
    
    try:
        await app.run(trial_name="Sanctum Ophidia")
    finally:
        if hasattr(app.scanner, 'close'):
            await app.scanner.close()

if __name__ == "__main__":
    asyncio.run(main())

