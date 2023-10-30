﻿from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ctypes
import numpy
import six
import warnings

from artdaq._lib import lib_importer, ctypes_byte_str, c_bool32

from artdaq._task_modules.channels.channel import Channel
from artdaq._task_modules.export_signals import ExportSignals
from artdaq._task_modules.in_stream import InStream
from artdaq._task_modules.read_functions import (
    _read_analog_f_64, _read_digital_lines, _read_digital_u_32, _read_ctr_freq,
    _read_ctr_time, _read_ctr_ticks, _read_counter_u_32,_read_counter_f_64)
from artdaq._task_modules.timing import Timing
from artdaq._task_modules.triggers import Triggers
from artdaq._task_modules.out_stream import OutStream
from artdaq._task_modules.channels.cio_channel import CIOChannel
from artdaq._task_modules.ai_channel_collection import (
    AIChannelCollection)
from artdaq._task_modules.ao_channel_collection import (
    AOChannelCollection)
from artdaq._task_modules.cio_channel_collection import (
    CIOChannelCollection)
from artdaq._task_modules.di_channel_collection import (
    DIChannelCollection)
from artdaq._task_modules.do_channel_collection import (
    DOChannelCollection)
from artdaq._task_modules.write_functions import (
    _write_analog_f_64, _write_digital_lines, _write_digital_u_32,
    _write_ctr_freq, _write_ctr_time, _write_ctr_ticks)
from artdaq.constants import (
    AcquisitionType, ChannelType, UsageTypeCI, EveryNSamplesEventType,
    READ_ALL_AVAILABLE, UsageTypeCO, LineGrouping)
from artdaq.error_codes import Errors
from artdaq.errors import (
    check_for_error, is_string_buffer_too_small, DaqError, DaqResourceWarning)
from artdaq.types import CtrFreq, CtrTick, CtrTime
from artdaq.utils import unflatten_channel_string, flatten_channel_string

__all__ = ['Task']


class UnsetNumSamplesSentinel(object):
    pass


class UnsetAutoStartSentinel(object):
    pass


NUM_SAMPLES_UNSET = UnsetNumSamplesSentinel()
AUTO_START_UNSET = UnsetAutoStartSentinel()

del UnsetNumSamplesSentinel
del UnsetAutoStartSentinel


