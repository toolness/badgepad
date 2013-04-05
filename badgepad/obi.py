import hashlib

def hashed_id(recipient, salt):
    email = recipient['email']
    idobj = {
        'type': 'email',
        'hashed': True
    }
    idobj['salt'] = salt
    idobj['identity'] = 'sha256$' + hashlib.sha256(email + salt).hexdigest()
    return idobj
