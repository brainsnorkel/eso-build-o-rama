"""
CSV Exporter Module
Exports player build data to CSV format for analysis.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from .models import PlayerBuild, TrialReport

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports player build data to CSV files."""
    
    # Gear slot names in order
    GEAR_SLOTS = [
        'head', 'chest', 'shoulders', 'hands', 'waist', 'legs', 'feet',
        'necklace', 'ring1', 'ring2',
        'main_hand', 'off_hand', 'backup_main_hand', 'backup_off_hand'
    ]
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize CSV exporter.
        
        Args:
            output_dir: Directory to write CSV files to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_gear_slot_value(self, player: PlayerBuild, slot: str) -> str:
        """
        Get the gear item name for a specific slot.
        
        Args:
            player: PlayerBuild object
            slot: Slot name (e.g., 'head', 'chest')
            
        Returns:
            Item name or empty string if not found
        """
        for gear in player.gear:
            if gear.slot.lower() == slot.lower():
                return f"{gear.item_name} ({gear.set_name})"
        return ""
    
    def _get_ability_names(self, abilities: List[Any]) -> List[str]:
        """
        Extract ability names from ability list.
        
        Args:
            abilities: List of Ability objects
            
        Returns:
            List of ability names
        """
        return [ability.ability_name for ability in abilities if ability.ability_name]
    
    def export_trial_data(
        self,
        trial_name: str,
        all_reports: List[TrialReport],
        report_codes: Dict[str, str]
    ) -> Path:
        """
        Export all player data from a trial to CSV.
        
        Args:
            trial_name: Name of the trial
            all_reports: List of TrialReport objects from all boss fights
            report_codes: Dict mapping fight_id to report_code for ESO Logs links
            
        Returns:
            Path to the generated CSV file
        """
        # Create filename
        trial_slug = trial_name.lower().replace("'", "").replace(" ", "-")
        csv_path = self.output_dir / f"{trial_slug}-data.csv"
        
        logger.info(f"Generating CSV export for {trial_name}")
        
        # Prepare CSV headers
        headers = [
            'Trial Name',
            'Boss Name',
            'ESO Logs Player Link',
            'Player Handle',
            'Character Name',
            'Build Slug',
            'Role',
            'Subclass 1',
            'Subclass 2',
            'Subclass 3',
            'Signature Set 1',
            'Signature Set 2',
            'DPS',
            'HPS',
            'CPM',
            'Primary Metric',
            'Mundus Stone'
        ]
        
        # Add gear slots
        headers.extend([f'Gear: {slot.title()}' for slot in self.GEAR_SLOTS])
        
        # Add ability bars (up to 6 abilities each)
        headers.extend([f'Bar 1 Ability {i+1}' for i in range(6)])
        headers.extend([f'Bar 2 Ability {i+1}' for i in range(6)])
        
        # Collect all rows
        rows = []
        total_players = 0
        
        for trial_report in all_reports:
            boss_name = trial_report.boss_name
            report_code = trial_report.report_code or ""
            fight_id = trial_report.fight_id or 0
            
            for player in trial_report.all_players:
                total_players += 1
                
                # Build ESO Logs player summary link
                # Format: https://www.esologs.com/reports/{code}#fight={fight}&type=summary&source={source}
                if report_code and fight_id and player.source_id:
                    esologs_link = f"https://www.esologs.com/reports/{report_code}#fight={fight_id}&type=summary&source={player.source_id}"
                else:
                    esologs_link = ""
                
                # Get subclasses (pad to 3)
                subclasses = (player.subclasses + ['', '', ''])[:3]
                
                # Get signature sets (pad to 2)
                sets = (list(player.sets_equipped) + ['', ''])[:2]
                
                # Build the row
                row = [
                    trial_name,
                    boss_name,
                    esologs_link,
                    player.player_name,
                    player.character_name,
                    player.get_build_slug(),
                    player.role,
                    subclasses[0],
                    subclasses[1],
                    subclasses[2],
                    sets[0],
                    sets[1],
                    f"{player.dps:.1f}" if player.dps else "0.0",
                    f"{player.healing:.1f}" if player.healing else "0.0",
                    f"{player.crowd_control:.1f}" if player.crowd_control else "0.0",
                    f"{player.get_primary_metric():.1f} {player.get_primary_metric_name()}",
                    player.mundus or ""
                ]
                
                # Add gear slots
                for slot in self.GEAR_SLOTS:
                    row.append(self._get_gear_slot_value(player, slot))
                
                # Add ability bars
                bar1_abilities = self._get_ability_names(player.abilities_bar1)
                bar2_abilities = self._get_ability_names(player.abilities_bar2)
                
                # Pad to 6 abilities each
                bar1_abilities = (bar1_abilities + [''] * 6)[:6]
                bar2_abilities = (bar2_abilities + [''] * 6)[:6]
                
                row.extend(bar1_abilities)
                row.extend(bar2_abilities)
                
                rows.append(row)
        
        # Write CSV with proper quoting for Excel compatibility
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(headers)
                writer.writerows(rows)
            
            logger.info(f"✅ Exported {total_players} players to {csv_path}")
            return csv_path
            
        except IOError as e:
            logger.error(f"Failed to write CSV file {csv_path}: {e}")
            raise

