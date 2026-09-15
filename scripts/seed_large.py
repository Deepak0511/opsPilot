import sqlite3
import os
import sys
import random
from datetime import datetime, timedelta
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

def generate_large_dataset():
    print(f"Generating large dataset to {DB_PATH}...")
    
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

    # Seed Data Generation
    random.seed(42) # Deterministic generation for consistency
    
    # 1. Employees (approx 250)
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    departments = ["Engineering", "HR", "Marketing", "Finance", "Sales", "IT Support", "Operations", "Legal"]
    roles = {"Engineering": ["Software Engineer", "DevOps Engineer", "QA Engineer"], "HR": ["HR Manager", "Recruiter"], "Marketing": ["Marketing Specialist", "SEO Expert"], "Finance": ["Accountant", "Financial Analyst"], "Sales": ["Sales Representative", "Account Executive"], "IT Support": ["IT Specialist", "Helpdesk Agent"], "Operations": ["Operations Manager"], "Legal": ["Legal Counsel"]}
    
    employees = []
    emp_count = 1
    for i in range(10): 
        for fn in first_names:
            for ln in last_names:
                if random.random() > 0.5:
                    dept = random.choice(departments)
                    role = random.choice(roles[dept])
                    device = random.choice(["Laptop", "Desktop", "Tablet"])
                    device_id = f"{'MAC' if random.random() > 0.5 else 'WIN'}-{random.randint(100, 9999)}"
                    employees.append((f"EMP{emp_count:03d}", f"{fn} {ln}", f"{fn.lower()}.{ln.lower()}{emp_count}@corpops.com", dept, role, device, device_id))
                    emp_count += 1
                    if emp_count > 250: break
            if emp_count > 250: break
        if emp_count > 250: break

    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)
    
    # 2. Systems (500+) with extreme tag depth
    print("Generating 500+ systems...")
    
    real_world_base = [
        # HR & Employee Experience
        ("Workday Time", "HR", "timesheets, pto, vacation request, leave of absence, time tracking, absence, sick days, hours logged"),
        ("ADP", "HR", "payroll, paycheck, tax forms, w2, w-2, salary, direct deposit, benefits, deductions, compensation"),
        ("Concur", "HR", "expenses, travel, flights, hotels, reimbursement, receipt, out of pocket, per diem, report, corporate card, amex"),
        ("Lattice", "HR", "performance review, goals, okrs, 1 on 1, feedback, continuous feedback, peer review, 360 review"),
        ("Greenhouse", "HR", "recruiting, applicant tracking, ats, interview, candidate, scorecard, offer letter, resume"),
        
        # Engineering & DevOps
        ("GitHub Enterprise", "Engineering", "source control, git, repository, pr, pull request, code review, commit, branch, merge, actions, ci cd"),
        ("Jira", "Engineering", "issue tracking, sprint, epic, story, bug, task, kanban, agile, scrum, board, ticket, backlog"),
        ("Artifactory", "Engineering", "package manager, artifact storage, npm, maven, docker registry, pypi, jfrog, binaries"),
        ("SonarQube", "Engineering", "code quality, static analysis, code coverage, bugs, vulnerabilities, code smell, tech debt"),
        
        # IT & Infra
        ("AWS", "Infrastructure", "cloud, compute, ec2, s3, rds, lambda, vpc, route53, iam, billing, elastic, infrastructure"),
        ("Datadog", "Infrastructure", "monitoring, observability, apm, traces, metrics, logs, dashboards, alerts, monitor, infrastructure"),
        ("Okta", "Access", "sso, single sign-on, identity, mfa, 2fa, duo, authenticator, login, password reset, app portal, access request"),
        ("ServiceNow", "Access", "itsm, tickets, service catalog, incidents, cmdb, requests, change management, approval"),
        ("Jamf", "Hardware", "mdm, macbook management, profiles, patching, remote wipe, software install, self service, apple"),
        ("Intune", "Hardware", "mdm, windows management, autopilot, compliance, profiles, remote wipe, mobile device"),
        ("Cisco Meraki", "Network", "networking, wifi, access point, switches, router, vpn, firewall, dashboard, connectivity"),
        
        # Finance & Procurement
        ("SAP S/4HANA", "Finance", "erp, accounting, finance, general ledger, accounts payable, accounts receivable, balance sheet, report"),
        ("Coupa", "Finance", "procurement, purchasing, purchase order, po, requisition, invoice, spending, approval"),
        ("Stripe", "Finance", "billing, payments, credit card, subscriptions, invoices, checkout, refund, chargeback"),
        
        # Sales & Marketing
        ("Salesforce", "Sales", "crm, leads, opportunities, accounts, contacts, reports, dashboards, sfdc, pipeline, forecast"),
        ("Marketo", "Marketing", "marketing automation, email blast, campaign, lead scoring, landing page, forms, nurture"),
        
        # Security & Compliance
        ("CrowdStrike", "Security", "edr, endpoint protection, antivirus, malware, quarantine, sensor, security alert, falcon"),
        ("Qualys", "Security", "vulnerability management, scanning, vm, compliance, security scan, assets, patch management"),
        
        # Productivity & Collaboration
        ("Office 365", "Software", "word, excel, powerpoint, outlook, emails, calendar, spreadsheet, presentation, document, meeting"),
        ("Slack", "Software", "chat, messaging, channels, direct message, huddle, notification, integration, bot, emoji"),
        ("Zoom", "Software", "video call, conferencing, meeting, webinar, recording, screen share, host, link"),
        ("Confluence", "Software", "wiki, documentation, pages, spaces, macros, knowledge base, notes, project plan"),
        
        # Data & Analytics
        ("Snowflake", "Data", "data warehouse, sql, tables, views, query, compute, storage, analytics, schema"),
        ("Tableau", "Data", "bi, reporting, dashboards, visualization, charts, data source, extract, analytics"),
        ("Airflow", "Data", "data engineering, etl, dags, scheduling, pipelines, tasks, orchestration, jobs"),
        
        # Day-to-Day Desktop Apps
        ("Google Chrome", "Software", "browser, web, internet, surf, chrome, google, extension, cache, cookies"),
        ("Mozilla Firefox", "Software", "browser, web, internet, surf, firefox, mozilla, extension, cache, cookies"),
        ("Microsoft Edge", "Software", "browser, web, internet, surf, edge, microsoft, extension, cache, cookies"),
        ("Microsoft Teams", "Software", "chat, video call, meeting, conferencing, screen share, teams, collaboration"),
        ("WebEx", "Software", "video call, conferencing, meeting, cisco, webex, screen share"),
        ("Adobe Acrobat Reader", "Software", "pdf, reader, document, sign, print, adobe, acrobat"),
        ("Adobe Creative Cloud", "Software", "photoshop, illustrator, premiere, design, creative, adobe, cc"),
        ("Notion", "Software", "notes, wiki, documentation, database, pages, workspace, productivity"),
        ("Evernote", "Software", "notes, notebook, sync, productivity, evernote"),
        ("OneNote", "Software", "notes, notebook, microsoft, office, onenote, sync"),
        ("VLC Media Player", "Software", "video, audio, media player, vlc, playback"),
        ("Notepad++", "Software", "text editor, code, notepad++, developer, text"),
        ("VS Code", "Software", "ide, code editor, visual studio code, vscode, developer, programming, typescript, python"),
        ("IntelliJ IDEA", "Software", "ide, java, code editor, intellij, jetbrains, developer, programming"),
        ("Postman", "Software", "api, testing, rest, http, request, postman, developer"),
        ("Docker Desktop", "Software", "docker, containers, virtualization, image, developer, desktop"),
        ("1Password", "Software", "password manager, vault, security, secrets, 1password"),
        ("LastPass", "Software", "password manager, vault, security, secrets, lastpass"),
        ("Spotify", "Software", "music, streaming, audio, podcast, spotify"),
        ("7-Zip", "Software", "archive, zip, unzip, extract, compress, rar, 7z, 7-zip"),
    ]
    
    systems = []
    sys_count = 1
    
    # 1. Add all real-world base systems
    for name, cat, tags in real_world_base:
        sys_id = f"SYS-{sys_count:03d}"
        desc = f"{name} system. Tags: {tags}"
        status = random.choices(["operational", "degraded", "down", "maintenance"], weights=[90, 5, 2, 3])[0]
        systems.append((sys_id, name, status, desc, "2026-09-10T08:00:00"))
        sys_count += 1
        
    # 2. Procedurally generate ~450 more internal tools to hit 500+ systems
    prefixes = ["Corp", "Ops", "Dev", "Intra", "Global", "Sec", "Data", "Cloud", "Net", "Tech", "Enterprise"]
    suffixes = ["Portal", "Tracker", "Hub", "Dashboard", "Manager", "Analyzer", "Sync", "Connect", "Gateway", "Vault", "Engine"]
    domains = ["HR", "Engineering", "Finance", "IT", "Marketing", "Data"]
    
    while sys_count <= 520:
        pref = random.choice(prefixes)
        suff = random.choice(suffixes)
        domain = random.choice(domains)
        name = f"{pref}{suff} {random.randint(1, 999)}"
        sys_id = f"SYS-{sys_count:03d}"
        desc = f"Internal {domain} application. Tags: internal tool, custom, {name.lower()}, {pref.lower()}"
        status = random.choices(["operational", "degraded", "down", "maintenance"], weights=[95, 3, 1, 1])[0]
        systems.append((sys_id, name, status, desc, "2026-09-10T08:00:00"))
        sys_count += 1
        
    # Also ensure Fallback systems exist
    systems.append(("SYS-HW", "IT Hardware Assets", "operational", "Physical IT assets like laptops and peripherals. Tags: hardware, laptop, macbook, dell, lenovo, monitor, screen, keyboard, mouse, dock", "2026-09-10T08:00:00"))
    systems.append(("SYS-OTHER", "Miscellaneous / Other", "operational", "Fallback system for issues not fitting other categories. Tags: generic, other, miscellaneous, unknown", "2026-09-10T08:00:00"))
    
    cursor.executemany("INSERT INTO systems VALUES (?, ?, ?, ?, ?)", systems)
    
    # 3. Knowledge Base Articles (~150 mapped to the first 50 systems)
    kb_templates = [
        ("How to connect to {sys}", "Network", "To connect to {sys}, ensure your credentials are valid. If it fails, check your network connection or clear your cache.", "vpn, network, {sys_lower}, connect, login, credentials, failure"),
        ("Resetting password for {sys}", "Access", "Go to the {sys} login page and click 'Forgot Password'. You will need your MFA device.", "password, reset, {sys_lower}, login, mfa, access, lockout"),
        ("Troubleshooting {sys} slowness", "Software", "If {sys} is running slow, try clearing your browser cache, restarting the application, or checking your internet speed.", "slow, performance, lag, {sys_lower}, cache, restart"),
        ("Requesting access to {sys}", "Software", "Access to {sys} requires approval from your manager. Please log a ticket with the 'Access' category.", "access, request, permission, role, {sys_lower}, manager approval"),
        ("Installing {sys} client", "Software", "Download the latest {sys} client from the IT portal. Run the installer with administrator privileges.", "install, setup, client, {sys_lower}, download, admin"),
        ("{sys} connection timeout error", "Infrastructure", "A timeout error in {sys} usually means the firewall is blocking it. Ensure you are on the corporate VPN.", "timeout, error, firewall, block, {sys_lower}, connection"),
        ("How to update {sys}", "Software", "Updates for {sys} are pushed automatically. To force an update, go to Help > Check for Updates.", "update, upgrade, version, {sys_lower}, latest"),
        ("{sys} best practices", "General", "When using {sys}, always save your work frequently and follow the corporate data handling guidelines.", "best practice, guide, manual, {sys_lower}, policy")
    ]
    
    kb_articles = []
    kb_count = 1
    
    # Generate KBs only for the top 100 real world systems to avoid bloating the KB too much
    for sys_id, name, status, desc, lc in systems[:100]:
        sys_short = name.split(" ")[0]
        for title_tmpl, cat, content_tmpl, tags_tmpl in kb_templates:
            if random.random() > 0.4: # 60% chance
                title = title_tmpl.format(sys=name)
                content = content_tmpl.format(sys=name)
                tags = tags_tmpl.format(sys_lower=sys_short.lower())
                
                # Inherit system tags so the KB is discoverable via colloquial terms (e.g. 'vpn' for Cisco Meraki)
                sys_tags = desc.split("Tags: ")[1] if "Tags: " in desc else ""
                if sys_tags:
                    tags = tags + ", " + sys_tags
                    
                extra_tags = random.sample(["error", "fix", "guide", "help", "support", "issue", "problem", "tutorial", "setup", "config", "sysadmin"], 3)
                tags = tags + ", " + ", ".join(extra_tags)
                
                kb_articles.append((f"KB{kb_count:03d}", title, cat, content, "", tags))
                kb_count += 1
                
    # Add hardware specific KBs
    hw_kbs = [
        ("Requesting a new laptop", "Hardware", "Submit a ticket. Specify Mac or Windows.", "laptop, hardware, request, mac, windows, upgrade, new hire"),
        ("Fixing flickering monitor", "Hardware", "Replace HDMI/DP cable. Update graphics drivers.", "monitor, hardware, screen, flicker, hdmi, displayport, cable, graphics"),
        ("Keyboard keys not responding", "Hardware", "Clean the keyboard with compressed air. If it fails, request a replacement.", "keyboard, keys, typing, hardware, stuck, broken, replace"),
        ("Docking station not charging", "Hardware", "Unplug power cycle the dock. Ensure firmware is up to date.", "dock, docking station, charge, power, usb-c, thunderbolt, hardware"),
        ("Mouse double clicking issue", "Hardware", "Check mouse settings in OS. If hardware is faulty, request a new mouse.", "mouse, click, double click, scroll, hardware, pointer")
    ]
    for title, cat, content, tags in hw_kbs:
        kb_articles.append((f"KB{kb_count:03d}", title, cat, content, "", tags))
        kb_count += 1
        
    cursor.executemany("INSERT INTO knowledge_base VALUES (?, ?, ?, ?, ?, ?)", kb_articles)
    
    # 4. Tickets (100 - 200)
    tickets = []
    inc_count = 1
    itr_count = 1
    
    ticket_issues = [
        ("Cannot login to {sys}", "I am getting an invalid password error when trying to access {sys}. Tags: login failed, password error, access denied, {sys_short}", "Access"),
        ("{sys} is running very slow", "Ever since the morning, {sys} takes minutes to load a page. Tags: slow, lag, performance, timeout, {sys_short}", "Software"),
        ("Need permission for {sys}", "My role changed and I need admin access to {sys}. Tags: permission, admin, role, access request, {sys_short}", "Access"),
        ("{sys} crashing on startup", "The {sys} client immediately crashes when I open it. Tags: crash, close, exception, error, startup, {sys_short}", "Software"),
        ("How do I configure {sys}?", "I need help setting up my profile in {sys}. Tags: config, setup, profile, help, {sys_short}", "Software"),
    ]
    
    it_support_employees = [e[0] for e in employees if e[3] == "IT Support"]
    if not it_support_employees:
        it_support_employees = [employees[0][0]]
        
    num_tickets = 150
    for _ in range(num_tickets):
        emp_id = random.choice(employees)[0]
        # Pick from the top 100 real systems for realistic tickets
        sys_tuple = random.choice(systems[:100])
        sys_id = sys_tuple[0]
        sys_name = sys_tuple[1]
        sys_short = sys_name.split(" ")[0].lower()
        
        issue_tmpl = random.choice(ticket_issues)
        title = issue_tmpl[0].format(sys=sys_name)
        description = issue_tmpl[1].format(sys=sys_name, sys_short=sys_short)
        
        extra_tags = random.sample(["urgent", "blocked", "help", "broken", "setup", "new", "failing", "down", "bug"], 2)
        description += f", {', '.join(extra_tags)}"
        
        category = issue_tmpl[2]
        status = random.choices(["Open", "In Progress", "Resolved", "Closed"], weights=[20, 20, 30, 30])[0]
        priority = random.choices(["Low", "Medium", "High", "Critical"], weights=[40, 40, 15, 5])[0]
        assigned_to = random.choice(it_support_employees)
        
        days_ago = random.randint(0, 180)
        created_date = datetime.now() - timedelta(days=days_ago)
        updated_date = created_date + timedelta(days=random.randint(0, 5))
        
        notes = "Issue resolved." if status in ["Resolved", "Closed"] else ""
        
        if category == "Access":
            tkt_id = f"ITR-{itr_count:03d}"
            itr_count += 1
        else:
            tkt_id = f"INC-{inc_count:03d}"
            inc_count += 1
            
        tickets.append((tkt_id, emp_id, title, description, status, priority, category, sys_id, assigned_to, created_date.isoformat(), updated_date.isoformat(), notes))
        
    # Add hardware tickets
    for _ in range(20):
        emp_id = random.choice(employees)[0]
        title = random.choice(["Laptop screen cracked", "Keyboard missing keys", "Need a new mouse", "Monitor won't turn on", "Laptop overheating"])
        description = f"Hardware issue reported. Tags: hardware, broken, replace, fix, {title.split(' ')[0].lower()}"
        status = random.choices(["Open", "In Progress", "Resolved", "Closed"], weights=[20, 20, 30, 30])[0]
        created_date = datetime.now() - timedelta(days=random.randint(0, 180))
        
        tkt_id = f"INC-{inc_count:03d}"
        inc_count += 1
        tickets.append((tkt_id, emp_id, title, description, status, "Medium", "Hardware", "SYS-HW", random.choice(it_support_employees), created_date.isoformat(), created_date.isoformat(), ""))
        
    cursor.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tickets)
    
    # 5. id_sequences
    sequences = [
        ("EMP", emp_count),
        ("INC", inc_count),
        ("ITR", itr_count),
        ("KB", kb_count),
        ("SYS", sys_count)
    ]
    cursor.executemany("INSERT INTO id_sequences VALUES (?, ?)", sequences)
    
    conn.commit()
    conn.close()
    
    print("Large dataset seeding complete!")
    print(f"Data loaded: {len(employees)} Employees, {len(systems)} Systems, {len(kb_articles)} KB Articles, {len(tickets)} Tickets.")

if __name__ == "__main__":
    generate_large_dataset()
