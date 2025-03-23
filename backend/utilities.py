import uuid
import base64

class Generate:
    def gen_uuid(length:int=6)->str:
        uid = uuid.uuid4()
        b64 = base64.urlsafe_b64encode(uid.bytes).decode('utf-8')
        return b64[:length]