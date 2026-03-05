import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import select

# Add the parent directory to sys.path to resolve app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash

def seed_admin_user():
    db: Session = SessionLocal()
    try:
        # Check if admin role exists
        admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none()
        if not admin_role:
            print("Admin role not found. Creating admin role...")
            admin_role = Role(name="admin", description="System Administrator")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            
        # Check if admin user exists
        admin_user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if not admin_user:
            print("Admin user not found. Creating admin user...")
            # Following the logic from the previous conversation about password updates
            hashed_password = get_password_hash("password123")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=hashed_password,
                is_active=True
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
            # Ensure the user has the admin role
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                db.commit()
                print("Added admin role to existing admin user.")
                
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database seeding...")
    seed_admin_user()
    print("Database seeding completed.")
