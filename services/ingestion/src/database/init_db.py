"""Database initialization helper for new schema."""
from typing import List
import structlog
from sqlalchemy.orm import Session

from src.models import Radar, Strategy, Volume, RadarStrategy
from src.config import RadarConfig, StrategyConfig, VolumeConfig

logger = structlog.get_logger()


def initialize_radar_with_strategies(
    session: Session,
    radar_config: RadarConfig
) -> Radar:
    """Initialize or update radar with its strategies.
    
    This handles the new schema where strategies are in separate tables.
    
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
        # Update existing radar
        radar.title = radar_config.title
        radar.description = radar_config.description
        radar.center_lat = radar_config.center_lat
        radar.center_long = radar_config.center_long
        radar.is_active = radar_config.is_active
        logger.info("radar_updated", radar_code=radar_config.code)
    else:
        # Create new radar
        radar = Radar(
            code=radar_config.code,
            title=radar_config.title,
            description=radar_config.description,
            center_lat=radar_config.center_lat,
            center_long=radar_config.center_long,
            is_active=radar_config.is_active
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
