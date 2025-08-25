# Sol-Ark 3-Phase Inverter Support Implementation Plan

## Overview
This document provides a detailed implementation plan for adding 3-phase Sol-Ark inverter support to the EMS-Dev Python Gateway while maintaining full SunSpec compliance for Models 701, 713, and 714.

## Architecture Design

### 1. Abstract Base Classes

#### `ems/inverters/base.py`
```python
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

class InverterClient(ABC):
    """Abstract base class for inverter clients"""
    
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
```

### 2. Extended Sol-Ark Data Structure

#### `ems/inverters/solark_data.py`
```python
from dataclasses import dataclass, field
from typing import List
import time
from .base import InverterData

@dataclass
class SolArkDataBase(InverterData):
    """Base Sol-Ark data structure with common fields"""
    
    # Diagnostic variables
    comm_version: int = 0
    serial_number_parts: List[int] = field(default_factory=lambda: [0] * 5)
    igbt_temp: float = 0.0
    dcdc_xfrmr_temp: float = 0.0
    
    # Battery variables
    battery_power: float = 0.0
    battery_current: float = 0.0
    battery_voltage: float = 0.0
    battery_soc: float = 0.0
    battery_temperature: float = 0.0
    
    # Energy counters
    battery_charge_energy: float = 0.0
    battery_discharge_energy: float = 0.0
    grid_buy_energy: float = 0.0
    grid_sell_energy: float = 0.0
    load_energy: float = 0.0
    pv_energy: float = 0.0
    
    # Power variables
    grid_power: float = 0.0
    inverter_output_power: float = 0.0
    load_power_total: float = 0.0
    pv_power_total: float = 0.0
    smart_load_power: float = 0.0
    
    # Power quality variables
    apparent_power: float = 0.0
    grid_power_factor: float = 0.0
    
    # Status variables
    inverter_status: int = 0
    grid_relay_status: int = 0
    generator_relay_status: int = 0
    grid_type: int = 0
    
    # Battery configuration
    battery_capacity: float = 0.0
    corrected_battery_capacity: float = 0.0
    
    # BMS variables
    bms_warning: int = 0
    bms_fault: int = 0

@dataclass
class SolArkSplitPhaseData(SolArkDataBase):
    """Sol-Ark split-phase specific data"""
    
    # Grid measurements (L1, L2)
    grid_voltage_l1l2: float = 0.0
    grid_voltage_l1n: float = 0.0
    grid_voltage_l2n: float = 0.0
    grid_current_l1: float = 0.0
    grid_current_l2: float = 0.0
    grid_frequency: float = 0.0
    
    # Load measurements (L1, L2)
    load_power_l1: float = 0.0
    load_power_l2: float = 0.0
    load_current_l1: float = 0.0
    load_current_l2: float = 0.0
    load_frequency: float = 0.0
    
    # Inverter measurements (L1, L2)
    inverter_voltage: float = 0.0
    inverter_voltage_ln: float = 0.0
    inverter_voltage_l2n: float = 0.0
    inverter_current_l1: float = 0.0
    inverter_current_l2: float = 0.0
    inverter_frequency: float = 0.0
    inverter_power_l1: float = 0.0
    inverter_power_l2: float = 0.0
    
    # PV measurements
    pv1_power: float = 0.0
    pv2_power: float = 0.0
    
    def get_phase_count(self) -> int:
        return 2

@dataclass
class SolArk3PhaseData(SolArkDataBase):
    """Sol-Ark 3-phase specific data"""
    
    # Grid measurements (L1, L2, L3)
    grid_voltage_l1l2: float = 0.0
    grid_voltage_l2l3: float = 0.0
    grid_voltage_l3l1: float = 0.0
    grid_voltage_l1n: float = 0.0
    grid_voltage_l2n: float = 0.0
    grid_voltage_l3n: float = 0.0
    grid_current_l1: float = 0.0
    grid_current_l2: float = 0.0
    grid_current_l3: float = 0.0
    grid_frequency: float = 0.0
    
    # Load measurements (L1, L2, L3)
    load_power_l1: float = 0.0
    load_power_l2: float = 0.0
    load_power_l3: float = 0.0
    load_current_l1: float = 0.0
    load_current_l2: float = 0.0
    load_current_l3: float = 0.0
    load_frequency: float = 0.0
    
    # Inverter measurements (L1, L2, L3)
    inverter_voltage_l1l2: float = 0.0
    inverter_voltage_l2l3: float = 0.0
    inverter_voltage_l3l1: float = 0.0
    inverter_voltage_l1n: float = 0.0
    inverter_voltage_l2n: float = 0.0
    inverter_voltage_l3n: float = 0.0
    inverter_current_l1: float = 0.0
    inverter_current_l2: float = 0.0
    inverter_current_l3: float = 0.0
    inverter_frequency: float = 0.0
    inverter_power_l1: float = 0.0
    inverter_power_l2: float = 0.0
    inverter_power_l3: float = 0.0
    
    # PV measurements (assuming 3 MPPT inputs)
    pv1_power: float = 0.0
    pv2_power: float = 0.0
    pv3_power: float = 0.0
    
    def get_phase_count(self) -> int:
        return 3
```

