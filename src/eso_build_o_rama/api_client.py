"""
ESO Logs API Client
Handles authentication and API requests to ESO Logs.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from esologs import Client, get_access_token

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ESOLogsAPIClient:
    """Client for interacting with ESO Logs API."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the ESO Logs API client.
        
        Args:
            client_id: ESO Logs client ID (defaults to env var ESOLOGS_ID)
            client_secret: ESO Logs client secret (defaults to env var ESOLOGS_SECRET)
        """
        self.client_id = client_id or os.getenv("ESOLOGS_ID")
        self.client_secret = client_secret or os.getenv("ESOLOGS_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "ESO Logs credentials not found. "
                "Set ESOLOGS_ID and ESOLOGS_SECRET environment variables."
            )
        
        # Get access token and initialize the client
        self.access_token = get_access_token(self.client_id, self.client_secret)
        self.client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        logger.info("ESO Logs API client initialized")
    
    async def get_zones(self) -> List[Dict[str, Any]]:
        """
        Get all available zones (trials).
        
        Returns:
            List of zone dictionaries with id, name, and encounters
        """
        logger.info("Fetching available zones")
        result = await self.client.get_zones()
        
        if result and result.world_data and result.world_data.zones:
            zones = []
            for zone in result.world_data.zones:
                zone_dict = {
                    "id": zone.id,
                    "name": zone.name,
                    "encounters": []
                }
                if zone.encounters:
                    for encounter in zone.encounters:
                        zone_dict["encounters"].append({
                            "id": encounter.id,
                            "name": encounter.name
                        })
                zones.append(zone_dict)
            
            logger.info(f"Found {len(zones)} zones")
            return zones
        
        logger.warning("No zones found")
        return []
    
    async def get_top_logs(
        self, 
        zone_id: int, 
        encounter_id: Optional[int] = None,
        limit: int = 5,
        difficulty: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top logs for a specific zone/encounter.
        
        Args:
            zone_id: Zone ID (trial)
            encounter_id: Optional specific encounter/boss ID
            limit: Number of top logs to fetch (default: 5)
            difficulty: Optional difficulty level
            
        Returns:
            List of ranking data
        """
        query = """
        query GetRankings(
          $zoneID: Int!
          $encounterID: Int
          $difficulty: Int
          $limit: Int
        ) {
          worldData {
            encounter(id: $encounterID) {
              characterRankings(
                zoneID: $zoneID
                difficulty: $difficulty
                limit: $limit
                metric: dps
              ) {
                data {
                  name
                  class
                  spec
                  amount
                  report {
                    code
                    startTime
                    fightID
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "zoneID": zone_id,
            "encounterID": encounter_id,
            "difficulty": difficulty,
            "limit": limit
        }
        
        logger.info(f"Fetching top {limit} logs for zone {zone_id}, encounter {encounter_id}")
        result = await self.client.query(query, variables)
        
        encounter_data = result.get("worldData", {}).get("encounter", {})
        rankings = encounter_data.get("characterRankings", {}).get("data", [])
        
        logger.info(f"Found {len(rankings)} top logs")
        return rankings
    
    async def get_report(self, report_code: str) -> Dict[str, Any]:
        """
        Get detailed report information by code.
        
        Args:
            report_code: Report code from ESO Logs
            
        Returns:
            Report data dictionary
        """
        query = """
        query GetReportByCode($code: String!) {
          reportData {
            report(code: $code) {
              code
              title
              startTime
              endTime
              zone {
                id
                name
              }
              fights {
                id
                name
                startTime
                endTime
                difficulty
                kill
                bossPercentage
                fightPercentage
              }
              masterData {
                actors {
                  id
                  name
                  type
                  subType
                  server
                }
              }
            }
          }
        }
        """
        
        variables = {"code": report_code}
        
        logger.info(f"Fetching report {report_code}")
        try:
            result = await self.client.get_report_by_code(report_code)
            
            if result and hasattr(result, 'report_data') and hasattr(result.report_data, 'report'):
                report_obj = result.report_data.report
                
                report = {
                    "code": getattr(report_obj, 'code', report_code),
                    "title": getattr(report_obj, 'title', 'Unknown Title'),
                    "startTime": getattr(report_obj, 'start_time', 0),
                    "endTime": getattr(report_obj, 'end_time', 0),
                    "fights": [
                        {
                            "id": getattr(fight, 'id', 0),
                            "name": getattr(fight, 'name', 'Unknown Fight'),
                            "startTime": getattr(fight, 'start_time', 0),
                            "endTime": getattr(fight, 'end_time', 0),
                            "difficulty": getattr(fight, 'difficulty', 0),
                            "kill": getattr(fight, 'kill', False)
                        }
                        for fight in getattr(report_obj, 'fights', [])
                    ]
                }
                
                logger.info(f"Fetched report: {report.get('title', 'Unknown')} with {len(report['fights'])} fights")
                return report
            
            logger.warning(f"Report {report_code} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching report {report_code}: {e}")
            return None
    
    async def get_report_table(
        self,
        report_code: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        fight_ids: Optional[List[int]] = None,
        data_type: str = "DamageDone",
        include_combatant_info: bool = False
    ) -> Dict[str, Any]:
        """
        Get table data for a report (DPS, damage breakdown, etc.).
        
        Args:
            report_code: Report code
            start_time: Optional fight start time
            end_time: Optional fight end time
            fight_ids: Optional list of fight IDs
            data_type: Type of data (DamageDone, Healing, Summary, etc.)
            include_combatant_info: If True, includes ability bars and gear (CRITICAL for build analysis!)
            
        Returns:
            Table data dictionary (with combatant info if requested)
        """
        query = """
        query GetReportTable(
          $code: String!
          $startTime: Float
          $endTime: Float
          $dataType: TableDataType!
          $fightIDs: [Int]
        ) {
          reportData {
            report(code: $code) {
              table(
                startTime: $startTime
                endTime: $endTime
                dataType: $dataType
                fightIDs: $fightIDs
              )
            }
          }
        }
        """
        
        variables = {
            "code": report_code,
            "startTime": start_time,
            "endTime": end_time,
            "dataType": data_type,
            "fightIDs": fight_ids
        }
        
        logger.info(f"Fetching table data for report {report_code}")
        try:
            result = await self.client.get_report_table(
                code=report_code,
                start_time=start_time,
                end_time=end_time,
                data_type=data_type,
                hostility_type="Friendlies",
                fight_ids=fight_ids,
                include_combatant_info=include_combatant_info
            )
            
            if result:
                return result
            
            logger.warning("No table data found")
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching table data: {e}")
            return {}
    
    async def close(self):
        """Close the client connection."""
        if hasattr(self.client, 'close'):
            if asyncio.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close()
        logger.info("ESO Logs API client closed")
