from pydantic import BaseModel

class UserRegister(BaseModel):
        
    name:str
    lastname : str
    username : str
    email : str
    password : str 


