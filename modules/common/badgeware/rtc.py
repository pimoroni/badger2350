import sys
import time
import machine
import pcf85063a
import datetime
import gc
import builtins
import board


class RTC:
    def __init__(self):
        self._rtc = pcf85063a.PCF85063A(machine.I2C())

        if time.localtime()[0] >= 2025:
            self.localtime_to_rtc()

        elif self._rtc.datetime()[0] >= 2025:
            self.rtc_to_localtime()

    def datetime(self, dt=None):
        dtf = self._rtc.datetime
        return dtf() if dt is None else dtf(dt)

    def localtime_to_rtc(self):
        self._rtc.datetime(time.localtime())

    def rtc_to_localtime(self):
        dt = self._rtc.datetime()
        machine.RTC().datetime((dt[0], dt[1], dt[2], dt[6], dt[3], dt[4], dt[5], 0))

    def time_from_ntp(self):
        import ntptime

        ntptime.settime()
        del sys.modules["ntptime"]
        gc.collect()
        self.localtime_to_rtc()

    def _get_running_app(self):
        try:
            return [str(v)[22:].split("'")[0] for _k, v in sys.modules.items() if "module '/system/apps/" in str(v)][0]
        except IndexError:
            return None

    def set_timer(self, ticks, enable_interrupt=True):
        self._rtc.enable_timer_interrupt(enable_interrupt)
        self._rtc.set_timer(ticks)

    def timer_elapsed(self):
        result = self._rtc.read_timer_flag()
        self._rtc.clear_timer_flag()
        return result

    def set_alarm(self, hours=0, minutes=0, seconds=0):
        self._rtc.clear_alarm_flag()
        self._rtc.clear_timer_flag()

        self._rtc.enable_alarm_interrupt(True)
        self._rtc.enable_timer_interrupt(True)

        year, month, day, hour, minute, second, _ = self._rtc.datetime()

        dt = datetime.datetime(year, month, day, hour, minute, second)

        dt += datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        self._rtc.set_alarm(dt.second, dt.minute, dt.hour)

    def clear_alarm(self):
        self._rtc.enable_alarm_interrupt(False)
        self._rtc.clear_alarm_flag()
        self._rtc.clear_timer_flag()
        self._rtc.unset_alarm()

    def alarm_status(self):
        return board.RTC_ALARM.value() == 0


builtins.rtc = RTC()
