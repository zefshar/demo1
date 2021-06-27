import io
import json
import logging
import socketserver
import time
import threading
from threading import Condition, RLock
from http import server
import mmap
import tarfile
import urllib
import datetime
# import av
import random
import traceback
import threading

from typing import List, Tuple, Iterable

import cv2
import numpy as np

import re

from fsa.basic.camera_adapter import CameraAdapter
from fsa.basic.data_manager import DataManager
from fsa.errors.sensor_agent_error import SensorAgentError
from fsa.model.sensor_agent_configuration import SensorAgentConfiguration
from fsa.model.events.change_active_leds_event import ChangeActiveLedsEvent
from fsa.model.events.sensor_agent_configuration_flush_event import SensorAgentConfigurationFlushEvent
from fsa.version.sensor_agent_version import SensorAgentVersion
from fsa.basic.statistics_manager import StatisticsManager
from fsa.basic.external.leds_manager import LedsManager
import os
import collections
import math as m

from datetime import datetime
from ev.event import event
from ev.observer import observer
import importlib
from swtp.swtp_request_handler import SwtpRequestHandler


SENSOR_AGENT_CONFIGURATION_DOES_NOT_SET = 'Sensor agent configuration does not set'
APPLICATION_JSON = 'application/json'


class MjpegStreamingOutput(object):
    def __init__(self, width: int, height: int, fps: float):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame = None
        self.time = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):  # The next jpeg
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            if self.condition.acquire(True, timeout=1):
                try:
                    self.frame = self.buffer.getvalue()
                    self.time = time.time()
                    self.condition.notify_all()
                finally:
                    self.condition.release()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class H264StreamingOutput(object):
    def __init__(self, width: int, height: int, fps: float, chunk_size=4096):  # b'\x4D\x34\x56\x20' 
        self.width = width
        self.height = height
        self.fps = fps
        self.data = b''
        self.time = None
        self.buffer = io.BytesIO()
        self.data_ready = Condition()
        self.data_ask = Condition()
        self.len = 0
        self.chunk_size = chunk_size

    def write(self, buf):
        if not buf:
            self.buffer.truncate()
            content = self.buffer.getvalue()

            if self.data_ask.acquire(True, timeout=1):
                try:
                    self.data_ask.wait(3)
                finally:
                    self.data_ask.release()
            if self.data_ready.acquire(True, timeout=1):
                try:
                    self.data = content + buf
                    self.time = time.time()
                    self.data_ready.notify_all()
                finally:
                    self.data_ready.release()

            self.buffer.seek(0)
            self.len = 0

            if self.data_ask.acquire(True, timeout=1):
                try:
                    self.data_ask.wait(3)
                finally:
                    self.data_ask.release()
            if self.data_ready.acquire(True, timeout=1):
                try:
                    self.data = b''
                    self.data_ready.notify_all()
                finally:
                    self.data_ready.release()

        part = buf[:]
        pos = part.find(b'\x00\x00\x00\x01')  # NAL Boundary
        while pos != -1 and self.len >= self.chunk_size:  # The next NAL
            # New chunk, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            content = self.buffer.getvalue()
            if self.data_ask.acquire(True, timeout=1):
                try:
                    self.data_ask.wait(3)
                finally:
                    self.data_ask.release()
            if self.data_ready.acquire(True, timeout=1):
                try:
                    _data = content + part[:pos]  # binary h264 stream
                    self.data = _data
                    # print(f'Write data is : {len(_data)}')
                    self.time = time.time()
                    self.data_ready.notify_all()
                finally:
                    self.data_ready.release()
            self.buffer.seek(0)
            self.buffer.write(part[pos:])
            self.len = 0

            part = part[pos:]

            pos = part.find(b'\x00\x00\x00\x01')

        self.len += len(part)
        return self.buffer.write(part)


