from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from app.schemas.all import User as UserSchema, UserCreate, UserAssignRoles, UserUpdate
from app.api.dependencies import require_permission

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
def read_users(db: Session = Depends(get_db), _ = Depends(require_permission("user.view"))):
    users = db.query(User).all()
    return users

@router.post("/", response_model=UserSchema)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), _ = Depends(require_permission("user.create"))):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        is_active=True
    )
    
    role = db.query(Role).filter(Role.id == user_in.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")
    new_user.roles = [role]
            
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), _ = Depends(require_permission("user.edit"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_in.username:
        if db.query(User).filter(User.username == user_in.username, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="Username already in use")
        user.username = user_in.username
        
    if user_in.email:
        if db.query(User).filter(User.email == user_in.email, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_in.email
        
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)
        
    if user_in.role_id is not None:
        role = db.query(Role).filter(Role.id == user_in.role_id).first()
        if role:
            user.roles = [role]
        else:
            user.roles = []
            
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _ = Depends(require_permission("user.delete"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/roles", response_model=UserSchema)
def assign_roles_to_user(
    user_id: int, 
    role_in: UserAssignRoles, 
    db: Session = Depends(get_db), 
    _ = Depends(require_permission("user.assign_roles"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    roles = db.query(Role).filter(Role.id.in_(role_in.role_ids)).all()
    if len(roles) != len(role_in.role_ids):
        raise HTTPException(status_code=400, detail="Some roles were not found")
        
    user.roles = roles
    db.commit()
    db.refresh(user)
    return user
