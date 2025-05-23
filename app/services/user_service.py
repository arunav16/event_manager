from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
import secrets
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, null, update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_email_service, get_settings
from app.models.user_model import User
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.nickname_gen import generate_nickname
from app.utils.security import generate_verification_token, hash_password, verify_password
from uuid import UUID
from app.services.email_service import EmailService
from app.models.user_model import UserRole
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            # Validate incoming user data using the UserCreate schema.
            validated_data = UserCreate(**user_data).model_dump()

            # Check if a user already exists with this email.
            existing_user = await cls.get_by_email(session, validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                return None

            # Hash the plaintext password.
            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
        
            # Use provided nickname if available; otherwise, generate one.
            nickname = validated_data.get("nickname")
            if not nickname:
                nickname = generate_nickname()
            if not nickname:
                raise ValueError("Failed to generate a valid nickname")
        
            # If uniqueness is not required, simply use the nickname.
            validated_data["nickname"] = nickname

            # Create the new user
            new_user = User(**validated_data)
            new_user.verification_token = generate_verification_token()

            session.add(new_user)
            await session.commit()
            await email_service.send_verification_email(new_user)
            return new_user

        except ValidationError as e:
                logger.error(f"Validation error during user creation: {e}")
                return None


    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            validated_data = UserUpdate(**update_data).dict(exclude_unset=True)

            # Cast URL fields to str explicitly
            for url_field in ["profile_picture_url", "linkedin_profile_url", "github_profile_url"]:
                if url_field in validated_data and validated_data[url_field] is not None:
                    validated_data[url_field] = str(validated_data[url_field])

            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))

            query = (
                update(User)
                .where(User.id == user_id)
                .values(**validated_data)
                .execution_options(synchronize_session="fetch")
            )
            await cls._execute_query(session, query)
            updated_user = await cls.get_by_id(session, user_id)
            if updated_user:
                session.refresh(updated_user)
                logger.info(f"User {user_id} updated successfully.")
                return updated_user
            else:
                logger.error(f"User {user_id} not found after update attempt.")
            return None
        except Exception as e:
            logger.error(f"Error during user update: {e}")
            return None


    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info(f"User with ID {user_id} not found.")
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await cls._execute_query(session, query)
        return result.scalars().all() if result else []

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], get_email_service) -> Optional[User]:
        return await cls.create(session, user_data, get_email_service)
    

    @classmethod
    async def login_user(cls, session, email: str, password: str) -> Optional[User]:
        # Retrieve user by email
        user = await cls.get_by_email(session, email)
        if not user:
            logging.info("Login attempt failed: user %s not found", email)
            return None

        logging.info("User %s found for login attempt", email)
        
        # Check if user's email is verified
        if user.email_verified is False:
            logging.info("User %s has not verified their email", email)
            return None
        
        # Check if account is locked
        if user.is_locked:
            logging.info("User %s account is locked", email)
            return None

        # Verify password
        if verify_password(password, user.hashed_password):
            logging.info("Password verification successful for user %s", email)
            # Reset failed login attempts and update last login timestamp
            user.failed_login_attempts = 0
            user.last_login_at = datetime.now(timezone.utc)
            session.add(user)
            await session.commit()
            return user
        else:
            logging.info("Password verification failed for user %s", email)
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.is_locked = True
                logging.info("User %s has been locked due to too many failed attempts", email)
            session.add(user)
            await session.commit()
            return None
    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False


    @classmethod
    async def reset_password(cls, session: AsyncSession, user_id: UUID, new_password: str) -> bool:
        hashed_password = hash_password(new_password)
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            user.failed_login_attempts = 0  # Resetting failed login attempts
            user.is_locked = False  # Unlocking the user account, if locked
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, email: str, token: str) -> bool:
        user = await cls.get_by_email(session, email)
        if not user:
            return False
        # Validate the token (for example, check expiry, signature, etc.)
        if user.verification_token != token:
            return False
        # Mark the email as verified and save
        user.email_verified = True
        await session.commit()
        return True

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        Count the number of users in the database.

        :param session: The AsyncSession instance for database access.
        :return: The count of users.
        """
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        count = result.scalar()
        return count
    
    @classmethod
    async def unlock_user_account(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.is_locked:
            user.is_locked = False
            user.failed_login_attempts = 0  # Optionally reset failed login attempts
            session.add(user)
            await session.commit()
            return True
        return False
