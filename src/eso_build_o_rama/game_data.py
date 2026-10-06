"""
Game data tables imported from the ESO Log Tail asset bundle.

The bundle (see docs/GAME_ASSET_BUNDLE.md) is imported into data/game/<update>/ and
gives this site what it used to keep in hand-typed tables: which skill line an
ability id belongs to, which lines are class lines, the mundus boon ids, and
ESO-Hub page paths for sets and mundus stones. Everything here is read-only and
offline; when no bundle has been imported, callers get None and fall back to the
legacy name-based behaviour.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GAME_DATA_DIR = PROJECT_ROOT / "data" / "game"
UPDATE_CONFIG_FILE = PROJECT_ROOT / "data" / "update_config.json"
ESO_HUB_BASE = "https://eso-hub.com"

TABLE_FILES = ("abilities.json", "skill_lines.json", "mundus.json", "sets.json")


class GameData:
    """Lookup tables for one game update, loaded from data/game/<update>/."""

    def __init__(
        self,
        update: str,
        abilities: Dict[str, dict],
        skill_lines: Dict[str, dict],
        mundus: Dict[str, dict],
        sets: Dict[str, dict],
        manifest: Optional[dict] = None,
    ):
        self.update = update
        self.abilities = abilities          # "183006" -> {name, icon, skill_line, class, type, ...}
        self.skill_lines = skill_lines      # "Herald of the Tome" -> {category, class, ability_ids, ...}
        self.mundus = mundus                # "13940" -> {name, game_name, icon, esohub}
        self.sets = sets                    # "270" -> {name, type, max_equip, esohub, ...}
        self.manifest = manifest or {}

        # Scribed skills reach us with ESO Logs pseudo-ids; only the grimoire icon
        # identifies their (non-class) line.
        self.grimoire_lines: Dict[str, str] = {
            stem: line_name
            for line_name, line in skill_lines.items()
            for stem in (line.get("grimoire_icon_stems") or [])
        }
        # The 21 slottable class lines. The bundle also carries passive-only
        # "Class Mastery (<class>)" lines with category "class"; nothing in them
        # can be slotted, so they never count towards a build.
        self.class_lines: Dict[str, str] = {
            name: line.get("class")
            for name, line in skill_lines.items()
            if line.get("category") == "class" and not name.startswith("Class Mastery")
        }
        self._native_lines: Dict[str, List[str]] = {}
        for name, cls in self.class_lines.items():
            if cls:
                self._native_lines.setdefault(cls.lower(), []).append(name)
        for lines in self._native_lines.values():
            lines.sort()
        self._mundus_by_name = {entry.get("name", ""): entry for entry in mundus.values()}
        self._sets_by_name = {entry.get("name", "").lower(): entry for entry in sets.values()}

    # ------------------------------------------------------------------ loading

    @staticmethod
    def available_updates() -> List[str]:
        """Update tags that have an imported bundle, oldest first."""
        if not GAME_DATA_DIR.is_dir():
            return []
        return sorted(
            p.name for p in GAME_DATA_DIR.iterdir()
            if p.is_dir() and all((p / f).is_file() for f in TABLE_FILES)
        )

    @staticmethod
    def _configured_update() -> Optional[str]:
        try:
            with open(UPDATE_CONFIG_FILE, encoding="utf-8") as fh:
                return json.load(fh).get("current_update") or None
        except (OSError, ValueError):
            return None

    @classmethod
    def load(cls, update: Optional[str] = None) -> Optional["GameData"]:
        """Load the tables for *update* (default: current_update from update_config.json).

        Falls back to the newest imported bundle when the requested update has none,
        and returns None when nothing has been imported at all.
        """
        available = cls.available_updates()
        if not available:
            logger.warning("No game data bundle under %s; skill lines and links use the legacy name tables",
                           GAME_DATA_DIR)
            return None
        wanted = update or cls._configured_update()
        chosen = wanted if wanted in available else available[-1]
        if wanted and chosen != wanted:
            logger.warning("No game data for %s; using %s", wanted, chosen)
        try:
            return _load_cached(chosen)
        except (OSError, ValueError) as e:
            logger.warning("Game data %s is unreadable (%s); using the legacy name tables", chosen, e)
            return None

    @classmethod
    def from_directory(cls, directory: Path, update: Optional[str] = None) -> "GameData":
        directory = Path(directory)
        tables = {}
        for filename in TABLE_FILES:
            with open(directory / filename, encoding="utf-8") as fh:
                data = json.load(fh)
            key = filename[:-5]
            tables[key] = data.get(key, data) if isinstance(data, dict) else data
        manifest = {}
        manifest_file = directory / "manifest.json"
        if manifest_file.is_file():
            with open(manifest_file, encoding="utf-8") as fh:
                manifest = json.load(fh)
        return cls(
            update=update or manifest.get("update") or directory.name,
            abilities=tables["abilities"],
            skill_lines=tables["skill_lines"],
            mundus=tables["mundus"],
            sets=tables["sets"],
            manifest=manifest,
        )

    # ------------------------------------------------------------------ lookups

    def ability(self, ability_id) -> Optional[dict]:
        if ability_id is None:
            return None
        return self.abilities.get(str(ability_id))

    def resolve(self, ability_id, icon: str = "") -> Tuple[bool, Optional[str]]:
        """(known, skill_line) for a slotted ability.

        known is True when the game id is in the table (even with no skill line,
        as for a mythic's granted skill) or the icon is a scribing grimoire's.
        skill_line may be a non-class line; use is_class_line().
        """
        entry = self.ability(ability_id)
        if entry is not None:
            return True, entry.get("skill_line")
        if icon:
            line = self.grimoire_lines.get(icon.lower())
            if line is not None:
                return True, line
        return False, None

    def skill_line_for(self, ability_id, icon: str = "") -> Optional[str]:
        """Skill line of a slotted ability, or None when unknown or line-less."""
        return self.resolve(ability_id, icon)[1]

    def is_class_line(self, skill_line: Optional[str]) -> bool:
        return bool(skill_line) and skill_line in self.class_lines

    def class_of_line(self, skill_line: str) -> Optional[str]:
        return self.class_lines.get(skill_line)

    def native_lines(self, class_name: str) -> List[str]:
        """The three class lines a character of *class_name* is born with (sorted).

        Case-insensitive because ESO Logs spells it "DragonKnight".
        """
        if not class_name:
            return []
        return list(self._native_lines.get(class_name.strip().lower(), []))

    def mundus_esohub_url(self, mundus_name: str) -> Optional[str]:
        entry = self._mundus_by_name.get(mundus_name)
        path = entry.get("esohub") if entry else None
        return f"{ESO_HUB_BASE}{path}" if path else None

    def set_esohub_url(self, set_name: str = "", set_id=None) -> Optional[str]:
        entry = None
        if set_id not in (None, 0, "0"):
            entry = self.sets.get(str(set_id))
        if entry is None and set_name:
            entry = self._sets_by_name.get(set_name.strip().lower())
        path = entry.get("esohub") if entry else None
        return f"{ESO_HUB_BASE}{path}" if path else None


@lru_cache(maxsize=4)
def _load_cached(update: str) -> GameData:
    data = GameData.from_directory(GAME_DATA_DIR / update, update=update)
    logger.info(
        "Loaded game data %s: %d abilities, %d skill lines, %d sets (client %s)",
        update, len(data.abilities), len(data.skill_lines), len(data.sets),
        data.manifest.get("game", {}).get("version", "unknown"),
    )
    return data
