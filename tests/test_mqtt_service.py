"""Tests for MQTTService with mocked MQTT client."""

import json
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.mock_mqtt import MockMQTTClient


class TestMQTTService(unittest.TestCase):
    """Test cases for MQTTService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = None
        self.mock_client_class = None

        MockMQTTClient.reset_global_flags()

        def mock_mqtt_client_factory(*args, **kwargs):
            self.mock_client = MockMQTTClient(*args, **kwargs)
            return self.mock_client

        self.mock_client_class = MagicMock(side_effect=mock_mqtt_client_factory)

        self.patcher = patch.dict('sys.modules', {
            'umqtt': MagicMock(),
            'umqtt.simple': MagicMock(MQTTClient=self.mock_client_class)
        })
        self.patcher.start()

        if 'mqtt_service' in sys.modules:
            del sys.modules['mqtt_service']

        from mqtt_service import MQTTService
        self.MQTTService = MQTTService

        self.service = self.MQTTService(
            server="test.server.com",
            user="testuser",
            password="testpass",
            client_id="test_client_123"
        )

    def tearDown(self):
        """Clean up after tests."""
        MockMQTTClient.reset_global_flags()
        self.patcher.stop()
        if 'mqtt_service' in sys.modules:
            del sys.modules['mqtt_service']

    def test_initial_state(self):
        """Test that service initializes with correct default state."""
        # Arrange
        service = self.service

        # Act
        # (no action needed - testing initial state)

        # Assert
        self.assertFalse(service.connected)
        self.assertIsNone(service.state)
        self.assertEqual(service.consecutive_failures, 0)
        self.assertEqual(service.current_reconnect_delay, 5)

    def test_connect_and_subscribe_success(self):
        """Test successful connection and subscription."""
        # Arrange
        service = self.service

        # Act
        result = service.connect_and_subscribe()

        # Assert
        self.assertTrue(result)
        self.assertTrue(service.connected)
        self.assertTrue(self.mock_client.connected)
        self.assertEqual(self.mock_client.connect_call_count, 1)
        self.assertEqual(self.mock_client.subscribe_call_count, 1)
        self.assertIn(("msb/state", 0), self.mock_client.subscriptions)

    def test_connect_and_subscribe_failure(self):
        """Test connection failure handling."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)

        # Act
        result = self.service.connect_and_subscribe()

        # Assert
        self.assertFalse(result)
        self.assertFalse(self.service.connected)

    def test_keepalive_is_set(self):
        """Test that keepalive is properly configured."""
        # Arrange
        service = self.service

        # Act
        service.connect_and_subscribe()

        # Assert
        self.assertEqual(self.mock_client.keepalive, 60)

    def test_message_callback(self):
        """Test that messages are properly received and parsed."""
        # Arrange
        received_states = []
        self.service.add_listener(lambda state: received_states.append(state))
        self.service.connect_and_subscribe()
        test_state = {"status": "open", "time": "14:30"}
        self.mock_client.simulate_message("msb/state", json.dumps(test_state))

        # Act
        self.service.check_msg()

        # Assert
        self.assertEqual(len(received_states), 1)
        self.assertEqual(received_states[0], test_state)
        self.assertEqual(self.service.state, test_state)

    def test_message_callback_with_invalid_json(self):
        """Test handling of invalid JSON messages."""
        # Arrange
        received_states = []
        self.service.add_listener(lambda state: received_states.append(state))
        self.service.connect_and_subscribe()
        self.mock_client.simulate_message("msb/state", "invalid json {{{")

        # Act
        self.service.check_msg()

        # Assert
        self.assertEqual(len(received_states), 0)
        self.assertTrue(self.service.connected)

    def test_check_msg_triggers_reconnect_when_disconnected(self):
        """Test that check_msg attempts reconnection when not connected."""
        # Arrange
        self.assertFalse(self.service.connected)
        self.service.last_reconnect_attempt = 0

        # Act
        self.service.check_msg()

        # Assert
        self.assertTrue(self.service.connected)
        self.assertEqual(self.mock_client.connect_call_count, 1)

    def test_check_msg_failure_marks_disconnected(self):
        """Test that check_msg failure marks service as disconnected."""
        # Arrange
        self.service.connect_and_subscribe()
        self.assertTrue(self.service.connected)
        self.mock_client.check_msg_should_fail = True
        MockMQTTClient.set_global_connect_fail(True)

        # Act
        self.service.check_msg()

        # Assert
        self.assertFalse(self.service.connected)

    def test_reconnect_backoff_doubles_on_failure(self):
        """Test exponential backoff on reconnection failures."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        initial_delay = self.service.current_reconnect_delay
        self.service.last_reconnect_attempt = 0

        # Act
        self.service._handle_reconnect()

        # Assert
        self.assertEqual(self.service.current_reconnect_delay, initial_delay * 2)

    def test_reconnect_backoff_continues_exponentially(self):
        """Test that backoff continues to grow exponentially."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        initial_delay = self.service.current_reconnect_delay
        self.service.last_reconnect_attempt = 0
        self.service._handle_reconnect()
        self.service.last_reconnect_attempt = 0

        # Act
        self.service._handle_reconnect()

        # Assert
        self.assertEqual(self.service.current_reconnect_delay, initial_delay * 4)

    def test_reconnect_backoff_max_limit(self):
        """Test that backoff doesn't exceed maximum delay."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        self.service.current_reconnect_delay = 30
        self.service.last_reconnect_attempt = 0

        # Act
        self.service._handle_reconnect()

        # Assert
        self.assertEqual(
            self.service.current_reconnect_delay,
            self.service.max_reconnect_delay
        )

    def test_reconnect_delay_resets_on_success(self):
        """Test that delay resets after successful reconnection."""
        # Arrange
        self.service.current_reconnect_delay = 30
        self.service.consecutive_failures = 5

        # Act
        self.service.connect_and_subscribe()

        # Assert
        self.assertEqual(self.service.current_reconnect_delay, 5)
        self.assertEqual(self.service.consecutive_failures, 0)

    def test_should_attempt_reconnect_returns_false_within_delay(self):
        """Test that reconnection is blocked within delay interval."""
        # Arrange
        import time as real_time
        self.service.last_reconnect_attempt = real_time.time()
        self.service.current_reconnect_delay = 10

        # Act
        result = self.service._should_attempt_reconnect()

        # Assert
        self.assertFalse(result)

    def test_should_attempt_reconnect_returns_true_after_delay(self):
        """Test that reconnection is allowed after delay interval."""
        # Arrange
        import time as real_time
        self.service.last_reconnect_attempt = real_time.time() - 15
        self.service.current_reconnect_delay = 10

        # Act
        result = self.service._should_attempt_reconnect()

        # Assert
        self.assertTrue(result)

    def test_ping_success(self):
        """Test successful ping."""
        # Arrange
        self.service.connect_and_subscribe()

        # Act
        result = self.service.ping()

        # Assert
        self.assertTrue(result)
        self.assertEqual(self.mock_client.ping_call_count, 1)

    def test_ping_failure_marks_disconnected(self):
        """Test that ping failure marks service as disconnected."""
        # Arrange
        self.service.connect_and_subscribe()
        self.mock_client.ping_should_fail = True

        # Act
        result = self.service.ping()

        # Assert
        self.assertFalse(result)
        self.assertFalse(self.service.connected)

    def test_ping_when_not_connected_returns_false(self):
        """Test ping returns False when not connected."""
        # Arrange
        # (service starts disconnected)

        # Act
        result = self.service.ping()

        # Assert
        self.assertFalse(result)

    def test_is_connected_returns_false_initially(self):
        """Test is_connected returns False initially."""
        # Arrange
        # (service starts disconnected)

        # Act
        result = self.service.is_connected()

        # Assert
        self.assertFalse(result)

    def test_is_connected_returns_true_after_connect(self):
        """Test is_connected returns True after successful connection."""
        # Arrange
        self.service.connect_and_subscribe()

        # Act
        result = self.service.is_connected()

        # Assert
        self.assertTrue(result)

    def test_connection_listener_notified_on_connect(self):
        """Test that connection listeners are notified on connect."""
        # Arrange
        connection_events = []
        self.service.add_connection_listener(
            lambda connected: connection_events.append(connected)
        )

        # Act
        self.service.connect_and_subscribe()

        # Assert
        self.assertEqual(connection_events, [True])

    def test_connection_listener_notified_on_disconnect(self):
        """Test that connection listeners are notified on disconnect."""
        # Arrange
        connection_events = []
        self.service.add_connection_listener(
            lambda connected: connection_events.append(connected)
        )
        self.service.connect_and_subscribe()
        self.mock_client.check_msg_should_fail = True
        MockMQTTClient.set_global_connect_fail(True)

        # Act
        self.service.check_msg()

        # Assert
        self.assertEqual(connection_events, [True, False])

    def test_connection_listener_error_does_not_break_service(self):
        """Test that errors in connection listeners don't break service."""
        # Arrange
        def failing_listener(connected):
            raise Exception("Listener error")
        self.service.add_connection_listener(failing_listener)

        # Act
        self.service.connect_and_subscribe()

        # Assert
        self.assertTrue(self.service.connected)

    def test_multiple_listeners_all_receive_updates(self):
        """Test that multiple listeners all receive updates."""
        # Arrange
        states_1 = []
        states_2 = []
        self.service.add_listener(lambda s: states_1.append(s))
        self.service.add_listener(lambda s: states_2.append(s))
        self.service.connect_and_subscribe()
        test_state = {"status": "closed"}
        self.mock_client.simulate_message("msb/state", json.dumps(test_state))

        # Act
        self.service.check_msg()

        # Assert
        self.assertEqual(states_1, [test_state])
        self.assertEqual(states_2, [test_state])

    def test_get_state_returns_none_initially(self):
        """Test get_state returns None initially."""
        # Arrange
        # (no messages received yet)

        # Act
        result = self.service.get_state()

        # Assert
        self.assertIsNone(result)

    def test_get_state_returns_last_received_state(self):
        """Test get_state returns the last received state."""
        # Arrange
        self.service.connect_and_subscribe()
        test_state = {"status": "open"}
        self.mock_client.simulate_message("msb/state", json.dumps(test_state))
        self.service.check_msg()

        # Act
        result = self.service.get_state()

        # Assert
        self.assertEqual(result, test_state)

    def test_disconnect_called_before_reconnect(self):
        """Test that old connection is disconnected before reconnecting."""
        # Arrange
        self.service.connect_and_subscribe()
        first_client = self.mock_client

        # Act
        self.service.connect_and_subscribe()

        # Assert
        self.assertEqual(first_client.disconnect_call_count, 1)

    def test_disconnect_failure_does_not_prevent_reconnect(self):
        """Test that disconnect failure doesn't prevent new connection."""
        # Arrange
        self.service.connect_and_subscribe()
        self.mock_client.disconnect_should_fail = True

        # Act
        result = self.service.connect_and_subscribe()

        # Assert
        self.assertTrue(result)
        self.assertTrue(self.service.connected)

    def test_consecutive_failures_increment_on_failed_reconnect(self):
        """Test that consecutive failures are tracked."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        self.service.last_reconnect_attempt = 0

        # Act
        self.service._handle_reconnect()

        # Assert
        self.assertEqual(self.service.consecutive_failures, 1)

    def test_consecutive_failures_continue_incrementing(self):
        """Test that consecutive failures continue to increment."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        self.service.last_reconnect_attempt = 0
        self.service._handle_reconnect()
        self.service.last_reconnect_attempt = 0

        # Act
        self.service._handle_reconnect()

        # Assert
        self.assertEqual(self.service.consecutive_failures, 2)


