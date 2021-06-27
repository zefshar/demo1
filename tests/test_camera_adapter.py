from fsa.basic.camera.mipi_camera import MipiCamera
from fsa.basic.camera import THROTTLED_PATTERN
from fsa.basic.camera.mock_camera import GPU_TEMPERATURE_PATTERN
from os.path import join, exists
from os import mkdir
from shutil import copy

from fsa.model.camera_type import CameraType
from fsa.basic.camera_adapter import CameraAdapter
from fsa.basic.statistics_manager import StatisticsManager
from fsa.model.sensor_agent_configuration import SensorAgentConfiguration
from tests.test_sensor_agent import TestSensorAgent, SENSOR_INI


class TestCameraAdapter(TestSensorAgent):

    def setUp(self) -> None:
        super().setUp()
        # Copy create init file for test
        copy(
            join(self.project_root, 'sensor.ini.example'),
            join(self.basic_folder, SENSOR_INI)
        )
        # COPY BLANK IMAGE FOR MOCK CAMERA
        copy(
            join(self.project_root, 'tests', 'white-color-1920x1080.png'),
            join(self.data_folder, 'white-color-1920x1080.png')
        )

    def test_get_image_and_metadata(self):
        sensor_agent_configuration = SensorAgentConfiguration('sensor.ini')
        sensor_agent_configuration.set_support_mode(False)
        statistics_manager = StatisticsManager(sensor_agent_configuration)

        camera_adapter = CameraAdapter(CameraType.Mock, sensor_agent_configuration, statistics_manager)
        self.assertIsNotNone(camera_adapter.get_image_and_metadata())

    def test_gpu_temperature_pattern(self):
        self.assertTrue(GPU_TEMPERATURE_PATTERN.match('31.0\'C'))
        self.assertTrue(GPU_TEMPERATURE_PATTERN.match('31C'))
        self.assertTrue(GPU_TEMPERATURE_PATTERN.match('0.1*C'))

    def test_throttled_pattern(self):
        self.assertTrue(THROTTLED_PATTERN.match('0x1000'))
        self.assertTrue(THROTTLED_PATTERN.match('0x40002'))
        self.assertTrue(THROTTLED_PATTERN.match('0x0'))
        self.assertTrue(THROTTLED_PATTERN.match('throttled=0x'))
        self.assertTrue(str(int(THROTTLED_PATTERN.match('0x20000').group(1), 16)), '132072')
        self.assertEquals(int(f'{int(THROTTLED_PATTERN.match("0x20000").group(1), 16):b}'), 100000000000000000)
        self.assertEquals(int(f'{int(THROTTLED_PATTERN.match("0x0").group(1), 16):b}'), 0)

    def test_get_throttled(self):
        self.assertEquals(MipiCamera._bit_representation(int(THROTTLED_PATTERN.match('0x20000').group(1), 16)), 100000)
        self.assertEquals(MipiCamera._bit_representation(int(THROTTLED_PATTERN.match('0x20001').group(1), 16)), 100001)
