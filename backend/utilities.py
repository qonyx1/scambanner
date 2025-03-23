import uuid
import base64, random, string

class Generate:
    def gen_id(length:int=32)->str:
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))
    
class SystemConfig:
    import tomli
    with open("../system_config.toml", mode="rb") as fp:
        system_config = tomli.load(fp) or None
    
        