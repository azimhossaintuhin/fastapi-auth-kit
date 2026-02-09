from  passlib.context import  CryptContext


_PWD = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str) -> str:
    return _PWD.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return _PWD.verify(password, hashed_password)