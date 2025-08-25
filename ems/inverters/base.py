"""
Abstract base classes for inverter implementations

This module defines the abstract interfaces that all inverter implementations
must follow, ensuring consistent behavior across different inverter types.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time


@dataclass
class InverterData(ABC):
    """Abstract base class for inverter data structures"""
    
    last_update: float = 0.0
    last_failure: float = 0.0
    
    @abstractmethod
    def get_phase_count(self) -> int:
        """Return number of phases (1, 2, or 3)"""
        pass
    
    @abstractmethod
    def get_inverter_type(self) -> str:
        """Return inverter type identifier"""
        pass


class InverterClient(ABC):
    """Abstract base class for inverter clients"""
    
    def __init__(self, port: str, baudrate: int = 9600, modbus_address: int = 1):
        """
        Initialize inverter client
        
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0')
            baudrate: Serial baudrate (default: 9600)
            modbus_address: Modbus slave address (default: 1)
        """
        self.port = port
        self.baudrate = baudrate
        self.modbus_address = modbus_address
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the inverter"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the inverter"""
        pass
    
    @abstractmethod
    def poll(self) -> bool:
        """Poll data from the inverter"""
        pass
    
    @property
    @abstractmethod
    def data(self) -> InverterData:
        """Get current inverter data"""
        pass
    
    @abstractmethod
    def get_inverter_type(self) -> str:
        """Get inverter type identifier"""
        pass
    
    # Convenience methods that can be overridden by implementations
    def is_grid_connected(self) -> bool:
        """Check if grid is connected - default implementation"""
        return False
    
    def is_generator_connected(self) -> bool:
        """Check if generator is connected - default implementation"""
        return False
    
    def is_battery_charging(self) -> bool:
        """Check if battery is charging - default implementation"""
        return False
    
    def is_battery_discharging(self) -> bool:
        """Check if battery is discharging - default implementation"""
        return False
    
    def is_selling_to_grid(self) -> bool:
        """Check if selling power to grid - default implementation"""
        return False
    
    def is_buying_from_grid(self) -> bool:
        """Check if buying power from grid - default implementation"""
        return False