import hashlib

def hashed_id(email, salt):
    idobj = {
        'type': 'email',
        'hashed': True
    }
    idobj['salt'] = salt
    idobj['identity'] = 'sha256$' + hashlib.sha256(email + salt).hexdigest()
    return idobj
