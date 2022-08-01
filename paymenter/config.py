# <--- Import --->
import json

# <--- Import from --->

# <--- Config class --->
class ConfigManager:
    config_file = ""
    def __init__(self, config_file: str = "paymenter/keys.json") -> None:
        self.config_file = config_file

    def load(self):
        return json.load(open(self.config_file, encoding="utf8"))