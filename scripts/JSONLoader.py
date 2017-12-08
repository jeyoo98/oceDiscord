import json


class CreateJSON:
    def __init__(self):
        self.default = {
            "ServiceAuthCredentials": None,
            "Prefix:": None,
            "Commands": {
                "help": {
                    "Enabled": False,
                    "Script": "help.py",
                    "Permissions": "*",
                    "Default-Message": "Please configure the help.yml file."
                },
                "motd": {
                    "Enabled": False,
                    "Script": "motd.py",
                    "Permissions": "Admins, Admirals",
                    "Default-Message": "Message from the Admirals:\nWelcome to (%dservername)!"
                },
                "on_join": {
                    "Enabled": False,
                    "Script": "on_join.py",
                    "Permissions": "Admins, Admirals",
                    "Default-Message": "Welcome to (%dservername), (%mentionuser)!"
                },
                "example": {
                    "Enabled": False,
                    "Script": "example.py",
                    "Permissions": "Admins, Admirals"
                }
            }
        }
        self.create_json('config.json', self.default)

    @staticmethod
    def create_json(json_name, inp):
        with open(json_name, 'w') as json_file:
            entries = json.dumps(inp)
            data = json.loads(entries)
            json.dump(data, json_file, indent=4)