class Mp4Remuxer(object):

    def __init__(self, h264streaming_output, writer, debug_writer=None, read_size=4096):
        self._h264streaming_output = h264streaming_output
        self._writer = writer
        self._debug_writer = debug_writer
        self._input = None
        self._output = None
        self._read_size = read_size
        self.__initial_nals = b'\x00\x00\x00\x01\x27\x64\x00\x28\xAC\x2B\x40\xA0\xFD\x00\xF1\x22\x6A\x00\x00\x00\x01\x28\xEE\x01\x0F\x2C'

    def close(self):
        if self._input:
            self._input.close()
        if self._output:
            self._output.close()

    def read(self, buf_size=4096):
        if self.__initial_nals:
            buf = self.__initial_nals
            self.__initial_nals = b''
        else:
            buf = b''
        while len(buf) < self._read_size:
            if self._h264streaming_output.data_ask.acquire(True, timeout=1):
                try:
                    self._h264streaming_output.data_ask.notify_all()
                finally:
                    self._h264streaming_output.data_ask.release()
            if self._h264streaming_output.data_ready.acquire(True, timeout=1):
                try:
                    self._h264streaming_output.data_ready.wait(3)
                    _data = self._h264streaming_output.data
                    # print(f'Read data is : {len(_data)}')
                    if _data is not None and len(_data) > 0:
                        buf += _data
                    else:
                        break
                finally:
                    self._h264streaming_output.data_ready.release()
        # print(f'Buf len is : {len(buf)}')
        return buf

    def write(self, buf):
        if self._writer:
            self._writer(buf)
        if self._debug_writer:
            self._debug_writer(buf)

    def remux(self, break_expression):
        open_method = getattr(
            importlib.import_module('av'),
            'open')
        self._input = open_method(self, format='h264', options={
            'pix_fmt': 'yuv420p',
            'width': str(self._h264streaming_output.width),
            'height': str(self._h264streaming_output.height)
        })
        in_stream = self._input.streams.video[0]
        # in_stream = self._input.add_stream('h264')
        #in_stream.pix_fmt = 'yuv420p'
        #in_stream.width = self._h264streaming_output.width
        #in_stream.height = self._h264streaming_output.height
        #in_stream.options = {}

        self._output = open_method(self, 'w', format='ismv')  # like mp4
        self._output.add_stream('libx264', options={
            'profile': 'Main',
            'movflags': 'frag_keyframe+empty_moov'
        })

        dts = .0
        for p in self._input.demux(in_stream):
            if break_expression():
                return
            # print(p)
            p.dts = (dts / in_stream.time_base) / self._h264streaming_output.fps
            p.pts = (dts / in_stream.time_base) / self._h264streaming_output.fps
            # We need to assign the packet to the new stream.
            self._output.mux(p)
            dts += 1


