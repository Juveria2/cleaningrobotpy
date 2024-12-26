from unittest import TestCase
from unittest.mock import Mock, patch, call

from mock import GPIO
from mock.ibs import IBS
from src.cleaning_robot import CleaningRobot


class TestCleaningRobot(TestCase):

    def test_initialize_robot(self):
        system = CleaningRobot()
        system.initialize_robot()
        self.assertEqual(system.robot_status(),"(0,0,N)")


