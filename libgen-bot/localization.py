import json


class Localization:

    supported_languages = ["en", "it"]

    def __init__(self) -> None:
        self.languages = self.get_translations()

    def get_translations(self):
        with open("libgen-bot/translations.json", encoding="utf-8") as f:
            return json.load(f)

    def get_string(self, string, language, *args):
        translations = self.languages.get(language) or self.languages.get("en")
        return translations.get(string).format(*args)
