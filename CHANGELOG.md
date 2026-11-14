# Changelog

All notable changes to **AdvanceR GeN** will be documented in this file.

## [v1.0.0] - 2026-11-05

### Added
- **Multi-Game Configuration Architecture**: Implemented JSON-based configuration files (`games/fire-red.json`, `games/radical-red.json`, and `games/global_config.json`) alongside `settings.py` to dynamically load ROM offsets, memory boundaries, and randomizer flags.
- **GBA Binary Decryption & Pointer Engine**: Added `helpers/consoles_helper.py` and `helpers/pointers_helper.py` to translate Little Endian GBA memory pointers (`0x08000000` range), decode proprietary GBA character tables, traverse map banks/headers, and locate safe `0xFF` free space blocks for binary injection.
- **Overworld Pokéball Item Randomizer**: Added `helpers/instances_helper.py` and `helpers/map_helper.py` to scan map NPC events, identify ground Pokéball item scripts (filtering out starter Pokéballs), generate valid random items, and repoint custom XSE bytecode scripts into free ROM space.
- **Supported Games**: Added initial randomization support for **Pokémon FireRed (16MB)** and **Pokémon Radical Red v4.1 (32MB)**.
- **Project Documentation & Licensing**: Added `README.md` with quick start instructions using `uv` and full configuration property references, along with an MIT `LICENSE` and Python `.gitignore`.

### Fixed
- **Documentation**: Corrected minor wording and typos.