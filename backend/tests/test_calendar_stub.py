"""
Tests for Calendar stub functionality
Tests the local JSON-based calendar adapter for offline testing
"""

import pytest
import json
import tempfile
import os
from datetime import date, datetime, timedelta

from src.calendar_handler import GoogleCalendarAdapter, ensure_data_file, get_calendar_adapter

@pytest.fixture
def temp_data_file():
    """Create a temporary data file for testing"""
    temp_path = tempfile.mktemp(suffix='.json')
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_ensure_data_file_creates_file():
    """Test that ensure_data_file creates the data file if it doesn't exist"""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_file = os.path.join(temp_dir, "test_appointments.json")
        
        # File shouldn't exist initially
        assert not os.path.exists(data_file)
        
        # Call ensure_data_file
        ensure_data_file(data_file)
        
        # File should now exist
        assert os.path.exists(data_file)
        
        # File should contain valid JSON with expected structure
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        assert 'appointments' in data
        assert 'availability' in data
        assert isinstance(data['appointments'], list)
        assert isinstance(data['availability'], dict)

def test_calendar_adapter_initialization(temp_data_file):
    """Test that GoogleCalendarAdapter initializes correctly"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    # Adapter should be created
    assert adapter is not None
    
    # Data file should be created
    assert os.path.exists(temp_data_file)
    
    # Should contain proper structure
    with open(temp_data_file, 'r') as f:
        data = json.load(f)
    
    assert 'appointments' in data
    assert 'availability' in data
    assert isinstance(data['appointments'], list)
    assert isinstance(data['availability'], dict)

def test_find_slots_returns_deterministic_list(temp_data_file):
    """Test find_slots returns a consistent list of available times"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    test_date = date.today()
    slots = adapter.find_slots("haircut", test_date)
    
    # Should return a list
    assert isinstance(slots, list)
    
    # Each slot should have required fields
    for slot in slots:
        assert 'time' in slot
        assert 'date' in slot
        assert 'available' in slot

def test_find_slots_deterministic_across_calls(temp_data_file):
    """Test that find_slots returns the same results for repeated calls"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    test_date = date.today()
    slots1 = adapter.find_slots("haircut", test_date)
    slots2 = adapter.find_slots("haircut", test_date)
    
    # Should return identical results
    assert slots1 == slots2

def test_find_slots_sunday_returns_empty(temp_data_file):
    """Test that Sunday returns no available slots"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    # Find next Sunday
    test_date = date.today()
    days_ahead = 6 - test_date.weekday()  # Sunday is 6
    if days_ahead <= 0:  # If today is Sunday
        days_ahead += 7
    sunday = test_date + timedelta(days=days_ahead)
    
    slots = adapter.find_slots("haircut", sunday)
    
    # Sunday should have no slots
    assert len(slots) == 0

def test_book_appointment_success(temp_data_file):
    """Test successful appointment booking"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    # Book an appointment
    result = adapter.book_appointment(
        name="John Doe",
        service="haircut",
        date_time=datetime(2024, 12, 16, 10, 0),  # Monday 10 AM
        phone="555-1234",
        email="john@example.com"
    )
    
    # Should be successful
    assert result['success'] is True
    assert 'confirmation_code' in result
    assert 'appointment' in result

def test_book_appointment_creates_confirmation_code(temp_data_file):
    """Test that booking creates a unique confirmation code"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    result1 = adapter.book_appointment(
        name="John Doe",
        service="haircut",
        date_time=datetime(2024, 12, 16, 10, 0),
        phone="555-1234",
        email="john@example.com"
    )
    
    result2 = adapter.book_appointment(
        name="Jane Smith",
        service="haircut",
        date_time=datetime(2024, 12, 17, 11, 0),
        phone="555-5678",
        email="jane@example.com"
    )
    
    # Should have different confirmation codes
    assert result1['success'] is True
    assert result2['success'] is True
    assert result1['confirmation_code'] != result2['confirmation_code']

def test_book_appointment_persists_to_file(temp_data_file):
    """Test that bookings are persisted to the JSON file"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    result = adapter.book_appointment(
        name="John Doe",
        service="haircut",
        date_time=datetime(2024, 12, 16, 10, 0),
        phone="555-1234",
        email="john@example.com"
    )
    
    assert result['success'] is True
    
    # Verify data was saved to file
    with open(temp_data_file, 'r') as f:
        data = json.load(f)
    
    assert len(data['appointments']) == 1
    appointment = data['appointments'][0]
    assert appointment['name'] == "John Doe"
    assert appointment['service'] == "haircut"

def test_find_slots_excludes_booked_times(temp_data_file):
    """Test that find_slots excludes already booked appointment times"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    test_date = date(2024, 12, 16)  # Monday
    
    # Get initial available slots
    initial_slots = adapter.find_slots("haircut", test_date)
    ten_am_available = any(slot['time'] == '10:00' for slot in initial_slots if slot['available'])
    
    # Book 10 AM appointment
    adapter.book_appointment(
        name="John Doe",
        service="haircut",
        date_time=datetime(2024, 12, 16, 10, 0),
        phone="555-1234",
        email="john@example.com"
    )
    
    # Get slots again
    updated_slots = adapter.find_slots("haircut", test_date)
    ten_am_still_available = any(slot['time'] == '10:00' for slot in updated_slots if slot['available'])
    
    # 10 AM should no longer be available (if it was initially)
    if ten_am_available:
        assert not ten_am_still_available

def test_multiple_bookings_same_day_different_times(temp_data_file):
    """Test that multiple bookings on the same day work correctly"""
    adapter = GoogleCalendarAdapter(temp_data_file)
    
    # Book two different times on the same day
    result1 = adapter.book_appointment(
        name="John Doe",
        service="haircut",
        date_time=datetime(2024, 12, 16, 10, 0),
        phone="555-1234",
        email="john@example.com"
    )
    
    result2 = adapter.book_appointment(
        name="Jane Smith",
        service="haircut",
        date_time=datetime(2024, 12, 16, 11, 0),
        phone="555-5678",
        email="jane@example.com"
    )
    
    # Both should succeed
    assert result1['success'] is True
    assert result2['success'] is True
    
    # Verify both are in the file
    with open(temp_data_file, 'r') as f:
        data = json.load(f)
    
    assert len(data['appointments']) == 2

def test_get_calendar_adapter_returns_google_adapter():
    """Test that get_calendar_adapter returns GoogleCalendarAdapter instance"""
    adapter = get_calendar_adapter()
    
    # Should return a GoogleCalendarAdapter
    assert isinstance(adapter, GoogleCalendarAdapter)
    assert hasattr(adapter, 'find_slots')
    assert hasattr(adapter, 'book_appointment')