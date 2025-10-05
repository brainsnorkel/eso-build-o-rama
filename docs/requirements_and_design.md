# Initial Design

## What it does

Once per week

Scan the five highest ranked public logs repoorts for each trial on esologs.

For each "boss fight" collect build information for all players:
* Player handle and character name
* Mundus ("Boon:" buff)
* Gear, with gear trait and type of enchantment.
* Ability bars
* DPS total and % contribution in this boss fight
* Any "blue CP" that can be inferred
* URL to the player summary page for that fight (to credit them)
* Game update level and date of this fight (e.g. U48 20251003)
- Remove any player with missing gear or skill information

Determine the subclasses of each collected character using the same mechanism as https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary 
If any of the three possible subclasses aren't known then substitute 'x' as the subclass name.

Establish how many slots of each set this character is wearing in total, and on each ability bar:
* Main bar weapons accrue to the set piece total for bar 1 (Bar1: head, shoulder, hands, legs, chest, belt, boots, neck, ring1, ring2, main hand, off hand (can be a staff or 2H weapon in main hand that counts as 2 pc/slots with no off hand) )
* Backup bar weapons accrue to the set piece total for bar 2 (Bar2: head, shoulder, hands, legs, chest, belt, boots, neck, ring1, ring2, backup main hand, backup off hand (can be a staff or 2H weapon in backup main hand that counts as 2 pc/slots with no backup off hand) )

A "build" for purposes of selecting an example character, is a subclass combination (e.g. Assassination/Herald of the Tome/Ardent Fire) and two five piece sets on one or two of the player's bars.  The tool could create a "slug" with sorted abbreviated subclasses and sets to identify common build. e.g. ass-ardent-herald-ansuuls-torment-deadly-strike

If a "build" appears five or more times in the collected builds for this fight then it is a "common build"

* Pick the the highest DPS character with each unique common build for consideration to publish
  
For each common build (if this build hasn't already been published for this update): 
* publish a page with a path that is the build slug from above prefixed with the update. e.g. u48-ass-ardent-herald-ansuuls-torment-deadly-strike:
* Title/heading is the full known subclass name and set names
* Fight name (Trial Name + Boss)
* The highest DPS player and character name this informaion is drawn from e.g. `@brainsnorkel` `Beam Hal` with a link to the ESOLOGS summary for that player.
* An icon-based display of the slotted abilities for that player with a row for bar 1 and a row for bar 2. 
* Abilities shall link to the appropriate page at uesp.net
* Mundus: {player's mundus}
* A table with each slot and the set piece that occupies it, its trait and enchant. 
* A table with known "blue cps"

The tool will create an index page for showing all builds with headings per trial and boss.

## Platformm, Performance and Cost

I would like this tool to be very cheap to run. Maybe a weekly lambda batch job that publishes static files (with minimal JS) to S3, use of Cloudflare's publishing capabilities. Serve via https from a yet to be acquired domain name. 

Develop and test locally, then push to a `https://test.{whatever domain name}` before migrating to `http://{whatever domain name}`


## Development approach

Prioritise getting a rough prototype working on this local machine.
Build sensible automated tests as we go.


## Technical constraints
* Do not use web scraping to access ESOlogs, only the API


## Reference material

This will show how to get sets, abilities and other data from the esologs api.

https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary

General Elder Scrolls Online reference:
https://en.uesp.net/wiki/Online:Online

Set data:
https://github.com/Baertram/LibSets/tree/LibSets-reworked/LibSets/Data (*.xlsm is the latest spreadsheet of sets, LibSets_Data_All.lua is an LUA option)

Ability bar icons:
https://github.com/sheumais/esoskillbarbuilder



## Credits

The published page should credit uesp.net, esologs.com, [LibSets](https://www.esoui.com/downloads/info2241-LibSets.html) by Baertram, https://github.com/sheumais/ for all their resources and advice, and https://www.elderscrollsonline.com ZeniMax Media Inc for their excellent game and support for community. 


## Initial API Secrets

In .env

## Copyright 

* https://github.com/brainsnorkel 2025