import os
import sys
from enums.gba.games_enum import AvailableGames
from enums.app_enums import AvailableLanguages
from tools.user_selection import UserSelection
from services.translations_service import TranslationsService


class _ExitMenuException(Exception):
    """Raised immediately when the user presses ESC anywhere in the menu."""


class _GoBackException(Exception):
    """Raised when the user presses Backspace (on empty input) or '0' to go back."""


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

        try:
            while True:
                self.__clear_screen()
                if status_banner:
                    print(status_banner)
                    status_banner = None

                print("=" * 46)
                print(f"   {t('menu.title', lang=self.language.name)}")
                print("=" * 46)
                print(t("menu.options.start_app"))
                print(t("menu.options.test_grpc"))
                print(t("menu.options.change_language"))
                print()
                print(t("menu.hints.main"))

                choice = self.__prompt_choice(t("menu.prompts.select_option"), ["1", "2", "3"], allow_back=False)

                if choice == "3":
                    try:
                        status_banner = self.__select_language()
                    except _GoBackException:
                        continue

                elif choice == "1":
                    selection = self.__flow_start_app()
                    if selection is not None:
                        self.__clear_screen()
                        return selection

                elif choice == "2":
                    selection = self.__flow_test_grpc()
                    if selection is not None:
                        self.__clear_screen()
                        return selection

        except _ExitMenuException:
            self.__clear_screen()
            print(t("menu.messages.exiting"))
            return None
    # End Public Methods

    # Private Methods
    def __flow_start_app(self) -> UserSelection | None:
        while True:
            try:
                mode = self.__select_execution_mode()
            except _GoBackException:
                return None

            try:
                game = self.__select_game()
                return UserSelection(action=mode, game=game, language=self.language)
            except _GoBackException:
                continue

    def __flow_test_grpc(self) -> UserSelection | None:
        while True:
            try:
                test_mode = self.__select_grpc_test_mode()
            except _GoBackException:
                return None

            if test_mode == "grpc_test_loaded":
                return UserSelection(action=test_mode, game=None, language=self.language)

            try:
                game = self.__select_game()
                return UserSelection(action=test_mode, game=game, language=self.language)
            except _GoBackException:
                continue

    def __select_language(self) -> str:
        t = self.translator.translate
        self.__clear_screen()
        languages_list = list(AvailableLanguages)
        print(t("menu.headers.select_language"))
        for idx, lang in enumerate(languages_list, start=1):
            label = self.LANGUAGE_LABELS.get(lang, lang.name.replace("_", "-"))
            current_tag = t("menu.messages.current_tag") if lang == self.language else ""
            print(f"{idx}. {label}{current_tag}")
        print()
        print(t("menu.hints.sub"))

        valid_options = [str(i) for i in range(1, len(languages_list) + 1)]
        choice = self.__prompt_choice(t("menu.prompts.language"), valid_options, allow_back=True)

        self.language = languages_list[int(choice) - 1]
        self.translator.set_locale(self.language.name)

        selected_label = self.LANGUAGE_LABELS.get(self.language, self.language.name)
        return t("menu.messages.language_updated", language=selected_label)

    def __select_execution_mode(self) -> str:
        t = self.translator.translate
        self.__clear_screen()
        print(t("menu.headers.select_mode"))
        print(t("menu.modes.randomizer"))
        print(t("menu.modes.grpc_server"))
        print()
        print(t("menu.hints.sub"))

        choice = self.__prompt_choice(t("menu.prompts.mode"), ["1", "2"], allow_back=True)
        return "randomizer" if choice == "1" else "grpc_server"

    def __select_grpc_test_mode(self) -> str:
        t = self.translator.translate
        self.__clear_screen()
        print(t("menu.headers.select_test_mode"))
        print(t("menu.test_modes.loaded_game"))
        print(t("menu.test_modes.replace_game"))
        print()
        print(t("menu.hints.sub"))

        choice = self.__prompt_choice(t("menu.prompts.test_mode"), ["1", "2"], allow_back=True)
        return "grpc_test_loaded" if choice == "1" else "grpc_test_replace"

    def __select_game(self) -> AvailableGames:
        t = self.translator.translate
        self.__clear_screen()
        games_list = list(AvailableGames)
        print(t("menu.headers.select_game"))
        for idx, game in enumerate(games_list, start=1):
            display_name = game.name.replace("_", " ").title()
            print(f"{idx}. {display_name}")
        print()
        print(t("menu.hints.sub"))

        valid_options = [str(i) for i in range(1, len(games_list) + 1)]
        choice = self.__prompt_choice(t("menu.prompts.game"), valid_options, allow_back=True)
        return games_list[int(choice) - 1]

    def __prompt_choice(self, label: str, valid_options: list[str], allow_back: bool = True) -> str:
        options_str = "/".join(valid_options) if len(valid_options) <= 4 else f"1-{len(valid_options)}"
        while True:
            raw_value = self.__read_input_with_hotkeys(f"{label} [{options_str}]: ", allow_back=allow_back)
            if raw_value in valid_options:
                return raw_value
            print(self.translator.translate("menu.messages.invalid_option"))

    @staticmethod
    def __clear_screen() -> None:
        """Clear the terminal screen cleanly across Windows, macOS, and Linux."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def __read_input_with_hotkeys(prompt: str, allow_back: bool) -> str:
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
                    raise _ExitMenuException()

                if ch in ("\r", "\n"):
                    print()
                    value = "".join(buffer).strip()
                    if allow_back and value == "0":
                        raise _GoBackException()
                    return value

                if ch == "\x08":
                    if buffer:
                        buffer.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    elif allow_back:
                        print()
                        raise _GoBackException()
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
                        raise _ExitMenuException()
                    if ch in ("\r", "\n"):
                        sys.stdout.write("\r\n")
                        value = "".join(buffer).strip()
                        if allow_back and value == "0":
                            raise _GoBackException()
                        return value
                    if ch in ("\x7f", "\x08"):
                        if buffer:
                            buffer.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                        elif allow_back:
                            sys.stdout.write("\r\n")
                            raise _GoBackException()
                        continue
                    if ch.isprintable():
                        buffer.append(ch)
                        sys.stdout.write(ch)
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
