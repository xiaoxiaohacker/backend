from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class DeviceCreate(BaseModel):
    management_ip: str
    vendor: str
    username: str
    password: str
    port: int = 22

class DeviceOut(DeviceCreate):
    id: int

    class Config:
        orm_mode = True
