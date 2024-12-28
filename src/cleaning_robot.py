import time
import requests

from sympy import false

DEPLOYMENT = False  # This variable is to understand whether you are deploying on the actual hardware

try:
    import RPi.GPIO as GPIO
    import board
    import IBS
    DEPLOYMENT = True
except:
    import mock.GPIO as GPIO
    import mock.board as board
    import mock.ibs as IBS


class CleaningRobot:

    RECHARGE_LED_PIN = 12
    CLEANING_SYSTEM_PIN = 13
    INFRARED_PIN = 15

    # Wheel motor pins
    PWMA = 16
    AIN2 = 18
    AIN1 = 22

    # Rotation motor pins
    BIN1 = 29
    BIN2 = 31
    PWMB = 32
    STBY = 33

    N = 'N'
    S = 'S'
    E = 'E'
    W = 'W'

    LEFT = 'l'
    RIGHT = 'r'
    FORWARD = 'f'

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.INFRARED_PIN, GPIO.IN)
        GPIO.setup(self.RECHARGE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.CLEANING_SYSTEM_PIN, GPIO.OUT)

        GPIO.setup(self.PWMA, GPIO.OUT)
        GPIO.setup(self.AIN2, GPIO.OUT)
        GPIO.setup(self.AIN1, GPIO.OUT)
        GPIO.setup(self.PWMB, GPIO.OUT)
        GPIO.setup(self.BIN2, GPIO.OUT)
        GPIO.setup(self.BIN1, GPIO.OUT)
        GPIO.setup(self.STBY, GPIO.OUT)

        ic2 = board.I2C()
        self.ibs = IBS.IBS(ic2)

        self.pos_x = None
        self.pos_y = None
        self.heading = None

        self.recharge_led_on = False
        self.cleaning_system_on = False
        self.status = "Ready"

    def check_weather_and_adjust_mode(self):
        weather_data = self.get_weather_data()
        if weather_data and weather_data['weather'][0]['main'] == "Rain":
            self.status = "Rain detected. Stopping cleaning."
            # Logic to stop the robot or adjust behavior.

    def get_weather_data(self, city="Fisciano,IT"):
        try:
            response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Fisciano,IT&appid=939778a56a28085695d673d66ac26933")
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            self.status = f"Weather data fetch failed: {e}"
            return None


    def initialize_robot(self) -> None:
        self.pos_x = 0
        self.pos_y = 0
        self.heading = "N"

    def robot_status(self) -> str:
        return f"({self.pos_x},{self.pos_y},{self.heading})"

    def execute_command(self, command: str) -> str:
        obstacle_x = self.pos_x
        obstacle_y = self.pos_y
        if self.ibs.get_charge_left() < 10:
            GPIO.output(self.RECHARGE_LED_PIN, GPIO.HIGH)
            GPIO.output(self.CLEANING_SYSTEM_PIN, GPIO.LOW)
            self.cleaning_system_on = False
            self.recharge_led_on = True
            return "!" + self.robot_status()
        if command == self.FORWARD:
            if self.obstacle_found():
                if self.heading == self.N:
                    obstacle_y += 1
                elif self.heading == self.E:
                    obstacle_x += 1
                elif self.heading == self.W:
                    obstacle_x -= 1
                elif self.heading == self.S:
                    obstacle_y -= 1
                return f"{self.robot_status()}({obstacle_x},{obstacle_y})"
            self.activate_wheel_motor()
            if self.heading == self.N:
                self.pos_y += 1
            elif self.heading == self.E:
                self.pos_x += 1
            elif self.heading == self.W:
                self.pos_x -= 1
            elif self.heading == self.S:
                self.pos_y -= 1
        elif command == self.RIGHT:
            self.activate_rotation_motor(self.RIGHT)
            if self.heading == self.N:
                self.heading = self.E
            elif self.heading == self.E:
                self.heading = self.S
            elif self.heading == self.S:
                self.heading = self.W
            elif self.heading == self.W:
                self.heading = self.N
        elif command == self.LEFT:
            self.activate_rotation_motor(self.LEFT)
            if self.heading == self.N:
                self.heading = self.W
            elif self.heading == self.W:
                self.heading = self.S
            elif self.heading == self.S:
                self.heading = self.E
            elif self.heading == self.E:
                self.heading = self.N
        else:
            raise CleaningRobotError

    def obstacle_found(self) -> bool:
        return GPIO.input(self.INFRARED_PIN)

    def manage_cleaning_system(self) -> None:
        charge = self.ibs.get_charge_left()
        if charge > 10:
            GPIO.output(self.RECHARGE_LED_PIN, GPIO.LOW)
            GPIO.output(self.CLEANING_SYSTEM_PIN, GPIO.HIGH)
            self.cleaning_system_on = True
            self.recharge_led_on = False
        else:
            GPIO.output(self.RECHARGE_LED_PIN, GPIO.HIGH)
            GPIO.output(self.CLEANING_SYSTEM_PIN, GPIO.LOW)
            self.cleaning_system_on = False
            self.recharge_led_on = True

    def activate_wheel_motor(self) -> None:
        """
        Let the robot move forward by activating its wheel motor
        """
        # Drive the motor clockwise
        GPIO.output(self.AIN1, GPIO.HIGH)
        GPIO.output(self.AIN2, GPIO.LOW)
        # Set the motor speed
        GPIO.output(self.PWMA, GPIO.HIGH)
        # Disable STBY
        GPIO.output(self.STBY, GPIO.HIGH)

        if DEPLOYMENT: # Sleep only if you are deploying on the actual hardware
            time.sleep(1) # Wait for the motor to actually move

        # Stop the motor
        GPIO.output(self.AIN1, GPIO.LOW)
        GPIO.output(self.AIN2, GPIO.LOW)
        GPIO.output(self.PWMA, GPIO.LOW)
        GPIO.output(self.STBY, GPIO.LOW)

    def activate_rotation_motor(self, direction) -> None:
        """
        Let the robot rotate towards a given direction
        :param direction: "l" to turn left, "r" to turn right
        """
        if direction == self.LEFT:
            GPIO.output(self.BIN1, GPIO.HIGH)
            GPIO.output(self.BIN2, GPIO.LOW)
        elif direction == self.RIGHT:
            GPIO.output(self.BIN1, GPIO.LOW)
            GPIO.output(self.BIN2, GPIO.HIGH)

        GPIO.output(self.PWMB, GPIO.HIGH)
        GPIO.output(self.STBY, GPIO.HIGH)

        if DEPLOYMENT:  # Sleep only if you are deploying on the actual hardware
            time.sleep(1)  # Wait for the motor to actually move

        # Stop the motor
        GPIO.output(self.BIN1, GPIO.LOW)
        GPIO.output(self.BIN2, GPIO.LOW)
        GPIO.output(self.PWMB, GPIO.LOW)
        GPIO.output(self.STBY, GPIO.LOW)



class CleaningRobotError(Exception):
    pass
