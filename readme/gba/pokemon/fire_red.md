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
* **`BANKS_TO_PRINT`** (`int`): Upper limit of map banks the parser loop iterates through during reverse engineering.
* **`MAPS_PER_BANK_TO_PRINT`** (`int`): Maximum number of individual maps evaluated sequentially per bank.

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