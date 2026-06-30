"""
StudyOS Utilities — Security.

Responsibility: Provides stateless cryptographic utilities, 
such as password hashing and verification.
"""

from passlib.context import CryptContext

# Define the password hashing context.
# bcrypt is the standard, secure algorithm for password hashing.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its hashed version.
    
    Args:
        plain_password: The raw string provided by the user.
        hashed_password: The bcrypt hash retrieved from the database.
        
    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Securely hash a plaintext password.
    
    Args:
        password: The raw string to hash.
        
    Returns:
        The bcrypt-hashed string suitable for database storage.
    """
    return pwd_context.hash(password)