### 3. Sol-Ark 3-Phase Register Mapping

#### `ems/inverters/solark_3phase_registers.py`
```python
from enum import Enum
from dataclasses import dataclass
from typing import List

class SolArk3PhaseRegisterMap:
    """Sol-Ark 3-Phase Modbus register addresses"""
    
    # Extend base registers with 3-phase specific ones
    # Grid voltage registers (3-phase)
    GRID_VOLTAGE_L1N = 150
    GRID_VOLTAGE_L2N = 151
    GRID_VOLTAGE_L3N = 152  # New for 3-phase
    GRID_VOLTAGE_L1L2 = 153
    GRID_VOLTAGE_L2L3 = 154  # New for 3-phase
    GRID_VOLTAGE_L3L1 = 155  # New for 3-phase
    
    # Grid current registers (3-phase)
    GRID_CURRENT_L1 = 160
    GRID_CURRENT_L2 = 161
    GRID_CURRENT_L3 = 162  # New for 3-phase
    
    # Inverter voltage registers (3-phase)
    INVERTER_VOLTAGE_L1N = 170
    INVERTER_VOLTAGE_L2N = 171
    INVERTER_VOLTAGE_L3N = 172  # New for 3-phase
    INVERTER_VOLTAGE_L1L2 = 173
    INVERTER_VOLTAGE_L2L3 = 174  # New for 3-phase
    INVERTER_VOLTAGE_L3L1 = 175  # New for 3-phase
    
    # Inverter current registers (3-phase)
    INVERTER_CURRENT_L1 = 180
    INVERTER_CURRENT_L2 = 181
    INVERTER_CURRENT_L3 = 182  # New for 3-phase
    
    # Load measurements (3-phase)
    LOAD_POWER_L1 = 190
    LOAD_POWER_L2 = 191
    LOAD_POWER_L3 = 192  # New for 3-phase
    LOAD_CURRENT_L1 = 193
    LOAD_CURRENT_L2 = 194
    LOAD_CURRENT_L3 = 195  # New for 3-phase
    
    # Inverter power (3-phase)
    INVERTER_POWER_L1 = 200
    INVERTER_POWER_L2 = 201
    INVERTER_POWER_L3 = 202  # New for 3-phase
    
    # PV inputs (3 MPPT for 3-phase)
    PV1_POWER = 210
    PV2_POWER = 211
    PV3_POWER = 212
    
    # All other registers remain the same as split-phase
```

### 4. Inverter Factory

#### `ems/inverters/factory.py`
```python
from typing import Dict, Any
from .base import InverterClient
from .solark_split_phase import SolArkSplitPhaseClient
from .solark_3phase import SolArk3PhaseClient

class InverterFactory:
    """Factory for creating inverter clients"""
    
    INVERTER_TYPES = {
        "solark_split_phase": SolArkSplitPhaseClient,
        "solark_3phase": SolArk3PhaseClient,
    }
    
    @classmethod
    def create_client(cls, config: Dict[str, Any]) -> InverterClient:
        """Create inverter client based on configuration"""
        inverter_config = config.get("inverter", {})
        inverter_type = inverter_config.get("type", "solark_split_phase")
        
        if inverter_type not in cls.INVERTER_TYPES:
            raise ValueError(f"Unsupported inverter type: {inverter_type}")
        
        client_class = cls.INVERTER_TYPES[inverter_type]
        
        # Extract connection parameters
        serial_config = config.get("serial", {})
        
        return client_class(
            port=serial_config.get("port", "/dev/ttyUSB0"),
            baudrate=serial_config.get("baudrate", 9600),
            modbus_address=inverter_config.get("modbus_address", 1)
        )
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported inverter types"""
        return list(cls.INVERTER_TYPES.keys())
```

