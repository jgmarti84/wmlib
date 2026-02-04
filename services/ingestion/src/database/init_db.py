"""Database initialization helper for new schema."""
from typing import List
import json
from pathlib import Path
import structlog
from sqlalchemy.orm import Session
from decimal import Decimal

from src.models import Radar, Strategy, Volume, RadarStrategy
from src.config import RadarConfig, StrategyConfig, VolumeConfig

logger = structlog.get_logger()

# Path to seed data file
SEED_DATA_PATH = Path(__file__).parent / "radars_seed.json"


def load_radar_seed_data() -> List[dict]:
    """Load radar seed data from JSON file.
    
    Returns:
        List of radar dictionaries with metadata
    """
    if not SEED_DATA_PATH.exists():
        logger.warning("radar_seed_file_not_found", path=str(SEED_DATA_PATH))
        return []
    
    try:
        with open(SEED_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("radar_seed_data_loaded", count=len(data))
        return data
    except Exception as e:
        logger.error("error_loading_radar_seed_data", error=str(e))
        return []


def ensure_radars_from_seed(session: Session) -> None:
    """Ensure all radars from seed data exist in the database.
    
    This creates or updates radars based on the seed file.
    Only updates location metadata, doesn't affect strategies.
    
    Args:
        session: Database session
    """
    from src.database.repository import RadarRepository
    
    radar_repo = RadarRepository(session)
    seed_data = load_radar_seed_data()
    
    for radar_data in seed_data:
        radar = radar_repo.get_by_code(radar_data['code'])
        if radar:
            # Update existing radar metadata
            radar.title = radar_data['title']
            radar.description = radar_data['description']
            radar.center_lat = Decimal(radar_data['center_lat'])
            radar.center_long = Decimal(radar_data['center_long'])
            radar.is_active = radar_data.get('is_active', True)
            logger.info("radar_updated_from_seed", radar_code=radar_data['code'])
        else:
            # Create new radar
            radar = Radar(
                code=radar_data['code'],
                title=radar_data['title'],
                description=radar_data['description'],
                center_lat=Decimal(radar_data['center_lat']),
                center_long=Decimal(radar_data['center_long']),
                is_active=radar_data.get('is_active', True)
            )
            radar_repo.create(radar)
            logger.info("radar_created_from_seed", radar_code=radar_data['code'])
    
    session.flush()


def initialize_radar_with_strategies(
    session: Session,
    radar_config: RadarConfig
) -> Radar:
    """Initialize or update radar with its strategies.
    
    This handles the new schema where strategies are in separate tables.
    Radar location metadata is loaded from seed file if not provided in config.
    
    Args:
        session: Database session
        radar_config: Radar configuration from settings
        
    Returns:
        Created or updated Radar instance
    """
    from src.database.repository import RadarRepository, StrategyRepository
    
    radar_repo = RadarRepository(session)
    strategy_repo = StrategyRepository(session)
    
    # Get or create radar
    radar = radar_repo.get_by_code(radar_config.code)
    if radar:
        # Update radar metadata if provided in config
        # Otherwise, keep existing values (from seed file)
        if hasattr(radar_config, 'title') and radar_config.title:
            radar.title = radar_config.title
        if hasattr(radar_config, 'description') and radar_config.description:
            radar.description = radar_config.description
        if hasattr(radar_config, 'center_lat') and radar_config.center_lat is not None:
            radar.center_lat = radar_config.center_lat
        if hasattr(radar_config, 'center_long') and radar_config.center_long is not None:
            radar.center_long = radar_config.center_long
        if hasattr(radar_config, 'is_active') and radar_config.is_active is not None:
            radar.is_active = radar_config.is_active
        logger.info("radar_updated", radar_code=radar_config.code)
    else:
        # Create new radar - must have metadata from config or will fail
        if not all([
            hasattr(radar_config, 'title'),
            hasattr(radar_config, 'center_lat'),
            hasattr(radar_config, 'center_long')
        ]):
            logger.error(
                "radar_not_in_seed_and_no_metadata",
                radar_code=radar_config.code
            )
            raise ValueError(
                f"Radar {radar_config.code} not found in seed data and "
                "no location metadata provided in config"
            )
        
        radar = Radar(
            code=radar_config.code,
            title=radar_config.title,
            description=getattr(radar_config, 'description', ''),
            center_lat=radar_config.center_lat,
            center_long=radar_config.center_long,
            is_active=getattr(radar_config, 'is_active', True)
        )
        radar_repo.create(radar)
        logger.info("radar_created", radar_code=radar_config.code)
    
    # Process strategies
    for strat_config in radar_config.strategies:
        # Get or create strategy
        strategy = strategy_repo.get_by_strategy_id(strat_config.strategy_id)
        if not strategy:
            strategy = Strategy(
                strategy_id=strat_config.strategy_id,
                name=f"Strategy {strat_config.strategy_id}",
                is_active=True
            )
            strategy_repo.create(strategy)
            logger.info("strategy_created", strategy_id=strat_config.strategy_id)
        
        # Create or update volumes for this strategy
        existing_volumes = {v.volume_number: v for v in strategy.volumes}
        for i, vol_config in enumerate(strat_config.volumes):
            fields_str = ",".join(vol_config.fields)
            if vol_config.number in existing_volumes:
                # Update existing volume
                vol = existing_volumes[vol_config.number]
                vol.fields = fields_str
                vol.sort_order = i
            else:
                # Create new volume
                vol = Volume(
                    strategy_id=strategy.id,
                    volume_number=vol_config.number,
                    fields=fields_str,
                    sort_order=i
                )
                session.add(vol)
        
        # Link strategy to radar if not already linked
        existing_link = session.query(RadarStrategy).filter(
            RadarStrategy.radar_code == radar.code,
            RadarStrategy.strategy_id == strategy.id
        ).first()
        
        if not existing_link:
            radar_strategy = RadarStrategy(
                radar_code=radar.code,
                strategy_id=strategy.id,
                is_active=True,
                priority=0
            )
            session.add(radar_strategy)
            logger.info(
                "radar_strategy_linked",
                radar_code=radar.code,
                strategy_id=strat_config.strategy_id
            )
    
    session.flush()
    return radar


def get_active_strategies_for_radar(
    session: Session,
    radar_code: str
) -> List[dict]:
    """Get active strategies for a radar in the format expected by the service.
    
    Args:
        session: Database session
        radar_code: Radar code
        
    Returns:
        List of strategy dictionaries with volumes and fields
    """
    strategies = session.query(Strategy).join(
        RadarStrategy
    ).filter(
        RadarStrategy.radar_code == radar_code,
        RadarStrategy.is_active == True,
        Strategy.is_active == True
    ).order_by(RadarStrategy.priority).all()
    
    result = []
    for strategy in strategies:
        volumes = []
        for volume in sorted(strategy.volumes, key=lambda v: v.sort_order):
            volumes.append({
                "number": volume.volume_number,
                "fields": volume.fields.split(",")
            })
        
        result.append({
            "strategy_id": strategy.strategy_id,
            "volumes": volumes
        })
    
    return result