@observer
class SensorStateController(object):

    def __init__(self, sensor_agent_configuration: SensorAgentConfiguration,
        data_manager: DataManager, camera_adapter: CameraAdapter, leds_manager: LedsManager) -> None:
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.released = False

        self.sensor_agent_configuration = sensor_agent_configuration
        self.data_manager = data_manager
        self.statistics_manager = None
        self.camera_adapter = camera_adapter
        self.leds_manager = leds_manager
        self.blank_image = None

        self.live_stream_width = 320
        self.live_stream_height = 240
        self.live_stream_frame_rate = 33  # It's hard preset for Pi Camera

        self.mjpeg_streaming_output = MjpegStreamingOutput(self.live_stream_width, self.live_stream_height, self.live_stream_frame_rate)
        self.h264_streaming_output = H264StreamingOutput(self.live_stream_width, self.live_stream_height, self.live_stream_frame_rate)

        self.__active_leds = self.leds_manager.get_active_leds()
        self.__support_mode = self.sensor_agent_configuration.get_support_mode()

    def is_support_mode(self, support_mode: bool or datetime) -> bool:
        return not(str(support_mode) == 'False')

    def get_status(self) -> dict:
        result = dict()
        result['sensor_agent_version'] = SensorAgentVersion.standard()
        if self.sensor_agent_configuration:
            support_mode = self.sensor_agent_configuration.get_support_mode()
            result['support_mode'] = self.is_support_mode(support_mode)
            result['support_mode_as_str'] = str(support_mode)
            result['disable_camera_in_support_mode'] = self.sensor_agent_configuration.get_disable_camera_in_support_mode()
            result['sensor_id'] = self.sensor_agent_configuration.get_sensor_id()
            result['compress_to_mp4_before_send'] = self.sensor_agent_configuration.get_compress_to_mp4_before_send()
            result['ai_filter_mode'] = str(self.sensor_agent_configuration.get_ai_filter_mode())
            result['camera_type'] = str(self.sensor_agent_configuration.get_camera_type())
            result['active_leds'] = self.leds_manager.get_active_leds()
            result['daylights'] = str(self.sensor_agent_configuration.get_camera_daylights_constraints())
        if self.data_manager:
            image_files_count, video_files_count, first_id = self.data_manager.get_buffer_info()
            result['buffer_size_images'] = image_files_count
            result['buffer_size_videos'] = video_files_count
            result['first_image_datetime'] = self._extract_date_time(first_id)
        if self.statistics_manager:
            result['average_ai_filter_duration'] = self.statistics_manager.get_average_ai_filter_duration()
            result['ai_filter_rate_percent'] = self.statistics_manager.get_ai_filter_rate_percent()
            result['ai_filter_duration_100'] = self.statistics_manager.get_ai_filter_duration_100()
            result['ai_filter_rate_percent_1000'] = self.statistics_manager.get_ai_filter_rate_percent_1000()
            result['average_capture_duration'] = self.statistics_manager.get_average_capture_duration()
            result['camera_captures'] = self.statistics_manager.get_camera_captures()
            result['ai_inferences'] = self.statistics_manager.get_ai_filter_inferences()
            result['average_db_persist_image_duration'] = self.statistics_manager.get_average_db_persist_image_duration()
            result['db_persist_images'] = self.statistics_manager.get_db_persist_images()
        return result

    @staticmethod
    def _extract_date_time(metadata_id: list) -> str:
        if metadata_id:
            matcher = re.search(
                r'^(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)', metadata_id[0])
            if matcher:
                return '%s-%s-%sT%s:%s:%sZ' % (matcher.group(1), matcher.group(2), matcher.group(3), matcher.group(4), matcher.group(5), matcher.group(6))
        return ''

    def set_support_mode(self, support_mode: bool or datetime):
        try:
            if not self.sensor_agent_configuration:
                raise SensorAgentError(SENSOR_AGENT_CONFIGURATION_DOES_NOT_SET)

            self.__support_mode = self.sensor_agent_configuration.get_support_mode()
            if self.__support_mode == support_mode:
                return

            self.__support_mode = support_mode # For websocket we need to set internal state before change configuration
            self.__active_leds = self.sensor_agent_configuration.get_active_leds() # Re get from configuration
            self.sensor_agent_configuration.set_support_mode(support_mode)

            if support_mode and not self.sensor_agent_configuration.get_disable_camera_in_support_mode():
                self.__start_recording()
            else:
                self.__stop_recording()

            self.sensor_agent_configuration.flush()

            self.__active_leds = self.sensor_agent_configuration.get_active_leds()

        except Exception as e:
            self.logger.error(f'{"Start" if support_mode else "Stop"} recording error: {e}', e, exc_info=True)
            raise e

    def set_disable_camera(self):
        if not self.sensor_agent_configuration:
            raise SensorAgentError(SENSOR_AGENT_CONFIGURATION_DOES_NOT_SET)

        self.sensor_agent_configuration.set_disable_camera_in_support_mode(True)

        self.sensor_agent_configuration.flush()

        if self.is_support_mode(self.sensor_agent_configuration.get_support_mode()):
            self.__stop_recording()


    def set_enable_camera(self):
        if not self.sensor_agent_configuration:
            raise SensorAgentError(SENSOR_AGENT_CONFIGURATION_DOES_NOT_SET)

        self.sensor_agent_configuration.set_disable_camera_in_support_mode(False)

        self.sensor_agent_configuration.flush()

        if self.is_support_mode(self.sensor_agent_configuration.get_support_mode()):
            self.__start_recording()

    def set_led_status_active(self, led_numbers: List[int], is_active: bool):
        if not self.sensor_agent_configuration:
            raise SensorAgentError(SENSOR_AGENT_CONFIGURATION_DOES_NOT_SET)

        if not self.is_support_mode(self.sensor_agent_configuration.get_support_mode()):
            return

        has_changes = False
        self.__active_leds = self.leds_manager.get_active_leds()
        active_leds = self.__active_leds
        for led_number in led_numbers:

            if is_active and led_number not in active_leds:
                active_leds.append(led_number)
                has_changes = True

            if not is_active and led_number in active_leds:
                active_leds.remove(led_number)
                has_changes = True

        if has_changes:
            self.__active_leds = self.leds_manager.get_active_leds()
            self.fire_change_active_leds_event(active_leds)

    @event
    def fire_change_active_leds_event(self, led_numbers: List[int]) -> ChangeActiveLedsEvent:
        return ChangeActiveLedsEvent(led_numbers)

    def start(self):
        if self.is_support_mode(self.sensor_agent_configuration.get_support_mode()) and not self.sensor_agent_configuration.get_disable_camera_in_support_mode():
            self.__start_recording()
        else:
            self.__write_blank_image()

    def release(self):
        try:
            self.__stop_recording()
        except Exception as e:
            self.logger.error('Stop recording error: %s', e, exc_info=True)
        finally:
            self.__write_blank_image()

        with self.mjpeg_streaming_output.condition:
            self.mjpeg_streaming_output.condition.notify_all()
        with self.h264_streaming_output.data_ask:
            self.h264_streaming_output.data_ask.notify_all()
        with self.h264_streaming_output.data_ready:
            self.h264_streaming_output.data_ready.notify_all()
        self.released = True

    def browser_error(self, error: str):
        self.logger.error(urllib.parse.unquote(error))

    def browser_warn(self, error: str):
        self.logger.warn(urllib.parse.unquote(error))

    def browser_log(self, error: str):
        self.logger.info(urllib.parse.unquote(error))

    def __write_blank_image(self):
        if not self.blank_image:
            self.blank_image = np.zeros(
                (self.live_stream_height, self.live_stream_width, 3), np.uint8)
            rgb_color = (255, 255, 255)  # White color RGB
            self.blank_image[:] = tuple(reversed(rgb_color))
            _, buffer = cv2.imencode(".jpg", self.blank_image)
            self.blank_image = buffer.tobytes()
        self.mjpeg_streaming_output.write(self.blank_image)
        self.mjpeg_streaming_output.write(self.blank_image)

    def __start_recording(self):
        if not self.camera_adapter:
            return
        self.camera_adapter.start_recording(self.mjpeg_streaming_output,
                                    self.h264_streaming_output,
                                    resolution_width=self.live_stream_width,
                                    resolution_height=self.live_stream_height,
                                    frame_rate=self.live_stream_frame_rate)

    def __stop_recording(self):
        if not self.camera_adapter:
            return
        self.camera_adapter.stop_recording()
        self.__write_blank_image()

    def _on_flush_configuration(self, event: SensorAgentConfigurationFlushEvent):
        SwtpRequestHandler.webtopics_processor.send('MAIN', json.dumps(self.get_status()).encode('utf-8'))

    def _on_change_active_leds_event(self, event: ChangeActiveLedsEvent):
        SwtpRequestHandler.webtopics_processor.send('MAIN', json.dumps(self.get_status()).encode('utf-8'))


