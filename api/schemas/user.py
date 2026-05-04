from pydantic import BaseModel, ConfigDict

class UserRegister(BaseModel):
        
    name:str
    lastname : str
    username : str
    email : str
    password : str 


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    lastname: str
    username: str
    email: str




