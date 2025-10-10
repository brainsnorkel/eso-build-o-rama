"""
ESO Logs API Client
Handles authentication and API requests to ESO Logs.
"""

import os
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from esologs import Client, get_access_token
from esologs._generated.exceptions import GraphQLClientHttpError

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ESOLogsAPIClient:
    """Client for interacting with ESO Logs API."""
    
    # Constants for rate limiting
    DEFAULT_MIN_REQUEST_DELAY = 2.0  # Default minimum delay between requests in seconds
    DEFAULT_MAX_RETRIES = 3  # Default maximum number of retries
    DEFAULT_RETRY_DELAY = 120.0  # Default retry delay in seconds
    RATE_LIMIT_HTTP_STATUS = 429  # HTTP status code for rate limiting
    
    def __init__(
        self, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None,
        min_request_delay: float = DEFAULT_MIN_REQUEST_DELAY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize the ESO Logs API client.
        
        Args:
            client_id: ESO Logs client ID (defaults to env var ESOLOGS_ID)
            client_secret: ESO Logs client secret (defaults to env var ESOLOGS_SECRET)
            min_request_delay: Minimum delay between API requests in seconds (default: 2.0)
            max_retries: Maximum number of retries for rate-limited requests (default: 3)
            retry_delay: Delay in seconds after hitting rate limit (default: 120)
        """
        self.client_id = client_id or os.getenv("ESOLOGS_ID")
        self.client_secret = client_secret or os.getenv("ESOLOGS_SECRET")
        
        self._validate_credentials(self.client_id, self.client_secret)
        
        # Rate limiting settings
        self.min_request_delay = min_request_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = 0
        
        # Get access token and initialize the client
        self.access_token = get_access_token(self.client_id, self.client_secret)
        self.client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        logger.info(f"ESO Logs API client initialized (rate limit: {min_request_delay}s between requests)")
    
    def _validate_credentials(self, client_id: str, client_secret: str) -> None:
        """Validate ESO Logs API credentials."""
        if not client_id:
            raise ValueError(
                "ESO Logs client ID not found. "
                "Set ESOLOGS_ID environment variable."
            )
        if not client_secret:
            raise ValueError(
                "ESO Logs client secret not found. "
                "Set ESOLOGS_SECRET environment variable."
            )
        if len(client_id) < 10:
            raise ValueError("Invalid client ID format")
        if len(client_secret) < 20:
            raise ValueError("Invalid client secret format")
    
    async def _wait_for_rate_limit(self):
        """Ensure minimum delay between API requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_delay:
            delay = self.min_request_delay - time_since_last_request
            logger.debug(f"Rate limiting: waiting {delay:.2f}s")
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _retry_on_rate_limit(self, func, *args, **kwargs):
        """
        Retry a function call with exponential backoff on rate limit errors.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        for attempt in range(self.max_retries):
            try:
                await self._wait_for_rate_limit()
                return await func(*args, **kwargs)
                
            except GraphQLClientHttpError as e:
                if str(self.RATE_LIMIT_HTTP_STATUS) in str(e):  # Rate limit error
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (attempt + 1)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Rate limit exceeded after {self.max_retries} retries")
                        raise
                else:
                    raise
        
        raise Exception(f"Failed after {self.max_retries} retries")
    
    async def get_zones(self) -> List[Dict[str, Any]]:
        """
        Get all available zones (trials).
        
        Returns:
            List of zone dictionaries with id, name, and encounters
        """
        logger.info("Fetching available zones")
        result = await self._retry_on_rate_limit(self.client.get_zones)
        
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
        limit: int = 12,
        difficulty: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top-ranked reports for a specific zone/encounter using fightRankings.
        
        This uses fightRankings (speed metric) to find the top-performing reports,
        then returns the report codes. The caller can then fetch full reports
        to analyze all players in those top runs.
        
        Args:
            zone_id: Zone ID (trial)
            encounter_id: Optional specific encounter/boss ID
            limit: Number of top reports to fetch (default: 12)
            difficulty: Optional difficulty level
            
        Returns:
            List of report dictionaries with code, fightID, and metadata
        """
        # Input validation
        if not isinstance(zone_id, int) or zone_id <= 0:
            raise ValueError("zone_id must be a positive integer")
        if limit <= 0 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if difficulty is not None and (difficulty < 1 or difficulty > 3):
            raise ValueError("difficulty must be between 1 and 3")
        
        
        logger.info(f"Fetching top {limit} ranked reports for zone {zone_id}, encounter {encounter_id}")
        
        try:
            # Use fightRankings with speed metric to get top-performing reports
            query_fight_rankings = '''
            query GetTopRankedReports($encounterID: Int!) {
              worldData {
                encounter(id: $encounterID) {
                  fightRankings(
                    metric: speed
                  )
                }
              }
            }
            '''
            
            result = await self._retry_on_rate_limit(
                self.client.execute,
                query=query_fight_rankings,
                variables={"encounterID": encounter_id}
            )
            
            if result.status_code != 200:
                logger.error(f"API request failed with status {result.status_code}")
                return []
            
            data = result.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            fight_rankings = data['data']['worldData']['encounter']['fightRankings']
            
            # Extract rankings data from response
            if isinstance(fight_rankings, dict):
                rankings = fight_rankings.get('rankings', [])
            elif isinstance(fight_rankings, list):
                rankings = fight_rankings
            else:
                logger.error(f"Unexpected fightRankings format: {type(fight_rankings)}")
                return []
            
            # fightRankings returns unique reports by default (one ranking per report)
            # Extract report codes and metadata
            top_reports = []
            for ranking in rankings[:limit]:
                report = ranking.get('report', {})
                code = report.get('code')
                
                if code:
                    top_reports.append({
                        "code": code,
                        "fightID": report.get('fightID', 1),
                        "startTime": report.get('startTime', 0),
                        "duration": ranking.get('duration', 0),
                        "score": ranking.get('score', 0),
                        "guild": ranking.get('guild', {}),
                        "server": ranking.get('server', {}),
                        "composition": {
                            "tanks": ranking.get('tanks', 0),
                            "healers": ranking.get('healers', 0),
                            "melee": ranking.get('melee', 0),
                            "ranged": ranking.get('ranged', 0)
                        }
                    })
            
            logger.info(f"Found {len(top_reports)} top-ranked reports")
            return top_reports
            
        except Exception as e:
            logger.error(f"Error fetching fight rankings: {e}")
            return []
    
    async def get_report(self, report_code: str) -> Dict[str, Any]:
        """
        Get detailed report information by code.
        
        Args:
            report_code: Report code from ESO Logs
            
        Returns:
            Report data dictionary
        """
        # Input validation
        if not isinstance(report_code, str) or not report_code.strip():
            raise ValueError("report_code must be a non-empty string")
        if len(report_code) < 8 or len(report_code) > 16:
            raise ValueError("report_code must be between 8 and 16 characters")
        
        
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
            # Use custom GraphQL query to ensure we get the kill field
            result = await self._retry_on_rate_limit(
                self.client.execute,
                query=query,
                variables=variables
            )
            
            # Parse the JSON response from execute()
            if result.status_code != 200:
                logger.error(f"API request failed with status {result.status_code}")
                return None
            
            data = result.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None
            
            report_data = data['data']['reportData']['report']
            
            if not report_data:
                logger.warning(f"Report {report_code} not found")
                return None
            
            report = {
                "code": report_data.get('code', report_code),
                "title": report_data.get('title', 'Unknown Title'),
                "startTime": report_data.get('startTime', 0),
                "endTime": report_data.get('endTime', 0),
                "gameVersion": None,  # Not available in ESO Logs API
                "fights": report_data.get('fights', [])
            }
            
            logger.info(f"Fetched report: {report.get('title', 'Unknown')} with {len(report['fights'])} fights")
            return report
            
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
            result = await self._retry_on_rate_limit(
                self.client.get_report_table,
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
    
    # Mundus stone ability IDs (from ESO game data)
    MUNDUS_ABILITY_IDS = {
        13940: "The Warrior",
        13943: "The Mage",
        13974: "The Serpent",
        13975: "The Thief",
        13976: "The Lady",
        13977: "The Steed",
        13978: "The Lord",
        13979: "The Apprentice",
        13980: "The Ritual",
        13981: "The Lover",
        13982: "The Atronach",
        13984: "The Shadow",
        13985: "The Tower"
    }
    
    async def get_player_buffs(
        self, 
        report_code: str, 
        fight_ids: List[int],
        player_name: str,
        start_time: float,
        end_time: float,
        source_id: Optional[int] = None
    ) -> Optional[str]:
        """Get mundus stone from player's buff uptime by checking mundus ability IDs."""
        
        
        # Use sourceID to filter Buffs table to this specific player
        try:
            if source_id:
                # Query Buffs filtered by source ID
                result = await self._retry_on_rate_limit(
                    self.client.get_report_table,
                    code=report_code,
                    start_time=start_time,
                    end_time=end_time,
                    data_type="Buffs",
                    hostility_type="Friendlies",
                    source_id=source_id  # Filter by this player's source ID
                )
            else:
                # Fallback: get all buffs (less accurate)
                logger.warning(f"No source_id provided for {player_name}, getting all buffs")
                result = await self._retry_on_rate_limit(
                    self.client.get_report_table,
                    code=report_code,
                    start_time=start_time,
                    end_time=end_time,
                    data_type="Buffs",
                    hostility_type="Friendlies"
                )
            
            # Parse Buffs table to find mundus (100% uptime buffs matching mundus IDs)
            if result and hasattr(result, 'report_data') and hasattr(result.report_data, 'report'):
                table = result.report_data.report.table
                
                if isinstance(table, dict) and 'data' in table:
                    table_data = table['data']
                    auras = table_data.get('auras', [])
                    
                    logger.debug(f"Checking {len(auras)} auras for {player_name}")
                    
                    # Look through auras for THIS PLAYER's mundus buffs (filtered by source_id)
                    for aura in auras:
                        if isinstance(aura, dict):
                            ability_id = aura.get('guid')  # Ability ID
                            
                            # Check if this is a mundus buff
                            if ability_id in self.MUNDUS_ABILITY_IDS:
                                mundus_name = self.MUNDUS_ABILITY_IDS[ability_id]
                                logger.info(f"✓ Found mundus: {mundus_name} (ID: {ability_id}) for {player_name}")
                                
                                # Since we filtered by source_id, this is THIS PLAYER's mundus
                                return mundus_name
                    
                    logger.warning(f"No mundus buffs found in {len(auras)} auras for {player_name}")
                else:
                    logger.warning(f"No auras data in Buffs table for {player_name}")
            else:
                logger.warning(f"Failed to get Buffs table for {player_name}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get buffs for {player_name}: {e}")
            return None
    
    async def close(self):
        """Close the client connection."""
        if hasattr(self.client, 'close'):
            if asyncio.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close()
        logger.info("ESO Logs API client closed")
