import pytest
from ops_pilot.repository.system_repository import (
    create_system,
    find_system_by_id,
    search_systems_by_keyword,
    search_systems_by_status,
    search_supported_systems_from_request,
    update_system,
    delete_system,
    count_systems,
)
from ops_pilot.models.system import System

@pytest.fixture
def sample_system():
    return System(
        id="SYS-001",
        name="Main Database",
        status="Online",
        description="Primary PostgreSQL database",
        last_checked="2023-10-27T10:00:00Z"
    )

def test_create_and_find_system(db_connection, sample_system):
    create_system(sample_system)
    
    found = find_system_by_id(sample_system.id)
    assert found is not None
    assert found.name == "Main Database"

def test_search_systems_by_keyword(db_connection, sample_system):
    create_system(sample_system)
    
    # Test partial name match
    # Since we added AND logic and stop words, 'main' and 'database' are matched.
    results = search_systems_by_keyword("Main Database")
    assert len(results) == 1
    
    # Test description match
    results = search_systems_by_keyword("Cache")
    assert len(results) == 0
    
    # Test with stop words - 'is', 'the', 'up' should be ignored
    results = search_systems_by_keyword("Is the PostgreSQL database up?")
    assert [system.id for system in results] == ["SYS-001"]

def test_search_systems_by_status(db_connection, sample_system):
    create_system(sample_system)
    
    results = search_systems_by_status("online")
    assert len(results) == 1
    
    results = search_systems_by_status("offline")
    assert len(results) == 0

def test_update_system(db_connection, sample_system):
    create_system(sample_system)
    
    sample_system.status = "Offline"
    update_system(sample_system)
    
    found = find_system_by_id(sample_system.id)
    assert found.status == "Offline"

def test_delete_system(db_connection, sample_system):
    create_system(sample_system)
    delete_system(sample_system.id)
    
    found = find_system_by_id(sample_system.id)
    assert found is None

def test_count_systems(db_connection, sample_system):
    create_system(sample_system)
    
    assert count_systems() == 1
    assert count_systems(keyword="Main") == 1
    assert count_systems(keyword="Main", status="Online") == 1
    assert count_systems(keyword="Cache") == 0


def test_search_supported_systems_from_full_request(db_connection):
    create_system(
        System(
            id="SYS-VPN",
            name="Patliputra VPN",
            status="Operational",
            description="Approved corporate virtual private network service.",
        )
    )

    results = search_supported_systems_from_request(
        "How do I reset my VPN password?"
    )

    assert [system.id for system in results] == ["SYS-VPN"]


def test_search_supported_systems_returns_no_match_for_unknown_vendor(db_connection):
    create_system(
        System(
            id="SYS-VPN",
            name="Patliputra VPN",
            status="Operational",
            description="Approved corporate virtual private network service.",
        )
    )

    assert search_supported_systems_from_request("Configure a public satellite service") == []


def test_search_supported_systems_returns_tied_catalog_matches(db_connection):
    create_system(
        System(
            id="SYS-INTERNET-A",
            name="Acme Internet",
            status="Operational",
            description="Approved internet reimbursement vendor.",
        )
    )
    create_system(
        System(
            id="SYS-INTERNET-B",
            name="Bharat Internet",
            status="Operational",
            description="Approved internet reimbursement vendor.",
        )
    )

    results = search_supported_systems_from_request(
        "How do I submit an internet reimbursement?"
    )

    assert [system.id for system in results] == ["SYS-INTERNET-A", "SYS-INTERNET-B"]


def test_search_supported_systems_ignores_filler_only_request(db_connection):
    create_system(
        System(
            id="SYS-VPN",
            name="Patliputra VPN",
            status="Operational",
            description="Approved corporate virtual private network service.",
        )
    )

    assert search_supported_systems_from_request("How can you help me?") == []