class IntegerStat(object):

    def __init__(self, cap: int = 10):
        self.__cap = cap
        self.__deque = collections.deque(maxlen=cap)

    def update(self, value: int = 0):
        self.__deque.append((datetime.timestamp(datetime.utcnow()), value))

    def update_with_time(self, key: float, value: int = 0):
        self.__deque.append((key, value))

    def __len__(self):
        return self.__cap

    def __getitem__(self, index: int):
        return self.__deque[index]


class FpsController(object):

    def __init__(self, initial_fps: float, cap: int  = 10):
        self.__initial_fps = initial_fps
        self.__fps = initial_fps
        self.__lock = RLock()
        self.__deque = collections.deque(maxlen=cap)

    def set_fps(self, fps: float, timeout: float = 3):
        if fps == 0:
            raise SensorAgentError(f'Fps can not set to zero')
        if fps < 0:
            raise SensorAgentError(f'Fps can not be negative')

        if self.__lock.acquire(True, timeout):
            try:
                self.__fps = fps
            finally:
                self.__lock.release()
        else:
            raise SensorAgentError(f'Acquire lock timeout {timeout}s, other args: {fps}')

    def get_initial_fps(self):
        return self.__initial_fps

    def get_fps(self):
        return self.__fps

    def wait(self, max_timeout: float = None, lock_timeout: float = 3):
        if self.__lock.acquire(True, lock_timeout):
            try:
                self.__deque.append(datetime.timestamp(datetime.utcnow()))
                count = len(self.__deque)
                if count < 2:
                    return
                timeout = (count / self.__fps) - (self.__deque[-1] - self.__deque[0])
                if timeout <= 0:
                    return
                if max_timeout is not None:
                    timeout = min(timeout, max_timeout)
                time.sleep(timeout)
            finally:
                self.__lock.release()
        else:
            raise SensorAgentError(f'Acquire lock timeout {lock_timeout}s, other args: {max_timeout}')

    def is_drop(self, max_timeout: float = None, lock_timeout: float = 3):
        if self.__lock.acquire(True, timeout=lock_timeout):
            try:
                count = len(self.__deque)
                if count < 2:
                    self.__deque.append(datetime.timestamp(datetime.utcnow()))
                    return False
                dropped = False
                stamp = datetime.timestamp(datetime.utcnow())

                # print(f'len/fps = {len(self.__deque) / self.__fps}, real fps is {len(self.__deque) / (self.__deque[-1] - self.__deque[0])}, delta is {stamp - self.__deque[0]}')
                dropped = ((count + 1) / self.__fps) > (stamp - self.__deque[0]) or (stamp - self.__deque[-1] < 1 / self.__fps)
                if not dropped:
                    self.__deque.append(datetime.timestamp(datetime.utcnow()))

                return dropped
            finally:
                self.__lock.release()
        else:
            raise SensorAgentError(f'Acquire lock timeout {lock_timeout}s, other args: {max_timeout}')


