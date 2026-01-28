
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ai_receptionist.models.base import Base
from ai_receptionist.models.business import Business
# Expected to fail until implemented
from ai_receptionist.models.billing import BillingUsageEvent 
from ai_receptionist.services.billing.repository import SqlAlchemyBillingRepository

# Use an in-memory SQLite DB for TDD speed
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_business_has_stripe_fields(session):
    """Test that Business model has Stripe-related fields"""
    biz = Business(name="Test Biz", stripe_customer_id="cus_123", subscription_status="active")
    session.add(biz)
    session.commit()
    
    loaded = session.query(Business).filter_by(name="Test Biz").first()
    assert loaded.stripe_customer_id == "cus_123"
    assert loaded.subscription_status == "active"

def test_usage_event_creation(session):
    """Test creating a billing usage event"""
    biz = Business(name="Usage Biz")
    session.add(biz)
    session.commit()
    
    event = BillingUsageEvent(business_id=biz.id, minutes=5)
    session.add(event)
    session.commit()
    
    assert event.id is not None
    assert event.minutes == 5
    assert event.created_at is not None

def test_repository_add_usage(session):
    """Test the SqlAlchemy implementation of BillingRepository"""
    repo = SqlAlchemyBillingRepository(session)
    
    biz = Business(name="Repo Biz")
    session.add(biz)
    session.commit()
    
    # Add usage via repo
    repo.add_usage(str(biz.id), 10)
    
    # Verify in DB
    events = session.query(BillingUsageEvent).filter_by(business_id=biz.id).all()
    assert len(events) == 1
    assert events[0].minutes == 10
