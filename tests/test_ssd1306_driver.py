import importlib
import sys
import types
import unittest
from pathlib import Path


FIRMWARE_DIR = Path(__file__).resolve().parents[1] / "firmware"
sys.path.insert(0, str(FIRMWARE_DIR))


class FakeFrameBuffer:
    def __init__(self, buffer, width, height, pixel_format):
        self.buffer = buffer
        self.width = width
        self.height = height

    def fill(self, value):
        self.buffer[:] = bytes([0xFF if value else 0x00]) * len(self.buffer)


class FakeI2C:
    def __init__(self):
        self.writes = []
        self.vector_writes = []

    def writeto(self, address, data):
        self.writes.append((address, bytes(data)))

    def writevto(self, address, vectors):
        self.vector_writes.append((address, tuple(bytes(item) for item in vectors)))


class SSD1306DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        micropython = types.ModuleType("micropython")
        micropython.const = lambda value: value
        framebuf = types.ModuleType("framebuf")
        framebuf.FrameBuffer = FakeFrameBuffer
        framebuf.MONO_VLSB = 0
        cls.original_modules = {
            name: sys.modules.get(name)
            for name in ("micropython", "framebuf", "ssd1306")
        }
        sys.modules["micropython"] = micropython
        sys.modules["framebuf"] = framebuf
        sys.modules.pop("ssd1306", None)
        cls.driver = importlib.import_module("ssd1306")

    @classmethod
    def tearDownClass(cls):
        for name, module in cls.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_i2c_driver_initializes_128_by_64_display_at_0x3c(self):
        bus = FakeI2C()
        display = self.driver.SSD1306_I2C(128, 64, bus)

        self.assertEqual(display.addr, 0x3C)
        self.assertEqual(len(display.buffer), 1024)
        self.assertGreater(len(bus.writes), 20)
        self.assertEqual(bus.vector_writes[-1][0], 0x3C)
        self.assertEqual(bus.vector_writes[-1][1][0], b"\x40")
        self.assertEqual(len(bus.vector_writes[-1][1][1]), 1024)


if __name__ == "__main__":
    unittest.main()