class IntegerStatQuantifier(object):

    def __init__(self, fps: float, time_value_sequence: Iterable[Tuple[float, int]]):
        self.__sequence = time_value_sequence
        self.__fps = fps

    def quantize(self) -> List[Tuple[float, int]]:
        result = []
        quant = 1 / self.__fps
        prev_point = None
        for tv in self.__sequence:
            if prev_point is None:
                result.append(tv)
                prev_point = tv
                continue
            t0, v0 = prev_point
            t, v = tv
            if (t - t0) > quant:
                quant_count = int((t - t0) // quant)
                quant_delta_value = (v - v0) / quant_count
                for i in range(0, quant_count):
                    result.append((t0 + (i + 1) * quant, m.floor(v0 + (i + 1) * quant_delta_value)))
            result.append(tv)
            prev_point = tv

        return result


class Tsd(object):

    def __init__(self, t: float, s: int, d: int = None):
        self.__initial_t = t
        # Sync threads: 1) send frame data 2) send statistics info
        self.__data_condition = Condition()
        self.__send_stat = IntegerStat()
        self.__delivery_stat = IntegerStat()
        self.__send_stat.update_with_time(t, s)
        if d is not None:
            self.__delivery_stat.update_with_time(t, d)

    def inc_s(self, timeout=3):
        if self.__data_condition.acquire(True, timeout=timeout):
            try:
                _, c = self.__send_stat[-1]
                self.__send_stat.update(c + 1)
                self.__data_condition.notify_all()
            finally:
                self.__data_condition.release()

    def set_d(self, d: int, timeout=3):
        self.__delivery_stat.update(d)

    def get_s(self, timeout=3):
        if self.__data_condition.acquire(True, timeout=timeout):
            try:
                self.__data_condition.wait(timeout)
                _, c = self.__send_stat[-1]
                return c
            finally:
                self.__data_condition.release()
        else:
            return None

    def get_t(self):
        return self.__initial_t

    def get_last_delivery_t(self):
        return self.__delivery_stat[-1][0]

    def get_last_send_t(self):
        return self.__send_stat[-1][0]

    def get_last_send(self):
        return self.__send_stat[-1][1]

    @staticmethod
    def _diffs(fps, send_statistics, delivery_statistics):
        result = []
        # print(f'send_statistics is {send_statistics}')
        # print(f'delivery_statistics is {delivery_statistics}')
        start_pos = 0
        for td in delivery_statistics:
            t, d = td
            # seek closest value in send stat
            closest_sent_time = None
            closest_sent_count = None
            for pos in range(start_pos, len(send_statistics) - 1):
                # print(f'Pos is {pos}, len is {len(send_statistics)}')
                st, s = send_statistics[pos]
                if st >= t or s > d:
                    break
                closest_sent_time = st
                closest_sent_count = s
                start_pos = pos
            if closest_sent_time is not None:
                result.append((closest_sent_time, closest_sent_count, t, d))
        return result

    def estimated_fps(self, fps):
        """
        Model:
            sent there      -1-2-3-4-5-----------------
            delivered here  -1---2---3---------4-----5-

        Algorithm:
            quantization of delivery-stat and send-stat series
            approximate (linear) delivery-stat and send-stat

            for every delivery-stat point find closest send-stat point
            collect differences

            calculate average difference and momentum

            calculate decrease/increase step for momentum and average difference
        """
        # We need to linearise delivery_stat

        # Get difference between delivery and send stat, for time-quant 1/fps
        diffs = self._diffs(fps, list(self.__send_stat), list(self.__delivery_stat))

        # Calculate fps_decrease_lambda valid values between [0, 0.967] for 33 fps
        if len(diffs) == 0 and (len(self.__send_stat) < 2 or (self.__send_stat[-1][1] - self.__send_stat[0][1]) == 0):
            fps_decrease_lambda = 0
            # print(f'Decrease fps lambda is {fps_decrease_lambda}')
        elif len(diffs) == 0:
            send_time = datetime.timestamp(datetime.utcnow()) - self.__send_stat[0][0]
            send_count = self.__send_stat[-1][1] - self.__send_stat[0][1]
            # print(f'Diffs has zero spot send_time is {send_time}, send_count is {send_count}, len of send_stat is {len(self.__send_stat)}')

            fps_decrease_lambda = min((send_time - send_count / fps) / send_time, 0.977) if send_time > send_count / fps else 0  # fast send for 1 sec and the slow down fps
            #if send_time > 10:
            #    raise SensorAgentError('Stalled connection, detect after 10 second no response')
            # print(f'Decrease fps lambda is {fps_decrease_lambda}')
        else:  # Calculate second differences
            total_delay = diffs[0][2] - diffs[0][0]
            total_momentum = 0
            for i in range(1, len(diffs)):
                delay_minus_one = diffs[i - 1][2] - diffs[i - 1][0]
                delay = diffs[i][2] - diffs[i][0]

                total_momentum += delay - delay_minus_one

                total_delay += delay

            average_momentum = total_momentum / len(diffs)
            average_delay = total_delay / len(diffs)
            fps_decrease_lambda = min(average_delay / (1 / fps), 0.977)
            # print(f'[{threading.current_thread().name}] Differences are: {[(round(t0v0tv[2] - t0v0tv[0], 3), t0v0tv[3] - t0v0tv[1]) for t0v0tv in diffs]}, average delay is {total_delay/len(diffs)}, average momentum is {total_momentum/len(diffs)}, fps_decrease_step is {fps_decrease_step}')
            # print(f'[{threading.current_thread().name}] Differences are: {diffs}, average delay is {total_delay/len(diffs)}, average momentum is {total_momentum/len(diffs)}, fps_decrease_step is {fps_decrease_step}')
            # print(f'[{threading.current_thread().name}] average delay is {average_delay}, average momentum is {average_momentum}, diffs count {len(diffs)}, delivery stat len is {len(self.__delivery_stat)}, send stat len is {len(self.__send_stat)}')
            # raise SensorAgentError('Debug break')
            # print(f'Decrease fps lambda is {fps_decrease_lambda} average_delay {average_delay}, average_momentum {average_momentum}, spot_width {len(diffs) / 10}, current_delay {self.__send_stat[-1][0] - diffs[-1][0]}, frames-in-fly {self.__send_stat[-1][1] - self.__delivery_stat[-1][1]}')

        return fps * (1 - 0.861) #  fps_decrease_lambda)


class LiveStreamStates(object):

    def __init__(self, cap: int):
        self._cap = cap
        self.__storage = dict()  # Dictionayr[List[TCD]]

    def new_from_string(self, url_string: str):  # find t, c, s paramaters
        c, _, s = self.__parse_url(url_string)
        t = datetime.timestamp(datetime.utcnow())
        self.__new(s, Tsd(t, c, 0))
        return s, t

    def __new(self, s: str, tsd: Tsd):
        while s not in self.__storage and len(self.__storage) + 1 > self._cap and self._cap > 0:
            # remove oldest one by one
            self.__storage.pop(min(self.__storage, key=lambda x: self[x].get_t()), None)
        states = self.__storage[s] if s in self.__storage else []
        states.append(tsd)
        self.__storage[s] = states

    @staticmethod
    def __len(the_str, pos):
        if pos > -1:
            amp_pos = the_str.find('&', pos)
            return amp_pos - pos if amp_pos > -1 else len(the_str) - pos
        return 0

    @staticmethod
    def __str(the_str, the_key, pos, str_len, def_val=''):
        return the_str[pos+len(the_key):pos+str_len] if (-1 < pos < len(the_str)) and (pos + str_len <= len(the_str)) else def_val

    def __parse_url(self, url_string: str):
        c_pos = url_string.find('c=')
        c_len = self.__len(url_string, c_pos)
        d_pos = url_string.find('d=')
        d_len = self.__len(url_string, d_pos)
        s_pos = url_string.find('s=')
        s_len = self.__len(url_string, s_pos)

        c = int(self.__str(url_string, 'c=', c_pos, c_len, 0))
        d = int(self.__str(url_string, 'd=', d_pos, d_len, 0))
        s = self.__str(url_string, 's=', s_pos, s_len, '')
        return c, d, s

    def set_from_string(self, url_string: str) -> bool:  # find t, c, s paramaters
        _, d, s = self.__parse_url(url_string)

        if s not in self.__storage:
            return False

        self[s].set_d(d)

    def get_send_count_for_session_by_url(self, url_string: str) -> bool:  # find t, c, s paramaters
        _, _, s = self.__parse_url(url_string)

        if s not in self.__storage:
            return 0

        return self[s].get_last_send()

    def inc_sent(self, s) -> bool:
        if s not in self.__storage:
            return False
        self[s].inc_s()

    def __len__(self):
        return len(self.__storage)

    def __getitem__(self, key) -> Tsd:
        return self.__storage[key][-1]

    def __contains__(self, key):
        return key in self.__storage

    def __index(self, key, predicate):
        result = 0
        for e in self.__storage[key]:
            if predicate(e):
                return result
            result += 1
        return -1

    def is_outdate(self, key, stamp):
        return key in self.__storage and len(self.__storage[key]) > 1 and self.__index(key, lambda x: x.get_t() == stamp) < len(self.__storage[key]) - 1

    def remove(self, key, stamp):
        i = self.__index(key, lambda x: x.get_t() == stamp)
        del self.__storage[key][i]

    def size(self):
        return sum([len(a) for a in self.__storage.values()])


class LiveStreamControls(object):

    def __init__(self, sessions: LiveStreamStates):
        self.__storage = dict()  # Dictionayr[List[TCD]]
        self.__sessions = sessions

    def new_from_string(self, url_string: str):  # find t, c, s paramaters
        s = self.__parse_url(url_string)
        # if s in self.__storage:
        #     raise SensorAgentError(f'Double control for session: {s}')
        t = datetime.timestamp(datetime.utcnow())
        self.__storage[s] = t
        return s

    @staticmethod
    def __len(the_str, pos):
        if pos > -1:
            amp_pos = the_str.find('&', pos)
            return amp_pos - pos if amp_pos > -1 else len(the_str) - pos
        return 0

    @staticmethod
    def __str(the_str, the_key, pos, str_len, def_val=''):
        return the_str[pos+len(the_key):pos+str_len] if (-1 < pos < len(the_str)) and (pos + str_len <= len(the_str)) else def_val

    def __parse_url(self, url_string: str):
        s_pos = url_string.find('s=')
        s_len = self.__len(url_string, s_pos)

        s = self.__str(url_string, 's=', s_pos, s_len, '')
        return s

    def __len__(self):
        return len(self.__storage)

    def __getitem__(self, key):
        if key in self.__sessions:
            return self.__sessions[key]
        return None

    def __contains__(self, key):
        return key in self.__storage

    def invalidate(self, key):
        if key not in self.__storage:
            return
        if key not in self.__sessions:
            del self.__storage[key]


class QvelteBundle(object):

    def __init__(self, bundle_name: str, folders: list = []):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bundle_file_path = self.__find(folders, bundle_name + '.qvelte')
        self.pathmap = {}
        self.file_object = None
        self.tar_file = None
        if self.bundle_file_path:
            file = open(self.bundle_file_path, 'rb')
            self.file_object = mmap.mmap(
                file.fileno(), 0, access=mmap.ACCESS_READ)
            self.tar_file = tarfile.open(mode='r', fileobj=self.file_object)
            for file_path in self.tar_file.getnames():
                file_path = file_path[1:]
                if file_path:
                    self.pathmap[file_path] = self.process
        self.content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'text/javascript',
            '.apng': 'image/apng',
            '.png': 'image/png',
            '.svg': 'image/svg',
            '.ico': 'image/ico',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.json': APPLICATION_JSON,
            '.tiff': 'image/tiff',
            '.webp': 'image/webp',
        }
        self.logger.info('QvelteBundle finish initialization')

    def __find(self, folders: list, file_name: str):
        for folder in folders:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder, followlinks=True):
                    for _name in files:
                        if _name == file_name:
                            return os.path.abspath(os.path.join(root, file_name))
        return None

    def process(self, handler: server.BaseHTTPRequestHandler):
        file_path = '.' + handler.path
        _, file_extension = os.path.splitext(handler.path)
        # Auto-append index.html for folders
        if not file_extension:
            file_path += '/index.html'
            file_extension = '.html'
        with self.tar_file.extractfile(file_path) as entry:
            content = entry.read()
            handler.send_response(200)
            handler.send_header(
                'Content-Type', self.content_types[file_extension])
            handler.send_header('Content-Length', str(len(content)))
            handler.end_headers()
            handler.wfile.write(content)

    def has_path(self, path: str):
        return path in self.pathmap

    def release(self):
        if self.tar_file:
            self.tar_file.close()
        if self.file_object:
            self.file_object.close()


