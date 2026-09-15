import subprocess
import os
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_SCRIPT = PROJECT_ROOT / "scripts" / "cli.py"

def run_cli_interaction(prompts: list[str]) -> str:
    """
    Runs the CLI script, feeds the sequence of prompts to stdin, 
    and returns the complete stdout output.
    """
    input_str = "\n".join(prompts) + "\nexit\n"
    
    # We must run it using the venv python to ensure it has all dependencies
    python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = "python" # fallback to global if venv is missing
        
    process = subprocess.Popen(
        [str(python_exe), str(CLI_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    
    stdout, stderr = process.communicate(input=input_str)
    return stdout

def flush_chat_db():
    python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = "python"
    subprocess.run([str(python_exe), str(PROJECT_ROOT / "scripts" / "flush_chat_db.py")], cwd=str(PROJECT_ROOT))

class TestOpsPilotE2E(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("Resetting primary database via seed_large.py to ensure clean ticket state...")
        python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = "python"
        subprocess.run([str(python_exe), str(PROJECT_ROOT / "scripts" / "seed_large.py")], cwd=str(PROJECT_ROOT))
    
    def setUp(self):
        # Flush the chat DB before each test to ensure a clean slate
        flush_chat_db()

    def test_01_knowledge_base_retrieval(self):
        print("\nRunning Test 1: KB Retrieval (VPN Password)")
        output = run_cli_interaction(["How do I configure my Cisco Meraki VPN?"])
        
        # Should invoke the KB tool
        self.assertIn("search_knowledge_base_tool", output)
        # Should find Cisco Meraki (the VPN system)
        self.assertIn("Cisco Meraki", output)
        # The AI should not create a ticket
        self.assertNotIn("create_ticket_tool", output)

    def test_02_ticket_status_lookup(self):
        print("\nRunning Test 2: Ticket Status Lookup")
        output = run_cli_interaction([
            "Check status of ticket INC-001"
        ])
        self.assertTrue("search_tickets_tool" in output or "search_ticket_by_id_tool" in output)
        # Should have found a ticket
        self.assertTrue("INC-" in output or "not find any active" in output or "found" in output.lower())

    def test_03_incident_ticket_creation(self):
        print("\nRunning Test 3: Incident Ticket Creation (Outlook)")
        # Multi-turn: Issue -> Provide EMP001 -> Confirm with 'yes'
        # The agent asks for confirmation, then applies it.
        # It only needs one 'yes' now because the prompt was fixed.
        output = run_cli_interaction([
            "My Office 365 is randomly freezing test999. Please raise a ticket.",
            "EMP001",
            "yes"
        ])
        
        # Check that it drafts the ticket
        # The actual ticket creation is done inside APPLY_CONFIRMED_TICKET_CHANGE node,
        # which prints 'Ticket action completed successfully'
        self.assertIn("Ticket action completed successfully", output)
        # Should mention Outlook or Office 365
        self.assertTrue("Outlook" in output or "Office 365" in output)

    def test_04_ambiguity_handling(self):
        print("\nRunning Test 4: Ambiguity Handling (LLM Interception)")
        output = run_cli_interaction(["My application froze and now I can't do my task."])
        
        # The AI should ask for clarification, NOT dump hundreds of systems
        self.assertNotIn("SYS-001", output) # Should not dump system IDs
        self.assertTrue(
            "specify" in output.lower() or 
            "which application" in output.lower() or 
            "which system" in output.lower() or
            "could not match" in output.lower()
        )

    def test_05_unsupported_system_rejection(self):
        print("\nRunning Test 5: Unsupported System Rejection")
        output = run_cli_interaction(["I need help with my personal Netflix account."])
        
        self.assertIn("OUT_OF_SCOPE_RESPONSE", output)
        self.assertTrue(
            "supported" in output.lower() or 
            "approved" in output.lower() or 
            "cannot" in output.lower() or
            "OpsPilot can help only with services" in output
        )

    def test_06_graceful_kb_failure(self):
        print("\nRunning Test 6: Graceful KB Failure (Offers Ticket)")
        output = run_cli_interaction(["How do I configure the new hyper-dimensional flux capacitor on my laptop?"])
        
        # Should gracefully fail the KB search and offer a ticket
        self.assertTrue(
            "ticket" in output.lower() or 
            "support" in output.lower() or 
            "raise" in output.lower()
        )
        # It shouldn't actually call the create tool yet
        self.assertNotIn("create_ticket_tool", output)

if __name__ == "__main__":
    unittest.main(verbosity=2)
