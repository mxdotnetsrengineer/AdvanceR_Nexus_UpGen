from operator import attrgetter
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from helpers.gba.pokemon.gba_pokemon_helper import MEGA_EVO_METHODS
from decorators.app_decorators import when_enabled
from services.config_service import ConfigService
from services.log_service import LogService
from services.gba.memory_service import GBAMemoryService

class StatsService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,

        
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.stats: list[CompiledBaseStats] = []

        self.max_species = self.config.get("MAX_POKEMON_SPECIES")
        self.name_length = self.config.get("POKEMON_NAME_LENGTH")
        self.evos_per_mon = self.config.get("EVOS_PER_MON")       
        self.evo_entry_size = self.config.get("EVO_ENTRY_SIZE")   
        self.include_megas = self.config.get("INCLUDE_MEGA_EVOLUTIONS")

    @when_enabled("BASE_STATS", default=True)
    async def get_all_species_data(self, game_file: bytearray) -> list[CompiledBaseStats]:
        stats_ptr_offset = self.config.get("POKEMON_STATS_OFFSET")
        names_ptr_offset = self.config.get("POKEMON_NAMES_OFFSET")
        raw_evos_offsets = self.config.get("POKEMON_EVOLUTIONS_OFFSET")
        struct_size = self.config.get("POKEMON_STRUCT_SIZE")

        self.log.raw("=" * 80)
        self.log.info(f"Iniciando lectura de tabla Pokémon desde puntero: {hex(stats_ptr_offset)}")
        self.log.raw("=" * 80)

        stats_table_offset = self.memory.pointer_to_offset(game_file, stats_ptr_offset)
        names_table_offset = self.memory.pointer_to_offset(game_file, names_ptr_offset)

        if not isinstance(raw_evos_offsets, list):
            raw_evos_offsets = [raw_evos_offsets]
        
        evos_table_offsets: list[int] = [
            int(off, 16) if isinstance(off, str) else off
            for off in raw_evos_offsets
        ]

        if not stats_table_offset or not names_table_offset or not evos_table_offsets:
            self.log.info("No se encontraron offsets válidos para stats, nombres o evoluciones.")
            return []

        evos_hex_str = ", ".join(hex(off) for off in evos_table_offsets)
        self.log.info(
            f"Tabla de Stats en: {hex(stats_table_offset)} | "
            f"Tabla de Nombres en: {hex(names_table_offset)} | "
            f"Tablas de Evoluciones en: [{evos_hex_str}]"
        )
        self.log.raw("-" * 80)

        processed: dict[int, CompiledBaseStats] = {}

        for evos_table_offset in evos_table_offsets:
            for species_id in range(self.max_species):
                if species_id in processed:
                    continue

                self._allocate_family_recursive(
                    game_file=game_file,
                    stats_table_offset=stats_table_offset,
                    names_table_offset=names_table_offset,
                    evos_table_offset=evos_table_offset,
                    species_id=species_id,
                    struct_size=struct_size,
                    stage=1,
                    processed=processed,
                )

        self.stats.sort(key=attrgetter("bst"))

        for stat in self.stats:
            self.log.info(
                f"ID #{stat.id:03d} - {stat.name:<10} (Etapa {stat.evolution_stage}) ({stat.offset_hex}) | "
                f"BST:{stat.bst:3d} [HP:{stat.hp:3d} ATK:{stat.attack:3d} DEF:{stat.defense:3d} "
                f"SPD:{stat.speed:3d} SPA:{stat.sp_attack:3d} SPD:{stat.sp_defense:3d}] | "
                f"Tipos: {stat.type_1}/{stat.type_2} | "
                f"Habilidades: {stat.ability_1}/{stat.ability_2} | "
                f"Ratio: {stat.catch_rate}"
            )

    def _allocate_family_recursive(
        self,
        game_file: bytearray,
        stats_table_offset: int,
        names_table_offset: int,
        evos_table_offset: int,
        species_id: int,
        struct_size: int,
        stage: int,
        processed: dict[int, CompiledBaseStats],
        ancestors: set[int] | None = None,
        is_mega: bool = False,
    ) -> None:
        if ancestors is None:
            ancestors = set()

        # Cortar ciclos infinitos (ej. cambios de forma A <-> B o datos corruptos)
        if species_id in ancestors or stage > 5:
            return

        if species_id in processed:
            existing_pokemon = processed[species_id]
            if is_mega:
                existing_pokemon.is_mega = True
            if stage > existing_pokemon.evolution_stage:
                existing_pokemon.evolution_stage = stage
                ancestors.add(species_id)
                for evo_id, evo_is_mega in self._get_species_evolutions(game_file, evos_table_offset, species_id):
                    self._allocate_family_recursive(
                        game_file, stats_table_offset, names_table_offset, evos_table_offset,
                        evo_id, struct_size, stage + 1, processed, ancestors, evo_is_mega
                    )
                ancestors.remove(species_id)
            return

        stats_data = self._allocate_stats_data(
            game_file, stats_table_offset, names_table_offset, species_id, struct_size, stage,is_mega
        )
        if stats_data is None:
            return

        processed[species_id] = stats_data
        self.stats.append(stats_data)

        ancestors.add(species_id)
        for evo_id, evo_is_mega in self._get_species_evolutions(game_file, evos_table_offset, species_id):
            self._allocate_family_recursive(
                game_file, stats_table_offset, names_table_offset, evos_table_offset,
                evo_id, struct_size, stage + 1, processed, ancestors, evo_is_mega
            )
        ancestors.remove(species_id)

    def _get_species_evolutions(
        self,
        game_file: bytearray,
        evos_table_offset: int,
        species_id: int,
    ) -> list[int]:
        block_size = self.evos_per_mon * self.evo_entry_size
        base_offset = self.memory.get_struct_offset(evos_table_offset, species_id, block_size)

        evolutions: list[int] = []
        for i in range(self.evos_per_mon):
            entry_offset = base_offset + (i * self.evo_entry_size)
            method = self.memory.read_u16(game_file, entry_offset)

            if method == 0:
                break

            is_mega_evo = method in MEGA_EVO_METHODS
            if not self.include_megas and is_mega_evo:
                continue
                        
            target_species = self.memory.read_u16(game_file, entry_offset + 4)
            if 0 < target_species < self.max_species and target_species != species_id:
                evolutions.append((target_species, is_mega_evo))

        return evolutions


    def _allocate_stats_data(
        self,
        game_file: bytearray,
        stats_table_offset: int,
        names_table_offset: int,
        species_id: int,
        struct_size: int,
        evolution_stage: int = 1,
        is_mega: bool = False
    ) -> CompiledBaseStats | None:
        species_struct_offset = self.memory.get_struct_offset(stats_table_offset, species_id, struct_size)
        data = game_file[species_struct_offset : species_struct_offset + struct_size]
        bst = sum(data[0:6])

        if bst == 0:
            return None

        name_string_offset = self.memory.get_struct_offset(names_table_offset, species_id, self.name_length)
        pokemon_name = self.memory.read_string(game_file, name_string_offset, max_length=self.name_length, fallback="")

        if pokemon_name in ("", "?", "??????????"):
            return None

        pokemon = CompiledBaseStats(
            id=species_id, name=pokemon_name, offset=species_struct_offset,
            hp=data[0], attack=data[1], defense=data[2], speed=data[3], sp_attack=data[4], sp_defense=data[5], bst=bst,
            type_1=data[6], type_2=data[7], catch_rate=data[8], base_exp=data[9],
            ev_yield_raw=self.memory.read_u16(game_file, species_struct_offset + 10),
            item_1=self.memory.read_u16(game_file, species_struct_offset + 12),
            item_2=self.memory.read_u16(game_file, species_struct_offset + 14),
            gender_ratio=data[16], egg_cycles=data[17], base_friendship=data[18],
            growth_rate=data[19], egg_group_1=data[20], egg_group_2=data[21],
            ability_1=data[22], ability_2=data[23], safari_zone_flee_rate=data[24], body_color_and_flip=data[25],
            evolution_stage=evolution_stage,is_mega=is_mega
        )

        return pokemon