class PresenterHandler(server.BaseHTTPRequestHandler):

    fsarc_bundle = None
    logger = logging.getLogger(str('PresenterHandler'))
    sessions = LiveStreamStates(12)  # limited storage used for control bandwidth
    controls = LiveStreamControls(sessions)   # limited storage used for control bandwidth
    sensor_state_controller = None

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif PresenterHandler.fsarc_bundle.has_path(self.path):
            PresenterHandler.fsarc_bundle.process(self)
        elif self.path.startswith('/api-1.0/stream.mjpg'):  #t=...&s=...
            if 'update' in self.path:
                PresenterHandler.sessions.set_from_string(self.path)
                PresenterHandler.__success_response(self)
                return
            if 'get-send-stat' in self.path:
                send_count = PresenterHandler.sessions.get_send_count_for_session_by_url(self.path)
                PresenterHandler.__success_response(self, {'s': send_count})
                return
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control',
                             'private, no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                if 'control' in self.path:
                    s = PresenterHandler.controls.new_from_string(self.path)
                    PresenterHandler.__streaming_control(self, s)
                    return
                s, t = PresenterHandler.sessions.new_from_string(self.path)
                PresenterHandler.__streaming_mjpeg(self, s, t)
            except Exception as e:
                logging.warning(
                    'Removed mjpeg streaming client %s: %s',
                    self.client_address, str(e), exc_info=True)
        elif self.path.startswith('/api-1.0/stream.h264'):
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control',
                             'private, no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'video/mp4')
            self.end_headers()
            try:
                PresenterHandler.__streaming_h264(self)
            except Exception as e:
                logging.warning(
                    'Removed h264 streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path.startswith('/api-1.0/status'):  #t=...&s=...
            PresenterHandler.sessions.set_from_string(self.path)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-support-mode-false':
            PresenterHandler.sensor_state_controller.set_support_mode(False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-support-mode-true':
            PresenterHandler.sensor_state_controller.set_support_mode(datetime.utcnow())
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-disable-camera':
            PresenterHandler.sensor_state_controller.set_disable_camera()
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-enable-camera':
            PresenterHandler.sensor_state_controller.set_enable_camera()
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-all-leds-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active(
                [0, 1, 2, 3, 4, 5, 6, 7], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-all-leds-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active(
                [0, 1, 2, 3, 4, 5, 6, 7], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led0-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([0], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led0-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([0], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led1-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([1], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led1-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([1], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led2-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([2], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led2-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([2], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led3-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([3], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led3-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([3], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led4-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([4], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led4-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([4], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led5-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([5], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led5-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([5], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led6-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([6], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led6-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([6], False)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led7-active-mode-true':
            PresenterHandler.sensor_state_controller.set_led_status_active([7], True)
            PresenterHandler.__success_response(self)
        elif self.path == '/api-1.0/set-led7-active-mode-false':
            PresenterHandler.sensor_state_controller.set_led_status_active([7], False)
            PresenterHandler.__success_response(self)
        elif self.path.startswith('/browser/error'):
            PresenterHandler.sensor_state_controller.browser_error(self.path)
            PresenterHandler.__success_response(self)
        elif self.path.startswith('/browser/warn'):
            PresenterHandler.sensor_state_controller.browser_warn(self.path)
            PresenterHandler.__success_response(self)
        elif self.path.startswith('/browser/log'):
            PresenterHandler.sensor_state_controller.browser_log(self.path)
            PresenterHandler.__success_response(self)
        else:
            self.send_error(404)
            self.end_headers()

    def __streaming_control(self, session):
        # Write request immediately if not support_mode
        if not PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode()):
            self.send_error(404)
            self.end_headers()
        while PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode()) and not PresenterHandler.sensor_state_controller.released and session in PresenterHandler.controls:
            state = PresenterHandler.controls[session]
            if state:
                c = state.get_s()  # default timeout 3 sec
                if c:
                    PresenterHandler.__write_buf(self, c.to_bytes(4, byteorder='big'), datetime.utcnow())
                    # print(f'[{threading.current_thread().name}] Write buf for session: {session}')
            PresenterHandler.controls.invalidate(session)

    def __streaming_mjpeg(self, session, stamp):
        # Write request immediately if not support_mode
        if not PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode()):
            frame = PresenterHandler.sensor_state_controller.mjpeg_streaming_output.frame
            PresenterHandler.__write_frame(self, frame, time.time())
        fps_controller = FpsController(PresenterHandler.sensor_state_controller.mjpeg_streaming_output.fps)
        while PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode()) and not PresenterHandler.sensor_state_controller.released and session in PresenterHandler.sessions:
            # Control output FPS
            estimated_fps = PresenterHandler.sessions[session].estimated_fps(PresenterHandler.sensor_state_controller.mjpeg_streaming_output.fps)
            # print(f'Estimated fps is {estimated_fps}')
            if estimated_fps != PresenterHandler.sensor_state_controller.mjpeg_streaming_output.fps:
                fps_controller.set_fps(estimated_fps)

            with PresenterHandler.sensor_state_controller.mjpeg_streaming_output.condition:
                PresenterHandler.sensor_state_controller.mjpeg_streaming_output.condition.wait(3)
                # Place holder to drop function
                if fps_controller.is_drop():
                    continue
                frame = PresenterHandler.sensor_state_controller.mjpeg_streaming_output.frame
                frame_time = PresenterHandler.sensor_state_controller.mjpeg_streaming_output.time
            if PresenterHandler.sessions.is_outdate(session, stamp):
                # print(f'Close infinite stream {session}')
                PresenterHandler.sessions.remove(session, stamp)
                self.send_error(404)
                self.end_headers()
                raise SensorAgentError(f'Duplicated stream detection, so remove oldest {session} stamp is {stamp}')
            PresenterHandler.__write_frame(self, frame, frame_time)
            PresenterHandler.sessions.inc_sent(session)
            # print(f'[{threading.current_thread().name}] Write frame for session: {session}')

    def __streaming_h264(self):
        # Write request immediately if not support_mode
        if not PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode()):
            data = PresenterHandler.sensor_state_controller.h264_streaming_output.data
            PresenterHandler.__write_chunk(self, data)
            return

        PresenterHandler.logger.info(f'REQUEST HEADERS {self.headers}')

        if not self.headers['range']:
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', 0xFFFFFFFF)
            self.end_headers()
            self.send_response(200)
            return

        debug_info = open(f'/tmp/debug-{datetime.now():%Y-%m-%d-%H-%M-%S}.mp4', 'wb+')
        remuxer = Mp4Remuxer(PresenterHandler.sensor_state_controller.h264_streaming_output, self.__write_chunk, debug_info.write)

        try:
            remuxer.remux(self.__break_remux_expression)
        finally:
            remuxer.close()
            debug_info.flush()
            debug_info.close()

    @staticmethod
    def __break_remux_expression():
        return PresenterHandler.sensor_state_controller.released and PresenterHandler.sensor_state_controller.is_support_mode(PresenterHandler.sensor_state_controller.sensor_agent_configuration.get_support_mode())

    def __write_chunk(self, chunk):
        # MP4 is broken into two pieces: moov and mdat
        self.send_response(206)
        self.send_header('HTTP/1.1 206 Partial Context', '')
        self.send_header('Content-Type', 'video/mp4')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', 0xFFFFFFFF)
        self.end_headers()
        self.wfile.write(chunk)

    def __write_frame(self, frame, frame_time):
        self.wfile.write(b'--FRAME\r\n')
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('X-Timestamp', str(frame_time))
        self.send_header('Content-Length', str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)
        self.wfile.write(b'\r\n')

    def __write_buf(self, buf, buf_time):
        self.wfile.write(b'--BUF\r\n')
        self.send_header('Content-Type', 'application/x-binary')
        self.send_header('X-Timestamp', str(buf_time))
        self.send_header('Content-Length', str(len(buf)))
        self.end_headers()
        self.wfile.write(buf)
        self.wfile.write(b'\r\n')

    def __success_response(self, data: object = None):
        if data is not None:
            content = ('{"success": true, "data": ' + json.dumps(data) + '}').encode('utf-8')
        else:
            content = json.dumps(
                PresenterHandler.sensor_state_controller.get_status()).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', APPLICATION_JSON)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class SensorStatePresenter(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, sensor_agent_configuration: SensorAgentConfiguration,
                 camera_adapter: CameraAdapter, data_manager: DataManager,
                 statistics_manager: StatisticsManager, leds_manager: LedsManager) -> None:
        super().__init__(('', sensor_agent_configuration.get_http_port()), SwtpRequestHandler)
        self.logger = logging.getLogger(str(self.__class__))
        self.sensor_agent_configuration = sensor_agent_configuration
        self.sensor_state_controller = SensorStateController(sensor_agent_configuration, data_manager, camera_adapter, leds_manager)
        SwtpRequestHandler.paths_router.register('/', PresenterHandler.do_GET)
        PresenterHandler.sensor_state_controller = self.sensor_state_controller
        self.statistics_manager = statistics_manager

    def start(self):
        PresenterHandler.fsarc_bundle = QvelteBundle(
            'fsarc', [self.sensor_agent_configuration.get_application_folder()])  # [.] for debug
        try:
            threading.Thread(target=self.sensor_state_controller.start).start()  # Ignition
            self.logger.info(f'Start web-server on port {self.sensor_agent_configuration.get_http_port()}')
            self.serve_forever(1)
        finally:
            self.sensor_state_controller.release()

    def stop(self):
        self.logger.debug('Stop sensor state presenter')
        if self.sensor_state_controller:
            self.sensor_state_controller.release()
        if PresenterHandler.fsarc_bundle:
            PresenterHandler.fsarc_bundle.release()
        self.shutdown()