### 5. SunSpec Model Extensions

#### Enhanced SunSpec Models for 3-Phase Support

The existing SunSpec models (701, 713, 714) need to be extended to properly handle 3-phase data:

**Model 701 (Inverter) - 3-Phase Extensions:**
- Add L3 voltage, current, and power measurements
- Update AC wiring type to support 3-phase Wye (type 2)
- Extend phase-specific measurements (WL3, VAL3, AL3, etc.)

**Model 713 (Battery) - No Changes:**
- Battery model remains the same for both split-phase and 3-phase

**Model 714 (DC Measurement) - Minor Extensions:**
- Support for 3 PV inputs instead of 2
- Updated port configurations

### 6. Configuration Updates

#### `config.yaml` Extensions
```yaml
# Inverter Configuration (NEW SECTION)
inverter:
  type: "solark_split_phase"  # Options: "solark_split_phase", "solark_3phase"
  modbus_address: 1
  poll_interval: 1.0
  max_retries: 3
  retry_delay: 0.5

# Serial/RS485 Configuration (EXISTING - NO CHANGES)
serial:
  port: "/dev/ttyRS485"
  baudrate: 9600
  bytesize: 8
  parity: "N"
  stopbits: 1
  timeout: 2.0

# Legacy solark section (DEPRECATED but maintained for backward compatibility)
solark:
  modbus_address: 1  # Will be overridden by inverter.modbus_address
  poll_interval: 1.0  # Will be overridden by inverter.poll_interval
  max_retries: 3
  retry_delay: 0.5
```

### 7. Main Application Updates

#### `ems/main.py` Modifications
- Replace direct `SolArkModbusClient` instantiation with `InverterFactory`
- Update configuration loading to handle new inverter section
- Maintain backward compatibility with existing configurations

### 8. Implementation Steps

1. **Create abstract base classes** (`ems/inverters/base.py`)
2. **Create extended data structures** (`ems/inverters/solark_data.py`)
3. **Refactor existing Sol-Ark client** to inherit from base classes
4. **Implement 3-phase Sol-Ark client** (`ems/inverters/solark_3phase.py`)
5. **Create 3-phase register mappings** (`ems/inverters/solark_3phase_registers.py`)
6. **Implement inverter factory** (`ems/inverters/factory.py`)
7. **Update SunSpec mapper** to handle both phase types
8. **Update main application** to use factory pattern
9. **Update configuration system** with backward compatibility
10. **Test both split-phase and 3-phase functionality**

### 9. SunSpec Compliance

The implementation will maintain full SunSpec compliance:

- **Model 1 (Common)**: Device identification - no changes needed
- **Model 701 (Inverter)**: Extended for 3-phase with proper AC wiring type
- **Model 713 (Battery)**: No changes needed
- **Model 714 (DC Measurement)**: Extended for 3 PV inputs

### 10. Backward Compatibility

- Existing `config.yaml` files will continue to work
- Legacy `solark` configuration section will be supported
- Default behavior remains split-phase Sol-Ark
- No breaking changes to existing APIs

### 11. Testing Strategy

- Unit tests for each inverter type
- Integration tests with SunSpec models
- Configuration validation tests
- Backward compatibility tests
- SunSpec compliance validation

## File Structure

```
ems/
├── inverters/
│   ├── __init__.py
│   ├── base.py                    # Abstract base classes
│   ├── solark_data.py            # Data structures
│   ├── solark_split_phase.py     # Refactored existing client
│   ├── solark_3phase.py          # New 3-phase client
│   ├── solark_3phase_registers.py # 3-phase register mappings
│   └── factory.py                # Inverter factory
├── main.py                       # Updated main application
├── sunspec_models.py            # Enhanced SunSpec mapper
└── config.yaml                  # Extended configuration
```

This implementation provides a clean, extensible architecture that maintains full SunSpec compliance while adding 3-phase Sol-Ark support through configuration-driven selection.