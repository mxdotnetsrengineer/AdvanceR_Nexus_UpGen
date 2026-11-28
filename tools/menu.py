import os
import sys
from enums.gba.games_enum import AvailableGames
from enums.app_enums import AvailableLanguages, NavAction
from tools.user_selection import UserSelection
from services.translations_service import TranslationsService

class ConsoleMenu:
    LANGUAGE_LABELS: dict[AvailableLanguages, str] = {
        AvailableLanguages.EN_US: "English (US)",
        AvailableLanguages.ES_MX: "Español (MX)",
    }

    def __init__(
        self,
        translator: TranslationsService,
        default_language: AvailableLanguages = AvailableLanguages.EN_US,
    ) -> None:
        self.translator = translator
        self.language = default_language
        self.translator.set_locale(self.language)

    # Public Methods
    def run(self) -> UserSelection | None:
        """Display the main menu loop supporting ESC to exit and Backspace/0 to return."""
        t = self.translator.translate
        status_banner: str | None = None

        while True:
            self._clear_screen()
            if status_banner:
                print(status_banner)
                status_banner = None

            print("=" * 46)
            print(f"   {t('menu.title', lang=self.language.name)}")
            print("=" * 46)
            print(t("menu.options.start_app"))
            print(t("menu.options.test_grpc"))
            print(t("menu.options.fastapi_server"))
            print(t("menu.options.run_tests"))
            print(t("menu.options.change_language"))
            print()
            print(t("menu.hints.main"))

            choice = self._prompt_choice(t("menu.prompts.select_option"), ["1", "2", "3", "4", "5" ], allow_back=False)
            if choice is NavAction.EXIT:
                return self._exit_menu()

            match choice:
                case "1":
                    result = self._flow_start_app()
                case "2":
                    result = self._flow_test_grpc()
                case "3":
                    result = UserSelection(action="fastapi_server", game=None, language=self.language)
                case "4":
                    pytest_action = self._select_pytest_mode()
                    if isinstance(pytest_action, NavAction):
                        result = pytest_action
                    else:
                        result = UserSelection(action=pytest_action, game=None, language=self.language)
                case "5":
                    lang_result = self._select_language()
                    if lang_result is NavAction.EXIT:
                        return self._exit_menu()
                    if isinstance(lang_result, str):
                        status_banner = lang_result
                    continue

            if result is NavAction.EXIT:
                return self._exit_menu()
            if isinstance(result, UserSelection):
                self._clear_screen()
                return result
    # End Public Methods

    # Private Methods
    def _exit_menu(self) -> None:
        self._clear_screen()
        print(self.translator.translate("menu.messages.exiting"))
        return None
    
    def _flow_start_app(self) -> UserSelection | None:
        while True:
            mode = self._select_execution_mode()
            if isinstance(mode, NavAction):
                return mode

            game = self._select_game()
            if game is NavAction.EXIT:
                return NavAction.EXIT
            if game is NavAction.BACK:
                continue

            return UserSelection(action=mode, game=game, language=self.language)

    def _flow_test_grpc(self) -> UserSelection | NavAction:
        while True:
            test_mode = self._select_grpc_test_mode()
            if isinstance(test_mode, NavAction):
                return test_mode

            if test_mode == "grpc_test_loaded":
                return UserSelection(action=test_mode, game=None, language=self.language)

            game = self._select_game()
            if game is NavAction.EXIT:
                return NavAction.EXIT
            if game is NavAction.BACK:
                continue

            return UserSelection(action=test_mode, game=game, language=self.language)

    def _select_language(self) -> str | NavAction:
        t = self.translator.translate
        self._clear_screen()
        languages_list = list(AvailableLanguages)
        print(t("menu.headers.select_language"))
        for idx, lang in enumerate(languages_list, start=1):
            label = self.LANGUAGE_LABELS.get(lang, lang.name.replace("_", "-"))
            current_tag = t("menu.messages.current_tag") if lang == self.language else ""
            print(f"{idx}. {label}{current_tag}")
        print()
        print(t("menu.hints.sub"))

        valid_options = [str(i) for i in range(1, len(languages_list) + 1)]
        choice = self._prompt_choice(t("menu.prompts.language"), valid_options, allow_back=True)
        if isinstance(choice, NavAction):
            return choice

        self.language = languages_list[int(choice) - 1]
        self.translator.set_locale(self.language.name)

        selected_label = self.LANGUAGE_LABELS.get(self.language, self.language.name)
        return t("menu.messages.language_updated", language=selected_label)

    def _select_execution_mode(self) -> str | NavAction:
        t = self.translator.translate
        self._clear_screen()
        print(t("menu.headers.select_mode"))
        print(t("menu.modes.randomizer"))
        print(t("menu.modes.grpc_server"))
        print()
        print(t("menu.hints.sub"))

        choice = self._prompt_choice(t("menu.prompts.mode"), ["1", "2"], allow_back=True)
        if isinstance(choice, NavAction):
            return choice
        return "randomizer" if choice == "1" else "grpc_server"

    def _select_grpc_test_mode(self) -> str | NavAction:
        t = self.translator.translate
        self._clear_screen()
        print(t("menu.headers.select_test_mode"))
        print(t("menu.test_modes.loaded_game"))
        print(t("menu.test_modes.replace_game"))
        print()
        print(t("menu.hints.sub"))

        choice = self._prompt_choice(t("menu.prompts.test_mode"), ["1", "2"], allow_back=True)
        if isinstance(choice, NavAction):
            return choice
        
        return "grpc_test_loaded" if choice == "1" else "grpc_test_replace"

    def _select_pytest_mode(self) -> str | NavAction:
        t = self.translator.translate
        self._clear_screen()
        print(t("menu.headers.select_pytest_mode"))
        print(t("menu.pytest_modes.all"))
        print(t("menu.pytest_modes.unit"))
        print(t("menu.pytest_modes.integration"))
        print(t("menu.pytest_modes.coverage"))
        print()
        print(t("menu.hints.sub"))

        choice = self._prompt_choice(t("menu.prompts.pytest_mode"), ["1", "2", "3", "4"], allow_back=True)
        if isinstance(choice, NavAction):
            return choice
        
        mapping = {
            "1": "pytest_all",
            "2": "pytest_unit",
            "3": "pytest_integration",
            "4": "pytest_cov",
        }
        return mapping[choice]

    def _select_game(self) -> AvailableGames | NavAction:
        t = self.translator.translate
        self._clear_screen()
        games_list = list(AvailableGames)
        print(t("menu.headers.select_game"))
        for idx, game in enumerate(games_list, start=1):
            display_name = game.name.replace("_", " ").title()
            print(f"{idx}. {display_name}")
        print()
        print(t("menu.hints.sub"))

        valid_options = [str(i) for i in range(1, len(games_list) + 1)]
        choice = self._prompt_choice(t("menu.prompts.game"), valid_options, allow_back=True)
        if isinstance(choice, NavAction):
            return choice
        return games_list[int(choice) - 1]

    def _prompt_choice(self, label: str, valid_options: list[str], allow_back: bool = True) -> str:
        options_str = "/".join(valid_options) if len(valid_options) <= 4 else f"1-{len(valid_options)}"
        while True:
            raw_value = self._read_input_with_hotkeys(f"{label} [{options_str}]: ", allow_back=allow_back)
            if isinstance(raw_value, NavAction) or raw_value in valid_options:
                return raw_value
            print(self.translator.translate("menu.messages.invalid_option"))

    @staticmethod
    def _clear_screen() -> None:
        """Clear the terminal screen cleanly across Windows, macOS, and Linux."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _read_input_with_hotkeys(prompt: str, allow_back: bool) -> str | NavAction:
        """Read user input character-by-character to intercept ESC and Backspace."""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        buffer: list[str] = []

        try:
            import msvcrt

            while True:
                ch = msvcrt.getwch()

                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    continue

                if ch == "\x1b":
                    print()
                    return NavAction.EXIT
                if ch in ("\r", "\n"):
                    print()
                    value = "".join(buffer).strip()
                    if allow_back and value == "0":
                        return NavAction.BACK
                    return value

                if ch == "\x08":
                    if buffer:
                        buffer.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    elif allow_back:
                        print()
                        return NavAction.BACK
                    continue

                if ch.isprintable():
                    buffer.append(ch)
                    sys.stdout.write(ch)
                    sys.stdout.flush()

        except ImportError:
            import termios  # type: ignore[import-not-found]
            import tty  # type: ignore[import-not-found]

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch == "\x1b":
                        sys.stdout.write("\r\n")
                        return NavAction.EXIT
                    if ch in ("\r", "\n"):
                        sys.stdout.write("\r\n")
                        value = "".join(buffer).strip()
                        if allow_back and value == "0":
                            return NavAction.BACK
                        return value
                    if ch in ("\x7f", "\x08"):
                        if buffer:
                            buffer.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                        elif allow_back:
                            sys.stdout.write("\r\n")
                            return NavAction.BACK
                        continue
                    if ch.isprintable():
                        buffer.append(ch)
                        sys.stdout.write(ch)
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
