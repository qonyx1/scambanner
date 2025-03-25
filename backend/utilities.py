import uuid
import tomli
import base64, random, string

class Generate:
    @staticmethod
    def gen_id(length: int = 8) -> str:
        characters = string.ascii_letters + string.digits + "!@$%^&"
        return ''.join(random.choice(characters) for _ in range(length))
    
class SystemConfig:
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None
    
        