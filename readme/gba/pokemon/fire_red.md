Below is a reference example of how these constants are structured inside the configuration file:

#### Identification & File Paths
* **`GAME_NAME`** (`str`): Descriptive title and file size displayed in initialization logs (e.g., `"Pokemon FireRed (16MB)"`).
* **`ORIGINAL_GAME`** (`str`): Exact filename of the clean input `.gba` game file located in the root directory.
* **`MODIFIED_GAME`** (`str`): Designated output filename for the updated/randomized `.gba` game file.

#### Memory Management & Free Space
* **`MAX_ROM_SIZE`** (`hex str`): Maximum allowed file size limit in bytes for the game binary.
* **`FREE_SPACE_START`** (`hex str`): Starting file offset where unused padding (bytes filled with `0xFF`) is safe to overwrite with newly generated scripts. `GBAMemoryService` tracks `free_space` dynamically from this address so consecutive binary writes never overlap.

#### Map Banks & Map Names
* **`BANK_TABLE_OFFSET`** (`hex str`): Hardcoded physical file offset pointing directly to the root master map bank table.
* **`BANK_TABLE_BANKS_POSITION`** (`int`): Index within the root master table holding the primary pointer to the active map bank list.
* **`MAP_NAMES_TABLE_OFFSET`** (`hex str`): Internal pointer table offset mapping out the text addresses for region/location names.
* **`REGION_MAP_BYTE`** (`int`): Byte offset within each map header (`map_header`) where the `regionMapSectionId` (map name ID) is stored.
* **`GAME_START`** (`hex str`): Base index shift for map names in the text table (e.g., `0x58` aligns entry `0` with *Pallet Town* in *FireRed*).
* **`MAX_BANKS`** (`int`): Upper limit of map banks the parser loop iterates through during reverse engineering.
* **`MAX_MAPS_PER_BANK`** (`int`): Maximum number of individual maps evaluated sequentially per bank.

#### Items & Pokéball Events
* **`ITEMS_POINTER_OFFSET`** (`hex str`): File address containing the master pointer to the global item structure table.
* **`ITEM_STRUCT_SIZE`** (`int`): Structural size in bytes occupied by a single item entry inside the GBA memory layout (`44` bytes in Gen III).
* **`MAX_ITEM_ID`** (`int`): Maximum upper index boundary for valid item IDs eligible for randomization (`374` in vanilla *FireRed*; `748` in *Radical Red*).
* **`POKEBALL_SPRITE_ID`** (`int`): Overworld sprite index (`92`) assigned to visible Pokéball items sitting on floor maps.

#### UI & Logical Keyboards
* **`CHARACTER_BYTE_SIZE`** (`int`): Number of bytes per character row/block in the game's naming screen structure.
* **`DEFAULT_UI_KEYBOARD_SEPARATORS`** (`list[str]`): Sequence of hexadecimal control bytes (e.g., `["0xFC", "0x11"]`) preceding each character in the visual table to define spacing and layout formatting.
* **`UPPER_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the uppercase (`A-Z`) logical character array begins.
* **`LOWER_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the lowercase (`a-z`) logical character array begins.
* **`OTHERS_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the numbers and punctuation (`0-9`, `!`, `?`, etc.) logical character array begins.

#### Pokémon Base Stats & Evolutions
* **`POKEMON_STATS_OFFSET`** (`hex str`): File address containing the offset to the pokemon base stats table (`0x0001BC` in *FireRed* / *Radical Red*).
* **`POKEMON_STRUCT_SIZE`** (`int`): Byte size of a single Pokémon base stats structure (`28` bytes in Gen III).
* **`POKEMON_NAMES_OFFSET`** (`hex str`): File address containing the offset to the pokemon name strings table (`0x000144` in *FireRed* / *Radical Red*).
* **`POKEMON_NAME_LENGTH`** (`int`): Maximum character length allocated per Pokémon pokemon name (`11` bytes).
* **`MAX_POKEMON_SPECIES`** (`int`): Total number of pokemon entries iterated when building the stats database (`412` in *FireRed*; `1376` in *Radical Red*).
* **`POKEMON_EVOLUTIONS_OFFSET`** (`list[hex str]`): List of physical file offsets pointing to evolution data tables (`["0x259754"]` in *FireRed*; `["0x17CD9B0"]` in *Radical Red*) used to recursively calculate evolution stages and detect Mega Evolutions.
* **`EVOS_PER_MON`** (`int`): Maximum number of evolution entries stored per pokemon (`5` in *FireRed*; `16` in *Radical Red*).
* **`EVO_ENTRY_SIZE`** (`int`): Byte size of each individual evolution entry (`8` bytes).

#### Wild Pokémon Encounters
* **`WILD_POKEMON_OFFSET`** (`list[hex str]`): List of physical file offsets pointing to wild encounter header tables (`["0x3C9CB8"]` in *FireRed*; `["0x1166428", "0x1166AB8"]` in *Radical Red*).
* **`WILD_HEADER_STRUCT_SIZE`** (`int`): Byte size of each map wild encounter header entry (`20` bytes).
* **`WILD_GRASS_SLOT_COUNT`** (`int`): Number of encounter slots inside a wild grass table (`12` slots).
* **`WILD_SLOT_STRUCT_SIZE`** (`int`): Byte size of an individual wild encounter slot containing min/max levels and pokemon ID (`4` bytes).