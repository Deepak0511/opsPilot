import sqlite3
import os
import sys
from pathlib import Path

# Add project root and src to path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ops_pilot.config.settings import lookup_for_setting

DB_PATH = lookup_for_setting["env_db_path"]

def seed_small():
    print(f"Seeding small dataset to {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} does not exist. Please run init_db.py first.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] > 0:
        print("Database already contains data. Please run flush_ops_db.py first if you want a clean seed.")
        conn.close()
        return
    
    # 2. Seed Data
    
    # Employees
    employees = [
        ("EMP001", "Alex Kumar", "alex.kumar@corpops.com", "Engineering", "Software Engineer", "Laptop", "MAC-101"),
        ("EMP002", "Priya Sharma", "priya.sharma@corpops.com", "HR", "HR Manager", "Laptop", "WIN-202"),
        ("EMP003", "Mike Chen", "mike.chen@corpops.com", "Marketing", "Marketing Specialist", "Tablet", "IPAD-303"),
        ("EMP004", "Sarah Jones", "sarah.jones@corpops.com", "Finance", "Accountant", "Laptop", "WIN-404"),
        ("EMP005", "David Lee", "david.lee@corpops.com", "Engineering", "DevOps Engineer", "Laptop", "MAC-505"),
        ("EMP006", "Emily Davis", "emily.davis@corpops.com", "IT Support", "IT Specialist", "Desktop", "WIN-606"),
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)
    
    # Systems
    systems = [
        ("SYS-VPN", "Corporate VPN", "degraded", "Primary VPN for remote access.", "2026-09-12T08:00:00"),
        ("SYS-JIRA", "Jira Issue Tracker", "operational", "Project management and issue tracking.", "2026-09-12T08:05:00"),
        ("SYS-EMAIL", "Exchange Email", "operational", "Corporate email server.", "2026-09-12T08:10:00"),
        ("SYS-SSO", "Okta Single Sign-On", "operational", "Identity and access management.", "2026-09-12T08:15:00"),
        ("SYS-WIFI", "Office Guest WiFi", "down", "Guest network in the main office.", "2026-09-12T08:20:00"),
        ("SYS-GIT", "GitLab Repository", "operational", "Source code management.", "2026-09-12T08:25:00"),
        ("SYS-HW", "IT Hardware Assets", "operational", "Physical IT assets like laptops and peripherals.", "2026-09-12T08:00:00"),
        ("SYS-OTHER", "Miscellaneous / Other", "operational", "Fallback system for issues not fitting other categories.", "2026-09-12T08:00:00"),
    ]
    cursor.executemany("INSERT INTO systems VALUES (?, ?, ?, ?, ?)", systems)
    
    # Knowledge Base
    kb_articles = [
        ("KB001", "How to connect to Corporate VPN", "Network", "To connect to the VPN, open the Cisco AnyConnect client and enter vpn.corpops.com. Use your SSO credentials.", "", "vpn, network, remote"),
        ("KB002", "Resetting Okta SSO Password", "Access", "Go to the Okta login page and click 'Forgot Password'. You will need access to your secondary email or phone for MFA.", "", "password, sso, login"),
        ("KB003", "Requesting a new laptop", "Hardware", "Submit a ticket with category 'Hardware' and specify Mac or Windows. Approval from your manager is required.", "", "laptop, hardware, request"),
        ("KB004", "Guest WiFi Access", "Network", "Guests can use 'CorpOps-Guest'. They must accept the terms of service on the captive portal. No password required.", "", "wifi, network, guest"),
        ("KB005", "Jira Access Request", "Software", "Access to Jira requires project manager approval. Open a ticket providing the project key.", "", "jira, access, software"),
        ("KB006", "Fixing flickering monitor", "Hardware", "If your monitor flickers, try replacing the HDMI/DisplayPort cable. If issues persist, log a hardware ticket.", "", "monitor, hardware, screen"),
    ]
    cursor.executemany("INSERT INTO knowledge_base VALUES (?, ?, ?, ?, ?, ?)", kb_articles)
    
    # Tickets
    tickets = [
        ("INC-001", "EMP001", "VPN dropping connection", "My VPN disconnects every 10 minutes since the new update.", "open", "high", "Network", "SYS-VPN", "IT Support", "2026-09-12T09:00:00", "2026-09-12T09:00:00", ""),
        ("ITR-001", "EMP002", "Need Jira access", "Please grant me access to the HR project in Jira.", "resolved", "medium", "Access", "SYS-JIRA", "IT Support", "2026-09-11T10:00:00", "2026-09-11T11:00:00", "Access granted."),
        ("INC-002", "EMP003", "Tablet won't charge", "My company iPad is not charging even with a new cable.", "in_progress", "medium", "Hardware", "None", "Hardware Team", "2026-09-12T09:30:00", "2026-09-12T10:00:00", "Waiting for spare parts."),
        ("ITR-002", "EMP005", "Production DB access", "Need read access to prod DB for debugging.", "open", "high", "Access", "SYS-SSO", "Security Team", "2026-09-12T10:00:00", "2026-09-12T10:00:00", ""),
        ("INC-003", "EMP001", "Monitor flickering", "My external monitor keeps flickering on and off.", "open", "low", "Hardware", "None", "Hardware Team", "2026-09-12T11:00:00", "2026-09-12T11:00:00", ""),
    ]
    cursor.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tickets)
    
    # id_sequences
    sequences = [
        ("EMP", 7),
        ("INC", 4),
        ("ITR", 3),
        ("KB", 7),
        ("SYS", 7)
    ]
    cursor.executemany("INSERT INTO id_sequences VALUES (?, ?)", sequences)
    
    conn.commit()
    conn.close()
    
    print("Small dataset seeding complete!")
    print(f"Sample data loaded: {len(employees)} Employees, {len(systems)} Systems, {len(kb_articles)} KB Articles, {len(tickets)} Tickets.")

if __name__ == "__main__":
    seed_small()
