#!/usr/bin/env python3
"""
create_admin.py — Seed an admin user directly into the database.

Usage:
    python scripts/create_admin.py \
        --clerk-id user_2abc123 \
        --email admin@sbuniversity.edu \
        --name "Super Admin"

Requirements:
    - .env must have DATABASE_URL set (postgresql+asyncpg://...)
    - Run from inside the server/ directory with .venv active
"""

import asyncio
import argparse
import sys
import os

# Make sure app module is importable from server/ root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.db.models.user import User, UserRole, UserStatus
from app.db.base import Base


async def create_admin(clerk_id: str, email: str, full_name: str) -> None:
    # Ensure tables exist (safe if already migrated)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if user already exists
        existing = await db.execute(
            select(User).where(
                (User.clerk_user_id == clerk_id) | (User.email == email)
            )
        )
        user = existing.scalar_one_or_none()

        if user:
            if user.role == UserRole.ADMIN:
                print(f"✅ User '{user.email}' is already an ADMIN. Nothing to do.")
            else:
                old_role = user.role.value
                user.role = UserRole.ADMIN
                user.status = UserStatus.ACTIVE
                await db.commit()
                await db.refresh(user)
                print(f"✅ Upgraded '{user.email}' from {old_role} → admin")
                print(f"   User ID   : {user.id}")
                print(f"   Clerk ID  : {user.clerk_user_id}")
        else:
            new_user = User(
                clerk_user_id=clerk_id,
                email=email,
                full_name=full_name,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            print(f"✅ Admin user created successfully!")
            print(f"   Name      : {new_user.full_name}")
            print(f"   Email     : {new_user.email}")
            print(f"   Role      : {new_user.role.value}")
            print(f"   User ID   : {new_user.id}")
            print(f"   Clerk ID  : {new_user.clerk_user_id}")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument(
        "--clerk-id",
        required=True,
        help="Clerk user ID (e.g. user_2abc123) — find this in your Clerk dashboard",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Admin user email address",
    )
    parser.add_argument(
        "--name",
        default="Admin",
        help="Full name for the admin user (default: Admin)",
    )
    args = parser.parse_args()

    asyncio.run(create_admin(
        clerk_id=args.clerk_id,
        email=args.email,
        full_name=args.name,
    ))


if __name__ == "__main__":
    main()
