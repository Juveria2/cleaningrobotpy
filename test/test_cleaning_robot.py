from unittest import TestCase
from unittest.mock import Mock, patch, call

from mock import GPIO
from mock.ibs import IBS
from src.cleaning_robot import CleaningRobot, CleaningRobotError


class TestCleaningRobot(TestCase):

    def test_initialize_robot(self):
        system = CleaningRobot()
        system.initialize_robot()
        self.assertEqual(system.robot_status(),"(0,0,N)")

    @patch.object(IBS, "get_charge_left")
    @patch.object(GPIO, "output")
    def test_manage_cleaning_system_is_greater_than_10(self, mock: Mock, mock_ibs: Mock):
        system = CleaningRobot()
        mock_ibs.return_value = 11
        system.manage_cleaning_system()
        mock.assert_has_calls([call(system.RECHARGE_LED_PIN, GPIO.LOW), call(system.CLEANING_SYSTEM_PIN, GPIO.HIGH)])

    @patch.object(IBS, "get_charge_left")
    @patch.object(GPIO, "output")
    def test_manage_cleaning_system_is_equal_or_less_than_10(self, mock: Mock, mock_ibs: Mock):
        system = CleaningRobot()
        mock_ibs.return_value = 9
        system.manage_cleaning_system()
        mock.assert_has_calls([call(system.RECHARGE_LED_PIN, GPIO.HIGH), call(system.CLEANING_SYSTEM_PIN, GPIO.LOW)])

    def test_movement_to_forward(self):
        system = CleaningRobot()
        system.initialize_robot()
        system.execute_command(system.FORWARD)
        self.assertEqual(system.robot_status(), "(0,1,N)")

    def test_movement_to_right(self):
        system = CleaningRobot()
        system.initialize_robot()
        system.execute_command(system.RIGHT)
        self.assertEqual(system.robot_status(), "(0,0,E)")

    def test_movement_to_left(self):
        system = CleaningRobot()
        system.initialize_robot()
        system.execute_command(system.LEFT)
        self.assertEqual(system.robot_status(), "(0,0,W)")

    def test_no_movement(self):
        system = CleaningRobot()
        system.initialize_robot()
        self.assertRaises(CleaningRobotError, system.execute_command, "X")
