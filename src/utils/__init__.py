"""
Utils package initialization.
Contains utility modules for the application.
"""
from .analytics import Analytics
from .cache import ChatCache
from .logger import AppLogger
from .monitor import PerformanceMonitor
from .logger import AppLogger

try:
    import psutil
except ImportError:
    raise ImportError("Please install psutil: pip install psutil")

logger = AppLogger()

__all__ = [
    'Analytics',
    'ChatCache',
    'AppLogger',
    'PerformanceMonitor'
]
__version__ = '1.0.0'


