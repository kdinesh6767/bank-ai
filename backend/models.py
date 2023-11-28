# models.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

Base = declarative_base()

class Banks(Base):
    __tablename__ = "banks"
    bank_id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    branches = relationship("Branches", back_populates="bank")

class Branches(Base):
    __tablename__ = "branches"
    branch_id = Column(Integer, primary_key=True, index=True)
    branch_name = Column(String(50), nullable=False)
    bank_id = Column(Integer, ForeignKey("banks.bank_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bank = relationship("Banks", back_populates="branches")

class Addresses(Base):
    __tablename__ = "addresses"
    address_id = Column(Integer, primary_key=True, index=True)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Customers(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    age = Column(Integer)
    identity_card_no = Column(String(20))
    language = Column(String(20)) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    accounts = relationship("Accounts", back_populates="customer")

class Accounts(Base):
    __tablename__ = "accounts"
    account_id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), unique=True, nullable=False)
    balance = Column(DECIMAL(15, 2), default="0.0")
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transactions", back_populates="account")
    customer = relationship("Customers", back_populates="accounts", lazy="joined")

class Transactions(Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(DECIMAL(15, 2), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    account_number = Column(String(20))
    description = Column(String(255))
    balance_after_transaction = Column(DECIMAL(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("Accounts", back_populates="transactions")
    chalan = relationship("Chalan", uselist=False, back_populates="transaction")

class Chalan(Base):
    __tablename__ = "chalans"
    chalan_id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id", ondelete="CASCADE"), unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    amount_in_words = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transaction = relationship("Transactions", back_populates="chalan")

# Other models (Branches, Addresses, Customers, Accounts, Transactions) should be added here
