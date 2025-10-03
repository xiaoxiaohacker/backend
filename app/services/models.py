from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(200))

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    management_ip = Column(String(50), unique=True)
    vendor = Column(String(50))
    username = Column(String(50))
    password = Column(String(100))
    port = Column(Integer, default=22)

class Config(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    config = Column(Text)
    taken_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
