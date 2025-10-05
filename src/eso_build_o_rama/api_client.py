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
        # Input validation
        if not isinstance(zone_id, int) or zone_id <= 0:
            raise ValueError("zone_id must be a positive integer")
        if limit <= 0 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if difficulty is not None and (difficulty < 1 or difficulty > 3):
            raise ValueError("difficulty must be between 1 and 3")
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
        
        if not encounter_id:
            logger.error("encounter_id is required for rankings")
            return []
        
        logger.info(f"Fetching top {limit} unique ranked logs for zone {zone_id}, encounter {encounter_id}")
        
        try:
            # Use LogsOnly leaderboard to get rankings with report codes
            # Note: This returns all available logs (typically 8-12 unique reports)
            # We'll take the top N after deduplication
            query_logs_only = '''
            query GetTopRankedReports($encounterID: Int!) {
              worldData {
                encounter(id: $encounterID) {
                  characterRankings(
                    metric: dps
                    leaderboard: LogsOnly
                  )
                }
              }
            }
            '''
            
            result = await self._retry_on_rate_limit(
                self.client.execute,
                query=query_logs_only,
                variables={"encounterID": encounter_id}
            )
            
            if result.status_code != 200:
                logger.error(f"API request failed with status {result.status_code}")
                return []
            
            data = result.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            character_rankings = data['data']['worldData']['encounter']['characterRankings']
            # LogsOnly returns data as JSON directly, not in a rankings sub-field
            if isinstance(character_rankings, dict):
                rankings = character_rankings.get('rankings', [])
            elif isinstance(character_rankings, list):
                rankings = character_rankings
            else:
                logger.error(f"Unexpected characterRankings format: {type(character_rankings)}")
                return []
            
            # Extract unique report codes (keep top DPS per report)
            report_map = {}
            for ranking in rankings:
                report = ranking.get('report', {})
                code = report.get('code')
                
                if code:  # Only include rankings with report codes
                    if code not in report_map or ranking['amount'] > report_map[code]['amount']:
                        report_map[code] = {
                            "name": ranking['name'],
                            "class": ranking['class'],
                            "spec": ranking.get('spec', 'Unknown'),
                            "amount": ranking['amount'],
                            "report": {
                                "code": code,
                                "startTime": report.get('startTime', 0),
                                "fightID": report.get('fightID', 1)
                            }
                        }
            
            # Sort by DPS and take top N
            sorted_rankings = sorted(report_map.values(), key=lambda x: x['amount'], reverse=True)
            top_rankings = sorted_rankings[:limit]
            
            logger.info(f"Found {len(top_rankings)} top-ranked reports")
            return top_rankings
            
        except Exception as e:
            logger.error(f"Error fetching top logs: {e}")
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
              gameVersion
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
            result = await self._retry_on_rate_limit(
                self.client.get_report_by_code,
                report_code
            )
            
            if result and hasattr(result, 'report_data') and hasattr(result.report_data, 'report'):
                report_obj = result.report_data.report
                
                report = {
                    "code": getattr(report_obj, 'code', report_code),
                    "title": getattr(report_obj, 'title', 'Unknown Title'),
                    "startTime": getattr(report_obj, 'start_time', 0),
                    "endTime": getattr(report_obj, 'end_time', 0),
                    "gameVersion": getattr(report_obj, 'game_version', None),
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
    
    async def close(self):
        """Close the client connection."""
        if hasattr(self.client, 'close'):
            if asyncio.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close()
        logger.info("ESO Logs API client closed")
