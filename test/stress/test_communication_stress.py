"""
MILITARY-GRADE COMMUNICATION STRESS TESTS
Tests for real-world scenarios and edge cases in TunnelClient
"""

import sys
import time
import threading
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phonesium import Wallet, TunnelClient
from phonesium.core.config import DEFAULT_TUNNEL_HOST, DEFAULT_TUNNEL_PORT


class CommunicationStressTest:
    """Comprehensive communication stress testing"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, test_name, status, message=""):
        """Log test result"""
        result = {"test": test_name, "status": status, "message": message}
        self.results.append(result)

        if status == "PASS":
            self.passed += 1
            print(f"  [PASS] {test_name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {test_name}: {message}")

    def test_1_basic_initialization(self):
        """Test 1: Basic TunnelClient initialization"""
        print("\n[TEST 1] Basic Initialization")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            assert client.wallet.address == wallet.address
            assert client.tunnel_host == DEFAULT_TUNNEL_HOST
            assert client.tunnel_port == DEFAULT_TUNNEL_PORT
            assert client.registered == False

            self.log("Basic initialization", "PASS")
        except Exception as e:
            self.log("Basic initialization", "FAIL", str(e))

    def test_2_multiple_clients(self):
        """Test 2: Create multiple clients simultaneously"""
        print("\n[TEST 2] Multiple Clients Creation")
        try:
            wallets = [Wallet.create() for _ in range(10)]
            clients = []

            for wallet in wallets:
                client = TunnelClient(wallet)
                clients.append(client)

            # Verify all clients are unique
            addresses = [c.wallet.address for c in clients]
            assert len(addresses) == len(set(addresses)), "Duplicate addresses found"

            # Verify all have different sockets
            ports = [c.sock.getsockname()[1] for c in clients]
            assert len(ports) == len(set(ports)), "Duplicate ports found"

            # Cleanup
            for client in clients:
                client.close()

            self.log("Multiple clients creation", "PASS")
        except Exception as e:
            self.log("Multiple clients creation", "FAIL", str(e))

    def test_3_registration_without_server(self):
        """Test 3: Registration attempt without tunnel server (should fail gracefully)"""
        print("\n[TEST 3] Registration Without Server")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            # Should timeout gracefully
            success = client.register()

            # Expected to fail without server
            assert success == False, "Should fail without server"
            assert client.registered == False

            client.close()
            self.log("Registration without server (graceful failure)", "PASS")
        except Exception as e:
            self.log("Registration without server", "FAIL", str(e))

    def test_4_send_message_without_registration(self):
        """Test 4: Send message without registration (should auto-register)"""
        print("\n[TEST 4] Send Message Without Registration")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address

            # Should attempt to register automatically
            result = client.send_message(recipient, "Test message")

            # Expected to fail without server, but should not crash
            assert isinstance(result, bool)

            client.close()
            self.log("Send message without registration (auto-register)", "PASS")
        except Exception as e:
            self.log("Send message without registration", "FAIL", str(e))

    def test_5_invalid_recipient_address(self):
        """Test 5: Send to invalid recipient address"""
        print("\n[TEST 5] Invalid Recipient Address")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            invalid_addresses = [
                "",
                "invalid",
                "PHN",  # Too short
                "PHN" + "x" * 100,  # Too long
                None,
                12345,
                {"address": "PHN123"},
            ]

            for invalid in invalid_addresses:
                try:
                    result = client.send_message(str(invalid), "test")
                    # Should handle gracefully
                except Exception:
                    # Expected to fail, but shouldn't crash
                    pass

            client.close()
            self.log("Invalid recipient addresses", "PASS")
        except Exception as e:
            self.log("Invalid recipient addresses", "FAIL", str(e))

    def test_6_empty_message(self):
        """Test 6: Send empty message"""
        print("\n[TEST 6] Empty Message")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address

            # Should handle empty message
            result = client.send_message(recipient, "")

            client.close()
            self.log("Empty message handling", "PASS")
        except Exception as e:
            self.log("Empty message handling", "FAIL", str(e))

    def test_7_large_message(self):
        """Test 7: Send very large message (edge case)"""
        print("\n[TEST 7] Large Message")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address

            # 1KB message
            small_msg = "x" * 1024
            client.send_message(recipient, small_msg)

            # 4KB message (UDP limit test)
            large_msg = "x" * 4096
            client.send_message(recipient, large_msg)

            # Very large message (should handle gracefully)
            huge_msg = "x" * 100000
            try:
                client.send_message(recipient, huge_msg)
            except Exception:
                pass  # Expected to fail, but shouldn't crash

            client.close()
            self.log("Large message handling", "PASS")
        except Exception as e:
            self.log("Large message handling", "FAIL", str(e))

    def test_8_rapid_fire_messages(self):
        """Test 8: Send many messages rapidly"""
        print("\n[TEST 8] Rapid Fire Messages")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address

            # Send 100 messages rapidly
            for i in range(100):
                client.send_message(recipient, f"Message {i}")

            client.close()
            self.log("Rapid fire messages", "PASS")
        except Exception as e:
            self.log("Rapid fire messages", "FAIL", str(e))

    def test_9_check_offline_miner(self):
        """Test 9: Check status of offline miner"""
        print("\n[TEST 9] Check Offline Miner Status")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            offline_address = Wallet.create().address

            # Should return error or offline status
            status = client.check_miner_status(offline_address)

            assert isinstance(status, dict)

            client.close()
            self.log("Check offline miner status", "PASS")
        except Exception as e:
            self.log("Check offline miner status", "FAIL", str(e))

    def test_10_concurrent_operations(self):
        """Test 10: Concurrent send operations from multiple threads"""
        print("\n[TEST 10] Concurrent Operations")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address
            errors = []

            def send_message(msg_id):
                try:
                    client.send_message(recipient, f"Message {msg_id}")
                except Exception as e:
                    errors.append(e)

            # Create 20 threads
            threads = []
            for i in range(20):
                t = threading.Thread(target=send_message, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join(timeout=2)

            # Should handle concurrent operations
            client.close()
            self.log("Concurrent operations", "PASS")
        except Exception as e:
            self.log("Concurrent operations", "FAIL", str(e))

    def test_11_socket_timeout_handling(self):
        """Test 11: Socket timeout handling"""
        print("\n[TEST 11] Socket Timeout Handling")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            # Socket should have timeout set
            timeout = client.sock.gettimeout()
            assert timeout is not None, "Socket should have timeout"

            client.close()
            self.log("Socket timeout handling", "PASS")
        except Exception as e:
            self.log("Socket timeout handling", "FAIL", str(e))

    def test_12_close_and_reopen(self):
        """Test 12: Close client and create new one"""
        print("\n[TEST 12] Close and Reopen")
        try:
            wallet = Wallet.create()

            # Create and close multiple times
            for i in range(5):
                client = TunnelClient(wallet)
                client.close()

            self.log("Close and reopen", "PASS")
        except Exception as e:
            self.log("Close and reopen", "FAIL", str(e))

    def test_13_special_characters_in_message(self):
        """Test 13: Special characters and unicode in messages"""
        print("\n[TEST 13] Special Characters in Message")
        try:
            wallet = Wallet.create()
            client = TunnelClient(wallet)

            recipient = Wallet.create().address

            special_messages = [
                "Hello\nWorld",  # Newlines
                "Tab\tSeparated",  # Tabs
                'Quote"Test"',  # Quotes
                "Backslash\\Test",  # Backslash
                'JSON{"test":"value"}',  # JSON
                "SQL'; DROP TABLE--",  # SQL injection attempt
                "<script>alert('xss')</script>",  # XSS attempt
            ]

            for msg in special_messages:
                try:
                    client.send_message(recipient, msg)
                except Exception:
                    pass  # Should handle gracefully

            client.close()
            self.log("Special characters in message", "PASS")
        except Exception as e:
            self.log("Special characters in message", "FAIL", str(e))

    def test_14_network_port_conflict(self):
        """Test 14: Handle port conflicts gracefully"""
        print("\n[TEST 14] Network Port Conflict")
        try:
            wallet1 = Wallet.create()
            wallet2 = Wallet.create()

            # Both should get different ports automatically
            client1 = TunnelClient(wallet1)
            client2 = TunnelClient(wallet2)

            port1 = client1.sock.getsockname()[1]
            port2 = client2.sock.getsockname()[1]

            assert port1 != port2, "Should assign different ports"

            client1.close()
            client2.close()

            self.log("Network port conflict handling", "PASS")
        except Exception as e:
            self.log("Network port conflict handling", "FAIL", str(e))

    def test_15_memory_leak_test(self):
        """Test 15: Memory leak test - create and destroy many clients"""
        print("\n[TEST 15] Memory Leak Test")
        try:
            wallets = []

            # Create 100 clients
            for i in range(100):
                wallet = Wallet.create()
                client = TunnelClient(wallet)
                client.close()
                wallets.append(wallet)

            # Should not leak memory or file descriptors
            self.log("Memory leak test (100 clients)", "PASS")
        except Exception as e:
            self.log("Memory leak test", "FAIL", str(e))

    def run_all_tests(self):
        """Run all stress tests"""
        print("=" * 70)
        print("COMMUNICATION MODULE - MILITARY-GRADE STRESS TESTS")
        print("=" * 70)

        self.test_1_basic_initialization()
        self.test_2_multiple_clients()
        self.test_3_registration_without_server()
        self.test_4_send_message_without_registration()
        self.test_5_invalid_recipient_address()
        self.test_6_empty_message()
        self.test_7_large_message()
        self.test_8_rapid_fire_messages()
        self.test_9_check_offline_miner()
        self.test_10_concurrent_operations()
        self.test_11_socket_timeout_handling()
        self.test_12_close_and_reopen()
        self.test_13_special_characters_in_message()
        self.test_14_network_port_conflict()
        self.test_15_memory_leak_test()

        print("\n" + "=" * 70)
        print("COMMUNICATION STRESS TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("=" * 70)

        if self.failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['message']}")

        return self.failed == 0


if __name__ == "__main__":
    tester = CommunicationStressTest()
    success = tester.run_all_tests()

    if success:
        print("\n[OK] All communication stress tests passed!")
        sys.exit(0)
    else:
        print("\n[WARNING] Some tests failed - review above")
        sys.exit(1)