class TestMQTTServiceIntegration(unittest.TestCase):
    """Integration-style tests for MQTTService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = None

        MockMQTTClient.reset_global_flags()

        def mock_mqtt_client_factory(*args, **kwargs):
            self.mock_client = MockMQTTClient(*args, **kwargs)
            return self.mock_client

        self.mock_client_class = MagicMock(side_effect=mock_mqtt_client_factory)

        self.patcher = patch.dict('sys.modules', {
            'umqtt': MagicMock(),
            'umqtt.simple': MagicMock(MQTTClient=self.mock_client_class)
        })
        self.patcher.start()

        if 'mqtt_service' in sys.modules:
            del sys.modules['mqtt_service']

        from mqtt_service import MQTTService
        self.service = MQTTService(
            server="test.server.com",
            user="testuser",
            password="testpass",
            client_id="test_client_123"
        )

    def tearDown(self):
        """Clean up after tests."""
        MockMQTTClient.reset_global_flags()
        self.patcher.stop()
        if 'mqtt_service' in sys.modules:
            del sys.modules['mqtt_service']

    def test_full_reconnection_cycle(self):
        """Test a complete connection -> disconnect -> reconnect cycle."""
        # Arrange
        connection_events = []
        states = []
        self.service.add_connection_listener(lambda c: connection_events.append(c))
        self.service.add_listener(lambda s: states.append(s))

        # Act - Phase 1: Initial connection
        self.service.connect_and_subscribe()

        # Assert - Phase 1
        self.assertEqual(connection_events, [True])

        # Act - Phase 2: Receive message
        self.mock_client.simulate_message("msb/state", json.dumps({"status": "open"}))
        self.service.check_msg()

        # Assert - Phase 2
        self.assertEqual(len(states), 1)

        # Arrange - Phase 3: Set up for connection loss
        self.mock_client.check_msg_should_fail = True
        MockMQTTClient.set_global_connect_fail(True)

        # Act - Phase 3: Connection lost
        self.service.check_msg()

        # Assert - Phase 3
        self.assertEqual(connection_events, [True, False])

        # Arrange - Phase 4: Allow reconnection
        MockMQTTClient.set_global_connect_fail(False)
        self.service.last_reconnect_attempt = 0

        # Act - Phase 4: Reconnection
        self.service.check_msg()

        # Assert - Phase 4
        self.assertEqual(connection_events, [True, False, True])

        # Act - Phase 5: Receive message after reconnect
        self.mock_client.simulate_message("msb/state", json.dumps({"status": "closed"}))
        self.service.check_msg()

        # Assert - Phase 5
        self.assertEqual(len(states), 2)

    def test_rapid_check_msg_calls_respect_backoff(self):
        """Test that rapid check_msg calls don't spam reconnection."""
        # Arrange
        MockMQTTClient.set_global_connect_fail(True)
        self.service.last_reconnect_attempt = 0

        # Act
        for _ in range(10):
            self.service.check_msg()

        # Assert
        self.assertEqual(self.mock_client.connect_call_count, 1)


if __name__ == '__main__':
    unittest.main()