class Task(object):
    """
    Represents a DAQ Task.
    """

    def __init__(self, new_task_name=''):
        """
        Creates a DAQ task.

        Args:
            new_task_name (Optional[str]): Specifies the name to assign to
                the task.

                If you use this method in a loop and specify a name for the
                task, you must use the DAQ Clear Task method within the loop
                after you are finished with the task. Otherwise, ArtDAQ
                attempts to create multiple tasks with the same name, which
                results in an error.
        """
        self._handle = lib_importer.task_handle(0)

        cfunc = lib_importer.windll.ArtDAQ_CreateTask
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        ctypes_byte_str,
                        ctypes.POINTER(lib_importer.task_handle)]

        error_code = cfunc(
            new_task_name, ctypes.byref(self._handle))
        check_for_error(error_code)

        self._initialize(self._handle)

    def __del__(self):
        if self._handle is not None:
            warnings.warn(
                'The task was not explicitly closed before it was '
                'destructed. Resources on the task device may still be '
                'reserved.')

    def __enter__(self):
        return self

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._handle == other._handle
        return False

    def __exit__(self, type, value, traceback):
        if (self._handle != None):
            self.close()



    def __hash__(self):
        return hash(self._handle)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Task(name={0})'.format(self.name)

    def __type__(self):
        return self.task_type

    @property
    def name(self):
        """
        str: Indicates the name of the task.
        """
        cfunc = lib_importer.windll.ArtDAQ_GetTaskAttribute
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        lib_importer.task_handle, ctypes.c_uint, ctypes.c_char_p,
                        ctypes.c_uint]

        temp_size = 256
        while True:
            val = ctypes.create_string_buffer(temp_size)
            size_or_code = cfunc(
                self._handle, 0x1276, val, temp_size)

            if is_string_buffer_too_small(size_or_code):
                # Buffer size must have changed between calls; check again.
                temp_size = 0
            elif size_or_code > 0 and temp_size == 0:
                # Buffer size obtained, use to retrieve data.
                temp_size = size_or_code
            else:
                break

        check_for_error(size_or_code)

        return val.value.decode('ascii')

    @property
    def channels(self):
        """
        :class:`artdaq._task_modules.channels.channel.Channel`: Specifies
            a channel object that represents the entire list of virtual 
            channels in this task.
        """
        return Channel._factory(
            self._handle, flatten_channel_string(self.channel_names))

    @property
    def channel_names(self):
        """
        List[str]: Indicates the names of all virtual channels in the task.
        """
        cfunc = lib_importer.windll.ArtDAQ_GetTaskAttribute
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        lib_importer.task_handle, ctypes.c_int, ctypes.c_char_p,
                        ctypes.c_int]

        temp_size = 256
        while True:
            val = ctypes.create_string_buffer(temp_size)

            size_or_code = cfunc(
                self._handle, 0x1273, val, temp_size)

            if is_string_buffer_too_small(size_or_code):
                # Buffer size must have changed between calls; check again.
                temp_size = 0
            elif size_or_code > 0 and temp_size == 0:
                # Buffer size obtained, use to retrieve data.
                temp_size = size_or_code
            else:
                break

        check_for_error(size_or_code)

        return unflatten_channel_string(val.value.decode('ascii'))

    @property
    def number_of_channels(self):
        """
        int: Indicates the number of virtual channels in the task.
        """
        cfunc = lib_importer.windll.ArtDAQ_GetTaskAttribute
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        lib_importer.task_handle, ctypes.c_int, ctypes.c_char_p,
                        ctypes.c_int]

        temp_size = 256
        while True:
            val = ctypes.create_string_buffer(temp_size)

            size_or_code = cfunc(
                self._handle, 0x1273, val, temp_size)

            if is_string_buffer_too_small(size_or_code):
                # Buffer size must have changed between calls; check again.
                temp_size = 0
            elif size_or_code > 0 and temp_size == 0:
                # Buffer size obtained, use to retrieve data.
                temp_size = size_or_code
            else:
                break

        check_for_error(size_or_code)

        return unflatten_channel_string(val.value.decode('ascii'))

    @property
    def task_type(self):
        return self.__type__

    @property
    def ai_channels(self):
        """
        :class:`artdaq._task_modules.ai_channel_collection.AIChannelCollection`:
            Gets the collection of analog input channels for this task.
        """
        self.__type__= ChannelType.ANALOG_INPUT
        return self._ai_channels

    @property
    def ao_channels(self):
        """
        :class:`artdaq._task_modules.ao_channel_collection.AOChannelCollection`:
            Gets the collection of analog output channels for this task.
        """
        self.__type__ = ChannelType.ANALOG_OUTPUT
        return self._ao_channels

    @property
    def cio_channels(self):
        """
        :class:`artdaq._task_modules.ci_channel_collection.CIOChannelCollection`:
            Gets the collection of counter input channels for this task.
        """
        self.__type__ = ChannelType.COUNTER
        return self._cio_channels

    @property
    def di_channels(self):
        """
        :class:`artdaq._task_modules.di_channel_collection.DIChannelCollection`:
            Gets the collection of digital input channels for this task.
        """
        self.__type__ = ChannelType.DIGITAL_IN
        return self._di_channels

    @property
    def do_channels(self):
        """
        :class:`artdaq._task_modules.do_channel_collection.DOChannelCollection`:
            Gets the collection of digital output channels for this task.
        """
        self.__type__ = ChannelType.DIGITAL_OUTPUT
        return self._do_channels

    @property
    def export_signals(self):
        """
        :class:`artdaq._task_modules.export_signals.ExportSignals`: Gets the
            exported signal configurations for the task.
        """
        return self._export_signals

    @property
    def in_stream(self):
        """
        :class:`artdaq._task_modules.in_stream.InStream`: Gets the read
            configurations for the task.
        """
        return self._in_stream

    @property
    def out_stream(self):
        """
        :class:`artdaq._task_modules.out_stream.OutStream`: Gets the
            write configurations for the task.
        """
        return self._out_stream

    @property
    def timing(self):
        """
        :class:`artdaq._task_modules.timing.Timing`: Gets the timing
            configurations for the task.
        """
        return self._timing

    @property
    def triggers(self):
        """
        :class:`artdaq._task_modules.triggers.Triggers`: Gets the trigger
            configurations for the task.
        """
        return self._triggers

    def _initialize(self, task_handle):
        """
        Instantiates and populates various attributes used by this task.

        Args:
            task_handle (TaskHandle): Specifies the handle for this task.
        """
        # Saved name is used in self.close() to throw graceful error on
        # double closes.
        self._saved_name = self.name

        self._ai_channels = AIChannelCollection(task_handle)
        self._ao_channels = AOChannelCollection(task_handle)
        self._cio_channels = CIOChannelCollection(task_handle)
        self._di_channels = DIChannelCollection(task_handle)
        self._do_channels = DOChannelCollection(task_handle)
        self._export_signals = ExportSignals(task_handle)
        self._in_stream = InStream(self)
        self._timing = Timing(task_handle)
        self._triggers = Triggers(task_handle)
        self._out_stream = OutStream(self)

        # These lists keep C callback objects in memory as ctypes doesn't.
        # Program will crash if callback is made after object is garbage
        # collected.
        self._done_event_callbacks = []
        self._every_n_transferred_event_callbacks = []
        self._every_n_acquired_event_callbacks = []
        self._signal_event_callbacks = []

    def _calculate_num_samps_per_chan(self, num_samps_per_chan):
        """
        Calculates the actual number of samples per channel to read.

        This method is necessary because the number of samples per channel
        can be set to NUM_SAMPLES_UNSET or -1, where each value entails a
        different method of calculating the actual number of samples per
        channel to read.

        Args:
            num_samps_per_chan (int): Specifies the number of samples per
                channel.
        """
        if num_samps_per_chan is NUM_SAMPLES_UNSET:
            return 1
        elif num_samps_per_chan == READ_ALL_AVAILABLE:
            acq_type = self.timing.samp_quant_samp_mode

            if (acq_type == AcquisitionType.FINITE and
                    not self.in_stream.read_all_avail_samp):
                return self.timing.samp_quant_samp_per_chan
            else:
                return self.in_stream.avail_samp_per_chan
        else:
            return num_samps_per_chan

    def close(self):
        """
        Clears the task.

        Before clearing, this method aborts the task, if necessary,
        and releases any resources the task reserved. You cannot use a task
        after you clear it unless you recreate the task.

        If you create a DAQ Task object within a loop, use this method
        within the loop after you are finished with the task to avoid
        allocating unnecessary memory.
        """
        # if self._handle is None:
        #     warnings.warn(
        #         'Attempted to close ArtDAQ task of name "{0}" but task was '
        #         'already closed.'.format(self._saved_name), DaqResourceWarning)
        #     return

        cfunc = lib_importer.windll.ArtDAQ_ClearTask
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        lib_importer.task_handle]

        error_code = cfunc(self._handle)
        if(error_code == 0):
            self._handle = None
        check_for_error(error_code)
        return 0

    def is_task_done(self):
        """
        Queries the status of the task and indicates if it completed
        execution. Use this function to ensure that the specified
        operation is complete before you stop the task.

        Returns:
            bool:

            Indicates if the measurement or generation completed.
        """
        is_task_done = c_bool32()

        cfunc = lib_importer.windll.ArtDAQ_IsTaskDone
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [
                        lib_importer.task_handle, ctypes.POINTER(c_bool32)]

        error_code = cfunc(
            self._handle, ctypes.byref(is_task_done))
        check_for_error(error_code)

        return is_task_done.value

    def read(self, number_of_samples_per_channel=NUM_SAMPLES_UNSET,
             timeout=10.0):
        """
        Reads samples from the task or virtual channels you specify.

        This read method is dynamic, and is capable of inferring an appropriate
        return type based on these factors:
        - The channel type of the task.
        - The number of channels to read.
        - The number of samples per channel.

        The data type of the samples returned is independently determined by
        the channel type of the task.

        For digital input measurements, the data type of the samples returned
        is determined by the line grouping format of the digital lines.
        If the line grouping format is set to "one channel for all lines", the
        data type of the samples returned is int. If the line grouping
        format is set to "one channel per line", the data type of the samples
        returned is boolean.

        If you do not set the number of samples per channel, this method
        assumes one sample was requested. This method then returns either a
        scalar (1 channel to read) or a list (N channels to read).

        If you set the number of samples per channel to ANY value (even 1),
        this method assumes multiple samples were requested. This method then
        returns either a list (1 channel to read) or a list of lists (N
        channels to read).

        Args:
            number_of_samples_per_channel (Optional[int]): Specifies the
                number of samples to read. If this input is not set,
                assumes samples to read is 1. Conversely, if this input
                is set, assumes there are multiple samples to read.

                If you set this input to artdaq.constants.
                READ_ALL_AVAILABLE, ArtDAQ determines how many samples
                to read based on if the task acquires samples
                continuously or acquires a finite number of samples.

                If the task acquires samples continuously and you set
                this input to artdaq.constants.READ_ALL_AVAILABLE, this
                method reads all the samples currently available in the
                buffer.

                If the task acquires a finite number of samples and you
                set this input to artdaq.constants.READ_ALL_AVAILABLE,
                the method waits for the task to acquire all requested
                samples, then reads those samples. If you set the
                "read_all_avail_samp" property to True, the method reads
                the samples currently available in the buffer and does
                not wait for the task to acquire all requested samples.
            timeout (Optional[float]): Specifies the amount of time in
                seconds to wait for samples to become available. If the
                time elapses, the method returns an error and any
                samples read before the timeout elapsed. The default
                timeout is 10 seconds. If you set timeout to
                artdaq.constants.WAIT_INFINITELY, the method waits
                indefinitely. If you set timeout to 0, the method tries
                once to read the requested samples and returns an error
                if it is unable to.
        Returns:
            dynamic:

            The samples requested in the form of a scalar, a list, or a
            list of lists. See method docstring for more info.

            ArtDAQ scales the data to the units of the measurement,
            including any custom scaling you apply to the channels. Use a
            DAQ Create Channel method to specify these units.

        Example:
            >>> task = Task()
            >>> task.ai_channels.add_voltage_channel('Dev1/ai0:3')
            >>> data = task.read()
            >>> type(data)
            <type 'list'>
            >>> type(data[0])
            <type 'float'>
        """
        channels_to_read = self.in_stream.channels_to_read
        number_of_channels = len(channels_to_read.channel_names)
        read_chan_type = self.task_type

        num_samples_not_set = (number_of_samples_per_channel is
                               NUM_SAMPLES_UNSET)

        number_of_samples_per_channel = self._calculate_num_samps_per_chan(
            number_of_samples_per_channel)

        # Determine the array shape and size to create
        if number_of_channels > 1:
            if not num_samples_not_set:
                array_shape = (number_of_channels,
                               number_of_samples_per_channel)
            else:
                array_shape = number_of_channels
        else:
            array_shape = number_of_samples_per_channel

        # Analog Input
        if read_chan_type == ChannelType.ANALOG_INPUT:
            data = numpy.zeros(array_shape, dtype=numpy.float64)
            samples_read = _read_analog_f_64(
                self._handle, data, number_of_samples_per_channel, timeout)

        # Digital Input or Digital Output
        elif read_chan_type == ChannelType.DIGITAL_IN:
            # if self.in_stream.di_num_booleans_per_chan == 1:
            #     data = numpy.zeros(array_shape, dtype=numpy.bool)
            #     samples_read = _read_digital_lines(
            #         self._handle, data, number_of_samples_per_channel, timeout
            #         ).samps_per_chan_read
            # else:
            #     data = numpy.zeros(array_shape, dtype=numpy.uint32)
            #     samples_read = _read_digital_u_32(
            #         self._handle, data, number_of_samples_per_channel, timeout)

            if Channel.line_grouping == LineGrouping.CHAN_PER_LINE:
                data = numpy.zeros(array_shape, dtype=numpy.bool)
                samples_read = _read_digital_lines(
                    self._handle, data, number_of_samples_per_channel, timeout
                ).samps_per_chan_read
            else:
                data = numpy.zeros(array_shape, dtype=numpy.uint32)
                samples_read = _read_digital_u_32(
                    self._handle, data, number_of_samples_per_channel, timeout)

        # Counter Input or Digital Output
        elif read_chan_type == ChannelType.COUNTER:
            # meas_type = channels_to_read.ci_meas_type

            meas_type = CIOChannel.ci_meas_type

            if meas_type == UsageTypeCI.PULSE_FREQ:
                frequencies = numpy.zeros(array_shape, dtype=numpy.float64)
                duty_cycles = numpy.zeros(array_shape, dtype=numpy.float64)

                samples_read = _read_ctr_freq(
                    self._handle, frequencies, duty_cycles,
                    number_of_samples_per_channel, timeout)

                data = []
                for f, d in zip(frequencies, duty_cycles):
                    data.append(CtrFreq(freq=f, duty_cycle=d))

            elif meas_type == UsageTypeCI.PULSE_TIME:
                high_times = numpy.zeros(array_shape, dtype=numpy.float64)
                low_times = numpy.zeros(array_shape, dtype=numpy.float64)

                samples_read = _read_ctr_time(
                    self._handle, high_times, low_times,
                    number_of_samples_per_channel, timeout)
                data = []
                for h, l in zip(high_times, low_times):
                    data.append(CtrTime(high_time=h, low_time=l))

            elif meas_type == UsageTypeCI.PULSE_TICKS:
                high_ticks = numpy.zeros(array_shape, dtype=numpy.uint32)
                low_ticks = numpy.zeros(array_shape, dtype=numpy.uint32)

                samples_read = _read_ctr_ticks(
                    self._handle, high_ticks, low_ticks,
                    number_of_samples_per_channel, timeout)
                data = []
                for h, l in zip(high_ticks, low_ticks):
                    data.append(CtrTick(high_tick=h, low_tick=l))

            elif meas_type == UsageTypeCI.COUNT_EDGES:
                data = numpy.zeros(array_shape, dtype=numpy.uint32)
                samples_read = _read_counter_u_32(
                    self._handle, data, number_of_samples_per_channel, timeout)

            else:
                data = numpy.zeros(array_shape, dtype=numpy.float64)
                samples_read = _read_counter_f_64(
                    self._handle, data, number_of_samples_per_channel, timeout)
        else:
            raise DaqError(
                'Read failed, because there are no channels in this task from '
                'which data can be read.',
                Errors.READ_NO_INPUT_CHANS_IN_TASK.value,
                task_name=self.name)

        if (read_chan_type == ChannelType.COUNTER and
                (meas_type == UsageTypeCI.PULSE_FREQ or
                 meas_type == UsageTypeCI.PULSE_TICKS or
                 meas_type == UsageTypeCI.PULSE_TIME)):

            if num_samples_not_set and array_shape == 1:
                return data[0]
            # Counter pulse measurements should not have N channel versions.
            if samples_read != number_of_samples_per_channel:
                return data[:samples_read]
            return data

        if num_samples_not_set and array_shape == 1:
            return data.tolist()[0]

        if samples_read != number_of_samples_per_channel:
            if number_of_channels > 1:
                return data[:, :samples_read].tolist()
            else:
                return data[:samples_read].tolist()

        return data.tolist()

    def register_done_event(self, callback_method):
        """
        Registers a callback function to receive an event when a task stops due
        to an error or when a finite acquisition task or finite generation task
        completes execution. A Done event does not occur when a task is stopped
        explicitly, such as by calling DAQ Stop Task.

        Args:
            callback_method (function): Specifies the function that you want
                DAQ to call when the event occurs. The function you pass in
                this parameter must have the following prototype:

                >>> def callback(task_handle, status, callback_data):
                >>>     return 0

                Upon entry to the callback, the task_handle parameter contains
                the handle to the task on which the event occurred. The status
                parameter contains the status of the task when the event
                occurred. If the status value is negative, it indicates an
                error. If the status value is zero, it indicates no error.
                If the status value is positive, it indicates a warning. The
                callbackData parameter contains the value you passed in the
                callbackData parameter of this function.

                Passing None for this parameter unregisters the event callback
                function.
        """
        DAQDoneEventCallbackPtr = ctypes.CFUNCTYPE(
            ctypes.c_int32, lib_importer.task_handle, ctypes.c_int32,
            ctypes.c_void_p)

        cfunc = lib_importer.windll.ArtDAQ_RegisterDoneEvent

        with cfunc.arglock:
            if callback_method is not None:
                callback_method_ptr = DAQDoneEventCallbackPtr(callback_method)
                self._done_event_callbacks.append(callback_method_ptr)
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_uint,
                    DAQDoneEventCallbackPtr, ctypes.c_void_p]
            else:
                del self._done_event_callbacks[:]
                callback_method_ptr = None
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_uint, ctypes.c_void_p,
                    ctypes.c_void_p]

            error_code = cfunc(
                self._handle, 0, callback_method_ptr, None)
        check_for_error(error_code)

    def register_every_n_samples_acquired_into_buffer_event(
            self, sample_interval, callback_method):
        """
        Registers a callback function to receive an event when the specified
        number of samples is written from the device to the buffer. This
        function only works with devices that support buffered tasks.

        When you stop a task explicitly any pending events are discarded. For
        example, if you call DAQ Stop Task then you do not receive any
        pending events.

        Args:
            sample_interval (int): Specifies the number of samples after
                which each event should occur.
            callback_method (function): Specifies the function that you want
                DAQ to call when the event occurs. The function you pass in
                this parameter must have the following prototype:

                >>> def callback(task_handle, every_n_samples_event_type,
                >>>         number_of_samples, callback_data):
                >>>     return 0

                Upon entry to the callback, the task_handle parameter contains
                the handle to the task on which the event occurred. The
                every_n_samples_event_type parameter contains the
                EveryNSamplesEventType.ACQUIRED_INTO_BUFFER value. The
                number_of_samples parameter contains the value you passed in
                the sample_interval parameter of this function. The
                callback_data parameter contains the value you passed in the
                callback_data parameter of this function.

                Passing None for this parameter unregisters the event callback
                function.
        """
        DAQEveryNSamplesEventCallbackPtr = ctypes.CFUNCTYPE(
            ctypes.c_int32, lib_importer.task_handle, ctypes.c_int32,
            ctypes.c_uint32, ctypes.c_void_p)

        cfunc = lib_importer.windll.ArtDAQ_RegisterEveryNSamplesEvent

        with cfunc.arglock:
            if callback_method is not None:
                callback_method_ptr = DAQEveryNSamplesEventCallbackPtr(
                    callback_method)
                self._every_n_acquired_event_callbacks.append(
                    callback_method_ptr)
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    ctypes.c_uint, DAQEveryNSamplesEventCallbackPtr,
                    ctypes.c_void_p]
            else:
                del self._every_n_acquired_event_callbacks[:]
                callback_method_ptr = None
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]

            error_code = cfunc(
                self._handle, EveryNSamplesEventType.ACQUIRED_INTO_BUFFER.value,
                sample_interval, 0, callback_method_ptr, None)
        check_for_error(error_code)

    def register_every_n_samples_transferred_from_buffer_event(
            self, sample_interval, callback_method):
        """
        Registers a callback function to receive an event when the specified
        number of samples is written from the buffer to the device. This
        function only works with devices that support buffered tasks.

        When you stop a task explicitly any pending events are discarded. For
        example, if you call DAQ Stop Task then you do not receive any
        pending events.

        Args:
            sample_interval (int): Specifies the number of samples after
                which each event should occur.
            callback_method (function): Specifies the function that you want
                DAQ to call when the event occurs. The function you pass in
                this parameter must have the following prototype:

                >>> def callback(task_handle, every_n_samples_event_type,
                >>>         number_of_samples, callback_data):
                >>>     return 0

                Upon entry to the callback, the task_handle parameter contains
                the handle to the task on which the event occurred. The
                every_n_samples_event_type parameter contains the
                EveryNSamplesEventType.TRANSFERRED_FROM_BUFFER value. The
                number_of_samples parameter contains the value you passed in
                the sample_interval parameter of this function. The
                callback_data parameter contains the value you passed in the
                callback_data parameter of this function.

                Passing None for this parameter unregisters the event callback
                function.
        """
        DAQEveryNSamplesEventCallbackPtr = ctypes.CFUNCTYPE(
            ctypes.c_int32, lib_importer.task_handle, ctypes.c_int32,
            ctypes.c_uint32, ctypes.c_void_p)

        cfunc = lib_importer.windll.ArtDAQ_RegisterEveryNSamplesEvent

        with cfunc.arglock:
            if callback_method is not None:
                callback_method_ptr = DAQEveryNSamplesEventCallbackPtr(
                    callback_method)
                self._every_n_transferred_event_callbacks.append(
                    callback_method_ptr)
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    ctypes.c_uint, DAQEveryNSamplesEventCallbackPtr,
                    ctypes.c_void_p]
            else:
                del self._every_n_transferred_event_callbacks[:]
                callback_method_ptr = None
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]

            error_code = cfunc(
                self._handle,
                EveryNSamplesEventType.TRANSFERRED_FROM_BUFFER.value,
                sample_interval, 0, callback_method_ptr, None)
        check_for_error(error_code)

    def register_signal_event(self, signal_type, callback_method):
        """
        Registers a callback function to receive an event when the specified
        hardware event occurs.

        When you stop a task explicitly any pending events are discarded. For
        example, if you call DAQ Stop Task then you do not receive any
        pending events.

        Args:
            signal_type (artdaq.constants.Signal): Specifies the type of
                signal for which you want to receive results.
            callback_method (function): Specifies the function that you want
                DAQ to call when the event occurs. The function you pass in
                this parameter must have the following prototype:

                >>> def callback(task_handle, signal_type, callback_data):
                >>>     return 0

                Upon entry to the callback, the task_handle parameter contains
                the handle to the task on which the event occurred. The
                signal_type parameter contains the integer value you passed in
                the signal_type parameter of this function. The callback_data
                parameter contains the value you passed in the callback_data
                parameter of this function.

                Passing None for this parameter unregisters the event callback
                function.
        """
        DAQSignalEventCallbackPtr = ctypes.CFUNCTYPE(
            ctypes.c_int32, lib_importer.task_handle, ctypes.c_int32,
            ctypes.c_void_p)

        cfunc = lib_importer.windll.ArtDAQ_RegisterSignalEvent

        with cfunc.arglock:
            if callback_method is not None:
                callback_method_ptr = DAQSignalEventCallbackPtr(
                    callback_method)
                self._signal_event_callbacks.append(callback_method_ptr)
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    DAQSignalEventCallbackPtr, ctypes.c_void_p]
            else:
                del self._signal_event_callbacks[:]
                callback_method_ptr = None
                cfunc.argtypes = [
                    lib_importer.task_handle, ctypes.c_int, ctypes.c_uint,
                    ctypes.c_void_p, ctypes.c_void_p]

            error_code = cfunc(
                self._handle, signal_type.value, 0, callback_method_ptr, None)
        check_for_error(error_code)

    def start(self):
        """
        Transitions the task to the running state to begin the measurement
        or generation. Using this method is required for some applications and
        is optional for others.

        If you do not use this method, a measurement task starts automatically
        when the DAQ Read method runs. The autostart input of the DAQ Write
        method determines if a generation task starts automatically when the
        DAQ Write method runs.

        If you do not use the DAQ Start Task method and the DAQ Stop Task
        method when you use the DAQ Read method or the DAQ Write method
        multiple times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces the
        performance of the application.
        """
        cfunc = lib_importer.windll.ArtDAQ_StartTask
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [lib_importer.task_handle]

        error_code = cfunc(self._handle)
        check_for_error(error_code)

    def stop(self):
        """
        Stops the task and returns it to the state the task was in before the
        DAQ Start Task method ran or the DAQ Write method ran with the
        autostart input set to TRUE.

        If you do not use the DAQ Start Task method and the DAQ Stop Task
        method when you use the DAQ Read method or the DAQ Write method
        multiple times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces the
        performance of the application.
        """
        if self._handle is None:
            warnings.warn(
                '11111 '
                'already closed.'.format(self._saved_name), DaqResourceWarning)
            return
        cfunc = lib_importer.windll.ArtDAQ_StopTask
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [lib_importer.task_handle]

        error_code = cfunc(self._handle)
        check_for_error(error_code)

    def wait_until_done(self, timeout=10.0):
        """
        Waits for the measurement or generation to complete.

        Use this method to ensure that the specified operation is complete
        before you stop the task.

        Args:
            timeout (Optional[float]): Specifies the maximum amount of time in
                seconds to wait for the measurement or generation to complete.
                This method returns an error if the time elapses. The
                default is 10. If you set timeout (sec) to
                artdaq.WAIT_INFINITELY, the method waits indefinitely. If you
                set timeout (sec) to 0, the method checks once and returns
                an error if the measurement or generation is not done.
        """
        cfunc = lib_importer.windll.ArtDAQ_WaitUntilTaskDone
        if cfunc.argtypes is None:
            with cfunc.arglock:
                if cfunc.argtypes is None:
                    cfunc.argtypes = [lib_importer.task_handle, ctypes.c_double]

        error_code = cfunc(self._handle, timeout)
        check_for_error(error_code)

    def _raise_invalid_num_lines_error(
            self, num_lines_expected, num_lines_in_data):
        raise DaqError(
            'Specified read or write operation failed, because the number '
            'of lines in the data for a channel does not match the number '
            'of lines in the channel.\n\n'
            'If you are using boolean data, make sure the array dimension '
            'for lines in the data matches the number of lines in the '
            'channel.\n\n'
            'Number of Lines Per Channel in Task: {0}\n'
            'Number of Lines Per Channel in Data: {1}'
            .format(num_lines_expected, num_lines_in_data),
            Errors.NUM_LINES_MISMATCH_IN_READ_OR_WRITE.value,
            task_name=self.name)

    def _raise_invalid_write_num_chans_error(
            self, number_of_channels, number_of_channels_in_data):

        raise DaqError(
            'Write cannot be performed, because the number of channels in the '
            'data does not match the number of channels in the task.\n\n'
            'When writing, supply data for all channels in the task. '
            'Alternatively, modify the task to contain the same number of '
            'channels as the data written.\n\n'
            'Number of Channels in Task: {0}\n'
            'Number of Channels in Data: {1}'
            .format(number_of_channels, number_of_channels_in_data),
            Errors.WRITE_NUM_CHANS_MISMATCH.value, task_name=self.name)

    def write(self, data, auto_start=AUTO_START_UNSET, timeout=10.0):
        """
        Writes samples to the task or virtual channels you specify.

        This write method is dynamic, and is capable of accepting the
        samples to write in the various forms for most operations:
        
        - Scalar: Single sample for 1 channel.
        - List/1D numpy.ndarray: Multiple samples for 1 channel or 1
          sample for multiple channels.
        - List of lists/2D numpy.ndarray: Multiple samples for multiple
          channels.

        The data type of the samples passed in must be appropriate for
        the channel type of the task.

        For counter output pulse operations, this write method only
        accepts samples in these forms:
        
        - Scalar CtrFreq, CtrTime, CtrTick (from artdaq.types):
          Single sample for 1 channel.
        - List of CtrFreq, CtrTime, CtrTick (from artdaq.types):
          Multiple samples for 1 channel or 1 sample for multiple 
          channels.

        If the task uses on-demand timing, this method returns only
        after the device generates all samples. On-demand is the default
        timing type if you do not use the timing property on the task to
        configure a sample timing type. If the task uses any timing type
        other than on-demand, this method returns immediately and does
        not wait for the device to generate all samples. Your
        application must determine if the task is done to ensure that
        the device generated all samples.

        Args:
            data (dynamic): Contains the samples to write to the task.

                The data you write must be in the units of the
                generation, including any custom scales. Use the DAQ
                Create Channel methods to specify these units.

            timeout (Optional[float]): Specifies the amount of time in
                seconds to wait for the method to write all samples.
                ArtDAQ performs a timeout check only if the method
                must wait before it writes data. This method returns an
                error if the time elapses. The default timeout is 10
                seconds. If you set timeout to
                artdaq.constants.WAIT_INFINITELY, the method waits
                indefinitely. If you set timeout to 0, the method tries
                once to write the submitted samples. If the method could
                not write all the submitted samples, it returns an error
                and the number of samples successfully written.
        Returns:
            int:

            Specifies the actual number of samples this method
            successfully wrote.
        """
        channels_to_write = self.channels
        number_of_channels = len(channels_to_write.channel_names)
        write_chan_type = self.task_type

        element = None
        if number_of_channels == 1:
            if isinstance(data, list):
                if isinstance(data[0], list):
                    self._raise_invalid_write_num_chans_error(
                        number_of_channels, len(data))

                number_of_samples_per_channel = len(data)
                element = data[0]

            elif isinstance(data, numpy.ndarray):
                if len(data.shape) == 2:
                    self._raise_invalid_write_num_chans_error(
                        number_of_channels, data.shape[0])

                number_of_samples_per_channel = len(data)
                element = data[0]

            else:
                number_of_samples_per_channel = 1
                element = data

        else:
            if isinstance(data, list):
                if len(data) != number_of_channels:
                    self._raise_invalid_write_num_chans_error(
                        number_of_channels, len(data))

                if isinstance(data[0], list):
                    number_of_samples_per_channel = len(data[0])
                    element = data[0][0]
                else:
                    number_of_samples_per_channel = 1
                    element = data[0]

            elif isinstance(data, numpy.ndarray):
                if data.shape[0] != number_of_channels:
                    self._raise_invalid_write_num_chans_error(
                        number_of_channels, data.shape[0])

                if len(data.shape) == 2:
                    number_of_samples_per_channel = data.shape[1]
                    element = data[0][0]
                else:
                    number_of_samples_per_channel = 1
                    element = data[0]

            else:
                self._raise_invalid_write_num_chans_error(
                    number_of_channels, 1)

        if auto_start is AUTO_START_UNSET:
            if number_of_samples_per_channel > 1:
                auto_start = False
            else:
                auto_start = True

        # Analog Input
        if write_chan_type == ChannelType.ANALOG_OUTPUT:
            data = numpy.asarray(data, dtype=numpy.float64)
            return _write_analog_f_64(
                self._handle, data, number_of_samples_per_channel, auto_start,
                timeout)

        elif write_chan_type == ChannelType.DIGITAL_OUTPUT:
            if Channel.line_grouping == LineGrouping.CHAN_PER_LINE:
                data = numpy.asarray(data, dtype=numpy.uint8)
                return _write_digital_lines(
                    self._handle, data, number_of_samples_per_channel, auto_start, timeout)
            else:
                if (not isinstance(element, six.integer_types) and
                        not isinstance(element, numpy.uint32)):
                    raise DaqError(
                        'Write failed, because this write method only accepts '
                        'unsigned 32-bit integer samples when there are '
                        'multiple digital lines per channel in a task.\n\n'
                        'Requested sample type: {0}'.format(type(element)),
                        Errors.UNKNOWN.value, task_name=self.name)
                data = numpy.asarray(data, dtype=numpy.uint32)
                return _write_digital_u_32(
                    self._handle, data, number_of_samples_per_channel, auto_start,
                    timeout)

        # Counter Input
        elif write_chan_type == ChannelType.COUNTER:
            output_type = channels_to_write.co_output_type

            if number_of_samples_per_channel == 1:
                data = [data]

            if output_type == UsageTypeCO.PULSE_FREQUENCY:
                frequencies = []
                duty_cycles = []
                for sample in data:
                    frequencies.append(sample.duty_cycle)
                    duty_cycles.append(sample.freq)

                frequencies = numpy.asarray(frequencies, dtype=numpy.float64)
                duty_cycles = numpy.asarray(duty_cycles, dtype=numpy.float64)

                return _write_ctr_freq(
                    self._handle, frequencies, duty_cycles,
                    number_of_samples_per_channel, auto_start, timeout)

            elif output_type == UsageTypeCO.PULSE_TIME:
                high_times = []
                low_times = []
                for sample in data:
                    high_times.append(sample.high_time)
                    low_times.append(sample.low_time)

                high_times = numpy.asarray(high_times, dtype=numpy.float64)
                low_times = numpy.asarray(low_times, dtype=numpy.float64)

                # return _write_ctr_time(
                #     self._handle, high_times, low_times,
                #     number_of_samples_per_channel, auto_start, timeout)
                return _write_ctr_time(
                    self._handle, high_times, low_times,
                    number_of_samples_per_channel, timeout)

            elif output_type == UsageTypeCO.PULSE_TICKS:
                high_ticks = []
                low_ticks = []
                for sample in data:
                    high_ticks.append(sample.high_tick)
                    low_ticks.append(sample.low_tick)

                high_ticks = numpy.asarray(high_ticks, dtype=numpy.uint32)
                low_ticks = numpy.asarray(low_ticks, dtype=numpy.uint32)

                return _write_ctr_ticks(
                    self._handle, high_ticks, low_ticks,
                    number_of_samples_per_channel, auto_start, timeout)
        else:
            raise DaqError(
                'Write failed, because there are no output channels in this '
                'task to which data can be written.',
                Errors.WRITE_NO_OUTPUT_CHANS_IN_TASK.value,
                task_name=self.name)
