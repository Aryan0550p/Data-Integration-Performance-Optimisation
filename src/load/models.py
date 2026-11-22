"""
SQLAlchemy 2.0 Declarative Models for Enterprise Unified Data Model (8 Tables, 6 Foreign Keys)
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Integer, SmallInteger, Numeric, Boolean, Date, DateTime,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# 1. Dimension: Customers
class DimCustomer(Base):
    __tablename__ = "dim_customers"

    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_normalized: Mapped[Optional[str]] = mapped_column(String(30))
    street_address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_code: Mapped[Optional[str]] = mapped_column(String(10))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country_code: Mapped[Optional[str]] = mapped_column(String(10), default="US")
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    is_enterprise: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    orders: Mapped[List["FactOrder"]] = relationship("FactOrder", back_populates="customer")


# 2. Dimension: Products
class DimProduct(Base):
    __tablename__ = "dim_products"

    product_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    retail_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("1.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    order_items: Mapped[List["FactOrderItem"]] = relationship("FactOrderItem", back_populates="product")


# 3. Dimension: Warehouses
class DimWarehouse(Base):
    __tablename__ = "dim_warehouses"

    warehouse_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    warehouse_name: Mapped[str] = mapped_column(String(150), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    facility_type: Mapped[str] = mapped_column(String(50), default="Distribution Center")
    capacity_sqft: Mapped[int] = mapped_column(Integer, default=50000)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), default="US")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    shipments: Mapped[List["FactShipment"]] = relationship("FactShipment", back_populates="warehouse")


# 4. Dimension: Campaigns
class DimCampaign(Base):
    __tablename__ = "dim_campaigns"

    campaign_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    campaign_name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    utm_source: Mapped[Optional[str]] = mapped_column(String(100))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100))
    target_region: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    orders: Mapped[List["FactOrder"]] = relationship("FactOrder", back_populates="campaign")


# 5. Dimension: Date
class DimDate(Base):
    __tablename__ = "dim_date"

    date_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    day_name: Mapped[str] = mapped_column(String(15), nullable=False)
    day_of_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    day_of_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    week_of_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month_name: Mapped[str] = mapped_column(String(15), nullable=False)
    calendar_quarter: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    calendar_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship
    orders: Mapped[List["FactOrder"]] = relationship("FactOrder", back_populates="order_date")


# 6. Fact: Orders (Contains FK1, FK2, FK3)
class FactOrder(Base):
    __tablename__ = "fact_orders"

    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("dim_customers.customer_id"), nullable=False)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("dim_campaigns.campaign_id"), nullable=True)
    order_date_key: Mapped[int] = mapped_column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    order_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    order_status: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    customer: Mapped["DimCustomer"] = relationship("DimCustomer", back_populates="orders")
    campaign: Mapped[Optional["DimCampaign"]] = relationship("DimCampaign", back_populates="orders")
    order_date: Mapped["DimDate"] = relationship("DimDate", back_populates="orders")
    items: Mapped[List["FactOrderItem"]] = relationship("FactOrderItem", back_populates="order", cascade="all, delete-orphan")
    shipment: Mapped[Optional["FactShipment"]] = relationship("FactShipment", back_populates="order", uselist=False, cascade="all, delete-orphan")


# 7. Fact: Order Items (Contains FK4, FK5)
class FactOrderItem(Base):
    __tablename__ = "fact_order_items"

    order_item_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("fact_orders.order_id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("dim_products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, CheckConstraint("quantity > 0"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), CheckConstraint("unit_price >= 0"), nullable=False)
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    order: Mapped["FactOrder"] = relationship("FactOrder", back_populates="items")
    product: Mapped["DimProduct"] = relationship("DimProduct", back_populates="order_items")


# 8. Fact: Shipments (Contains FK6)
class FactShipment(Base):
    __tablename__ = "fact_shipments"

    shipment_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("fact_orders.order_id"), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(50), ForeignKey("dim_warehouses.warehouse_id"), nullable=False)
    carrier_code: Mapped[str] = mapped_column(String(50), nullable=False)
    tracking_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    shipping_status: Mapped[str] = mapped_column(String(30), nullable=False)

    # Relationships
    order: Mapped["FactOrder"] = relationship("FactOrder", back_populates="shipment")
    warehouse: Mapped["DimWarehouse"] = relationship("DimWarehouse", back_populates="shipments")
