"""The PIR motion sensor (HC-SR501) on GPIO17.

On the Pi this reads the sensor with gpiozero. In mock mode the spacebar
stands in for it (controls.py calls `trigger()`).

Motion counts once when the sensor's output goes high, and then not again
for MOTION_COOLDOWN seconds, so someone standing in front of the frame
doesn't make the horse trot over and over.
"""

import config


class MotionSensor:
    def __init__(self, mock: bool):
        self.mock = mock
        self.status = "mock (spacebar)" if mock else "off"
        self._pir = None
        self._was_high = False
        self._pending = False
        self.cooldown_left = 0.0
        if not mock:
            try:
                from gpiozero import MotionSensor as PIR  # only on the Pi
                self._pir = PIR(config.PIR_PIN)
                self.status = f"PIR on GPIO{config.PIR_PIN}"
            except Exception as err:  # missing library, wrong pin, no permission...
                print(f"[sensors] motion sensor disabled: {err}")
                self.status = "unavailable"

    def trigger(self) -> None:
        """Fake a motion event (mock mode)."""
        self._pending = True

    def update(self, dt: float) -> bool:
        """Call once per frame. True when motion should reach the horse."""
        self.cooldown_left = max(0.0, self.cooldown_left - dt)
        if self._pir is not None:
            high = bool(self._pir.motion_detected)
            if high and not self._was_high:  # only the moment it goes high
                self._pending = True
            self._was_high = high
        if not self._pending:
            return False
        self._pending = False
        if self.cooldown_left > 0:
            return False  # too soon: ignore
        self.cooldown_left = config.MOTION_COOLDOWN
        return True

    def close(self) -> None:
        if self._pir is not None:
            self._pir.close()
