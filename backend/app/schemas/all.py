from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal

# --- Permission Schemas ---
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    class Config:
        from_attributes = True

# --- Role Schemas ---
class RoleBase(BaseModel):
    name: Literal['admin', 'supervisor', 'worker']
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
    class Config:
        from_attributes = True

class RoleAssignPermissions(BaseModel):
    permission_ids: List[int]

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_id: int

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    roles: List[Role] = []
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=6)

class UserAssignRoles(BaseModel):
    role_ids: List[int]

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
