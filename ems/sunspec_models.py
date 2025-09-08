"""
SunSpec Models Implementation

This module implements SunSpec-compliant data models for exposing Sol-Ark inverter data
in a standardized format over Modbus TCP.
"""

import logging
import time
from dataclasses import dataclass, field

from .solark_client import SolArkData


@dataclass
class SunSpecCommonModel:
    """SunSpec Common Model (Model 1) - Device identification"""
    
    # Fixed header
    sunspec_id = 0x53756E53  # 'SunS' in ASCII
    model_id = 1
    model_length = 66
    
    # Device information
    manufacturer = "Energy IoT Open Source"
    model = "EMS-Dev Python"
    options = "Sol-Ark Gateway"
    version = "1.0.0"
    serial_number = "EMS-PY-001"
    device_address = 1


@dataclass
class SunSpecInverterModel:
    """SunSpec Inverter Model (Model 701) - Base class for Grid and Load instances"""
    
    # Model header
    model_id = 701
    model_length = 153  # Match C implementation
    
    # AC measurements
    ac_current = 0.0  # A - AC Total Current value
    ac_current_a = 0.0  # AphA - AC Phase A Current value
    ac_current_b = 0.0  # AphB - AC Phase B Current value
    ac_voltage_ab = 0.0  # PPVphAB - AC Voltage Phase AB value
    ac_power = 0.0  # W - AC Power value
    ac_frequency = 0.0  # Hz - AC Frequency value
    ac_energy = 0.0  # WH - AC Lifetime Energy production
    
    # DC measurements
    dc_current = 0.0  # DCA - DC Current value
    dc_voltage = 0.0  # DCV - DC Voltage value
    dc_power = 0.0  # DCW - DC Power value
    
    # Temperature
    cabinet_temperature = 0.0  # TmpCab - Cabinet Temperature
    
    # Status
    operating_state = 0  # St - Operating State
    vendor_operating_state = 0  # StVnd - Vendor Operating State
    
    # Scale factors (SF)
    current_sf = -2  # A_SF
    voltage_sf = -1  # V_SF
    power_sf = 0  # W_SF
    energy_sf = 0  # WH_SF
    frequency_sf = -2  # Hz_SF
    temperature_sf = 0  # Tmp_SF


@dataclass
class SunSpecGridModel(SunSpecInverterModel):
    """SunSpec Grid Model (Model 701) - Grid-side measurements"""
    pass


@dataclass
class SunSpecLoadModel(SunSpecInverterModel):
    """SunSpec Load Model (Model 701) - Load-side measurements"""
    pass


@dataclass
class SunSpecBatteryModel:
    """SunSpec Battery Model (Model 713) - Battery bank model"""
    
    # Model header
    model_id = 713
    model_length = 7  # Match C implementation (DER Storage Capacity Model)
    
    # Battery measurements
    battery_voltage = 0.0  # V - Battery voltage
    battery_current = 0.0  # A - Battery current
    battery_power = 0.0  # W - Battery power
    battery_soc = 0.0  # SoC - State of charge
    battery_temperature = 0.0  # Tmp - Battery temperature
    
    # Battery configuration
    battery_capacity = 0.0  # AHRtg - Amp-hour rating
    battery_energy_capacity = 0.0  # WHRtg - Watt-hour rating
    
    # Battery status
    battery_status = 0  # St - Battery status
    
    # Scale factors
    voltage_sf = -1  # V_SF
    current_sf = -2  # A_SF
    power_sf = 0  # W_SF
    energy_sf = 0  # WH_SF
    soc_sf = 0  # SoC_SF
    temperature_sf = 0  # Tmp_SF


@dataclass
class SunSpecDCPort:
    """SunSpec DC Port for Model 714"""
    
    # Port identification
    port_type: int = 0  # PrtTyp - 0=PV, 1=ESS, 2=EV, 3=INJ, 4=ABS, 5=BIDIR, 6=DC_DC
    port_id: int = 0  # ID - Port ID number
    port_id_string: str = ""  # IDStr - Port ID string (8 registers)
    
    # DC measurements
    dc_current: float = 0.0  # DCA - DC current for the port
    dc_voltage: float = 0.0  # DCV - DC voltage for the port
    dc_power: float = 0.0  # DCW - DC power for the port
    dc_energy_injected: int = 0  # DCWhInj - Total cumulative DC energy injected
    dc_energy_absorbed: int = 0  # DCWhAbs - Total cumulative DC energy absorbed
    
    # Status and temperature
    temperature: float = 0.0  # Tmp - DC port temperature
    dc_status: int = 0  # DCSta - 0=OFF, 1=ON, 2=WARNING, 3=ERROR
    dc_alarm: int = 0  # DCAlrm - DC port alarm bitfield (32-bit)


@dataclass
class SunSpec714Model:
    """SunSpec DER DC Measurement Model (Model 714) - Dynamic port configuration based on inverter type"""
    
    # Model header
    model_id: int = 714
    model_length: int = 0  # Will be calculated based on number of ports
    
    # General DC measurements
    port_alarms: int = 0  # PrtAlrms - Bitfield of ports with active alarms
    num_ports: int = 5  # NPrt - Default: 4 PV + 1 ESS (will be updated based on inverter type)
    total_dc_current: float = 0.0  # DCA - Total DC current for all ports
    total_dc_power: float = 0.0  # DCW - Total DC power for all ports
    total_dc_energy_injected: int = 0  # DCWhInj - Total cumulative DC energy injected
    total_dc_energy_absorbed: int = 0  # DCWhAbs - Total cumulative DC energy absorbed
    
    # Scale factors
    current_sf: int = -2  # DCA_SF - DC current scale factor
    voltage_sf: int = -1  # DCV_SF - DC voltage scale factor
    power_sf: int = 0  # DCW_SF - DC power scale factor
    energy_sf: int = -3  # DCWH_SF - DC energy scale factor
    temperature_sf: int = -1  # Tmp_SF - Temperature scale factor
    
    # DC Ports - will be configured dynamically based on inverter type
    ports: list = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize ports if not already configured"""
        if not self.ports:
            self.configure_ports_for_inverter_type(3)  # Default to 3-phase configuration
    
    def configure_ports_for_inverter_type(self, phase_count: int):
        """Configure ports based on inverter type (phase count)"""
        # Always have 4 PV ports (with PV4 uninitialized)
        self.ports = [
            SunSpecDCPort(port_type=0, port_id=1, port_id_string="MPPT1"),      # PV Port 1 (register 672/676/677)
            SunSpecDCPort(port_type=0, port_id=2, port_id_string="MPPT2"),      # PV Port 2 (register 673/678/679)
            SunSpecDCPort(port_type=0, port_id=3, port_id_string="MPPT3"),      # PV Port 3 (register 674/680/681)
            SunSpecDCPort(port_type=0, port_id=4, port_id_string="MPPT4"),      # PV Port 4 (register 675/682/683) - uninitialized
            SunSpecDCPort(port_type=1, port_id=5, port_id_string="BATT1")       # Battery Port 1 (register 590/587/591)
        ]
        
        # For split-phase/single-phase systems, use 5 ports; for 3-phase, use 6 ports
        if phase_count == 2:  # Split-phase or single-phase
            self.num_ports = 5  # 4 PV + 1 ESS (for single-phase and split-phase)
        else:  # 3-phase
            self.ports.append(
                SunSpecDCPort(port_type=1, port_id=6, port_id_string="BATT2")   # Battery Port 2 (register 595/593/594)
            )
            self.num_ports = 6  # 4 PV + 2 ESS
        
        # Recalculate model length
        self._calculate_model_length()
    
    def _calculate_model_length(self):
        """Calculate model length based on number of ports"""
        # Base model: 2 (header) + 2 (PrtAlrms) + 1 (NPrt) + 1 (DCA) + 1 (DCW) + 4 (DCWhInj) + 4 (DCWhAbs) + 5 (scale factors) = 20
        # Per port: 1 (PrtTyp) + 1 (ID) + 8 (IDStr) + 1 (DCA) + 1 (DCV) + 1 (DCW) + 4 (DCWhInj) + 4 (DCWhAbs) + 1 (Tmp) + 1 (DCSta) + 2 (DCAlrm) = 25
        base_length = 18  # Without header
        port_length = 25
        self.model_length = base_length + (self.num_ports * port_length)


class SunSpecRegisterMap:
    """SunSpec register mapping for Modbus TCP server with dual 701 instances and 714 model"""
    
    # Base addresses for each model
    SUNSPEC_BASE_ADDR = 40000
    COMMON_MODEL_BASE = SUNSPEC_BASE_ADDR + 2  # 40002 (after SunS header)
    GRID_MODEL_BASE = COMMON_MODEL_BASE + 66 + 2  # 40070 (after Common Model + header)
    LOAD_MODEL_BASE = GRID_MODEL_BASE + 153 + 2  # 40225 (after Grid Model + header)
    STORAGE_MODEL_BASE = LOAD_MODEL_BASE + 153 + 2  # 40380 (after Load Model + header)
    DC_MODEL_BASE = STORAGE_MODEL_BASE + 7 + 2  # 40389 (after Storage Model + header)
    # END_MODEL_BASE will be calculated dynamically based on actual number of ports
    
    # SunSpec Header
    SUNSPEC_ID = SUNSPEC_BASE_ADDR  # 40000-40001 (2 registers)
    
    # Common Model (1) registers
    COMMON_MODEL_ID = COMMON_MODEL_BASE + 0  # 40002
    COMMON_MODEL_LENGTH = COMMON_MODEL_BASE + 1  # 40003
    MANUFACTURER = COMMON_MODEL_BASE + 2  # 40004-40019 (16 registers)
    MODEL = COMMON_MODEL_BASE + 18  # 40020-40035 (16 registers)
    OPTIONS = COMMON_MODEL_BASE + 34  # 40036-40043 (8 registers)
    VERSION = COMMON_MODEL_BASE + 42  # 40044-40051 (8 registers)
    SERIAL_NUMBER = COMMON_MODEL_BASE + 50  # 40052-40067 (16 registers)
    DEVICE_ADDRESS = COMMON_MODEL_BASE + 66  # 40068
    
    # Grid Model (701) registers - First instance
    GRID_MODEL_ID = GRID_MODEL_BASE  # 40070
    GRID_MODEL_LENGTH = GRID_MODEL_BASE + 1  # 40071
    GRID_AC_TYPE = GRID_MODEL_BASE + 2  # 40072
    GRID_OPERATING_STATE = GRID_MODEL_BASE + 3  # 40073
    GRID_STATUS = GRID_MODEL_BASE + 4  # 40074
    GRID_CONNECTION = GRID_MODEL_BASE + 5  # 40075
    GRID_ALARM = GRID_MODEL_BASE + 6  # 40076-40077 (2 registers)
    GRID_DER_MODE = GRID_MODEL_BASE + 8  # 40078-40079 (2 registers)
    GRID_AC_POWER = GRID_MODEL_BASE + 10  # 40080
    GRID_AC_VA = GRID_MODEL_BASE + 11  # 40081
    GRID_AC_VAR = GRID_MODEL_BASE + 12  # 40082
    GRID_AC_PF = GRID_MODEL_BASE + 13  # 40083
    GRID_AC_CURRENT = GRID_MODEL_BASE + 14  # 40084
    GRID_AC_VOLTAGE_LL = GRID_MODEL_BASE + 15  # 40085
    GRID_AC_VOLTAGE_LN = GRID_MODEL_BASE + 16  # 40086
    GRID_AC_FREQUENCY = GRID_MODEL_BASE + 17  # 40087-40088 (2 registers)
    
    # Load Model (701) registers - Second instance
    LOAD_MODEL_ID = LOAD_MODEL_BASE  # 40225
    LOAD_MODEL_LENGTH = LOAD_MODEL_BASE + 1  # 40226
    LOAD_AC_TYPE = LOAD_MODEL_BASE + 2  # 40227
    LOAD_OPERATING_STATE = LOAD_MODEL_BASE + 3  # 40228
    LOAD_STATUS = LOAD_MODEL_BASE + 4  # 40229
    LOAD_CONNECTION = LOAD_MODEL_BASE + 5  # 40230
    LOAD_ALARM = LOAD_MODEL_BASE + 6  # 40231-40232 (2 registers)
    LOAD_DER_MODE = LOAD_MODEL_BASE + 8  # 40233-40234 (2 registers)
    LOAD_AC_POWER = LOAD_MODEL_BASE + 10  # 40235
    LOAD_AC_VA = LOAD_MODEL_BASE + 11  # 40236
    LOAD_AC_VAR = LOAD_MODEL_BASE + 12  # 40237
    LOAD_AC_PF = LOAD_MODEL_BASE + 13  # 40238
    LOAD_AC_CURRENT = LOAD_MODEL_BASE + 14  # 40239
    LOAD_AC_VOLTAGE_LL = LOAD_MODEL_BASE + 15  # 40240
    LOAD_AC_VOLTAGE_LN = LOAD_MODEL_BASE + 16  # 40241
    LOAD_AC_FREQUENCY = LOAD_MODEL_BASE + 17  # 40242-40243 (2 registers)
    
    # Storage Model (713) registers
    STORAGE_MODEL_ID = STORAGE_MODEL_BASE + 0  # 40380
    STORAGE_MODEL_LENGTH = STORAGE_MODEL_BASE + 1  # 40381
    STORAGE_ENERGY_RATING = STORAGE_MODEL_BASE + 2  # 40382
    STORAGE_ENERGY_AVAILABLE = STORAGE_MODEL_BASE + 3  # 40383
    STORAGE_SOC = STORAGE_MODEL_BASE + 4  # 40384
    STORAGE_SOH = STORAGE_MODEL_BASE + 5  # 40385
    STORAGE_STATUS = STORAGE_MODEL_BASE + 6  # 40386
    STORAGE_SF_ENERGY = STORAGE_MODEL_BASE + 7  # 40387
    STORAGE_SF_PERCENT = STORAGE_MODEL_BASE + 8  # 40388
    
    # DC Model (714) registers
    DC_MODEL_ID = DC_MODEL_BASE + 0  # 40389
    DC_MODEL_LENGTH = DC_MODEL_BASE + 1  # 40390
    DC_PORT_ALARMS = DC_MODEL_BASE + 2  # 40391-40392 (2 registers for bitfield32)
    DC_NUM_PORTS = DC_MODEL_BASE + 4  # 40393
    DC_TOTAL_CURRENT = DC_MODEL_BASE + 5  # 40394
    DC_TOTAL_POWER = DC_MODEL_BASE + 6  # 40395
    DC_TOTAL_ENERGY_INJ = DC_MODEL_BASE + 7  # 40396-40399 (4 registers for uint64)
    DC_TOTAL_ENERGY_ABS = DC_MODEL_BASE + 11  # 40400-40403 (4 registers for uint64)
    DC_CURRENT_SF = DC_MODEL_BASE + 15  # 40404
    DC_VOLTAGE_SF = DC_MODEL_BASE + 16  # 40405
    DC_POWER_SF = DC_MODEL_BASE + 17  # 40406
    DC_ENERGY_SF = DC_MODEL_BASE + 18  # 40407
    DC_TEMP_SF = DC_MODEL_BASE + 19  # 40408
    
    # DC Port base addresses (each port takes 25 registers)
    DC_PORT1_BASE = DC_MODEL_BASE + 20  # 40409 - PV Port 1
    DC_PORT2_BASE = DC_PORT1_BASE + 25  # 40434 - PV Port 2
    DC_PORT3_BASE = DC_PORT2_BASE + 25  # 40459 - PV Port 3
    DC_PORT4_BASE = DC_PORT3_BASE + 25  # 40484 - PV Port 4 (uninitialized)
    DC_PORT5_BASE = DC_PORT4_BASE + 25  # 40509 - ESS Port 1 (Battery 1)
    DC_PORT6_BASE = DC_PORT5_BASE + 25  # 40534 - ESS Port 2 (Battery 2) - only for 3-phase
    
    @classmethod
    def calculate_end_model_base(cls, num_ports: int) -> int:
        """Calculate END_MODEL_BASE dynamically based on number of DC ports"""
        model_length = 18 + (num_ports * 25)  # 18 base + num_ports * 25 registers per port
        return cls.DC_MODEL_BASE + model_length + 2  # +2 for header
    
    @classmethod
    def get_end_model_registers(cls, num_ports: int) -> tuple:
        """Get END_MODEL register addresses based on number of ports"""
        end_base = cls.calculate_end_model_base(num_ports)
        return (end_base, end_base + 1)  # (END_MODEL_ID, END_MODEL_LENGTH)
    


class SunSpecMapper:
    """Maps Sol-Ark data to SunSpec models with dual 701 instances"""
    # Constants for register initialization
    NULL_UINT16 = 0xFFFF  # Not implemented value for unsigned 16-bit
    NULL_INT16 = 0x8000   # Not implemented value for signed 16-bit
    
    # Register offset groups for signed int16 values that need NULL_INT16
    GRID_SIGNED_OFFSETS = [35, 36, 39, 40, 42, 43, 44, 65, 66, 67, 87, 88, 89, 90, 91]
    LOAD_SIGNED_OFFSETS = [35, 36, 39, 40, 42, 43, 44, 65, 66, 67, 87, 88, 89, 90, 91]
    
    # Register descriptions for better maintainability
    REGISTER_DESCRIPTIONS = {
        35: "TmpAmb - Ambient Temperature",
        36: "TmpCab - Cabinet Temperature",
        39: "TmpSw - Switch Temperature",
        40: "TmpOt - Other Temperature",
        42: "VAL1",
        43: "VarL1",
        44: "PFL1",
        65: "VAL2",
        66: "VarL2",
        67: "PFL2",
        87: "WL3",
        88: "VAL3",
        90: "VarL3",
        89: "PFL3",
        91: "AL3"
    }
    
    def __init__(self, device_info, inverter_type="3phase"):
        """
        Initialize SunSpec mapper
        
        Args:
            device_info: Device information dictionary
            inverter_type: Type of inverter ("split_phase", "3phase", etc.)
        """
        self.logger = logging.getLogger(__name__)
        self.device_info = device_info
        self.inverter_type = inverter_type
                
        # Determine phase count from inverter type
        if "split" in inverter_type.lower() or "single" in inverter_type.lower():
            self.phase_count = 2  # Split-phase or single-phase
        else:
            self.phase_count = 3  # 3-phase
        
        # Initialize models
        self.common_model = SunSpecCommonModel()
        
        # Update with device info
        if "manufacturer" in device_info:
            self.common_model.manufacturer = device_info["manufacturer"]
        if "model" in device_info:
            self.common_model.model = device_info["model"]
        if "options" in device_info:
            self.common_model.options = device_info["options"]
        if "version" in device_info:
            self.common_model.version = device_info["version"]
        if "serial_number" in device_info:
            self.common_model.serial_number = device_info["serial_number"]
        
        # Initialize dual 701 models
        self.grid_model = SunSpecGridModel()
        self.load_model = SunSpecLoadModel()
        self.battery_model = SunSpecBatteryModel()
        
        # Initialize DC model with appropriate port configuration
        self.dc_model = SunSpec714Model()
        self.dc_model.configure_ports_for_inverter_type(self.phase_count)
        
        # Register map for Modbus server
        self.registers = {}
        self._initialize_registers()
    
    def _initialize_registers(self):
        """Initialize the Modbus register map with dual 701 instances"""
        
        # Common Model registers
        self._set_register_32bit(SunSpecRegisterMap.SUNSPEC_ID, self.common_model.sunspec_id)
        self._set_register(SunSpecRegisterMap.COMMON_MODEL_ID, self.common_model.model_id)
        self._set_register(SunSpecRegisterMap.COMMON_MODEL_LENGTH, self.common_model.model_length)
        self._set_string_registers(SunSpecRegisterMap.MANUFACTURER, self.common_model.manufacturer, 16)
        self._set_string_registers(SunSpecRegisterMap.MODEL, self.common_model.model, 16)
        self._set_string_registers(SunSpecRegisterMap.OPTIONS, self.common_model.options, 8)
        self._set_string_registers(SunSpecRegisterMap.VERSION, self.common_model.version, 8)
        self._set_string_registers(SunSpecRegisterMap.SERIAL_NUMBER, self.common_model.serial_number, 16)
        self._set_register(SunSpecRegisterMap.DEVICE_ADDRESS, self.common_model.device_address)
        
        ###############################################
        # Grid Model (701) header - First instance
        ###############################################
        self._set_register(SunSpecRegisterMap.GRID_MODEL_ID, self.grid_model.model_id)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_LENGTH, self.grid_model.model_length)
        
        # Initialize all grid model values to "not implemented" (0xFFFF)
        for i in range(2, self.grid_model.model_length + 2):  # +2 for header
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + i, 0xFFFF)
        
        # Initialize 701 model signed int values to "not implemented" using bulk operation
        self._set_signed_registers_to_null(SunSpecRegisterMap.GRID_MODEL_BASE, self.GRID_SIGNED_OFFSETS)
        
        # Set scale factors for Grid model
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 113, -2)  # Current scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 114, -1)  # Voltage scale factor: -1 (0.1)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 115, -2)  # Frequency scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 116, 0)   # Power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 117, -2)  # Power factor scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 118, 0)   # Apparent power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 119, 0)   # Reactive power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 120, -3)  # Energy scale factor: -3 (0.001)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 121, -3)  # Reactive energy scale factor: -3 (0.001)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 122, -1)  # Temperature scale factor: -1 (0.1)

        ###############################################
        # Load Model (701) header - Second instance
        ###############################################
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_ID, self.load_model.model_id)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_LENGTH, self.load_model.model_length)
        
        # Initialize all load model values to "not implemented" (0xFFFF)
        for i in range(2, self.load_model.model_length + 2):  # +2 for header
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + i, 0xFFFF)
        
        # Initialize 701 model signed int values to "not implemented" using bulk operation
        self._set_signed_registers_to_null(SunSpecRegisterMap.LOAD_MODEL_BASE, self.LOAD_SIGNED_OFFSETS)
        
        # Set scale factors for Load model
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 113, -2)  # Current scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 114, -1)  # Voltage scale factor: -1 (0.1)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 115, -2)  # Frequency scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 116, 0)   # Power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 117, -2)  # Power factor scale factor: -2 (0.01)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 118, 0)   # Apparent power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 119, 0)   # Reactive power scale factor: 0 (1)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 120, -3)  # Energy scale factor: -3 (0.001)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 121, -3)  # Reactive energy scale factor: -3 (0.001)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 122, -1)  # Temperature scale factor: -1 (0.1)
        

        ###############################################
        # Storage Model (713)
        ###############################################
        # Storage Model header
        self._set_register(SunSpecRegisterMap.STORAGE_MODEL_ID, self.battery_model.model_id)
        self._set_register(SunSpecRegisterMap.STORAGE_MODEL_LENGTH, self.battery_model.model_length)
        
        # Initialize all storage model values to "not implemented" (0xFFFF)
        for i in range(2, self.battery_model.model_length + 2):  # +2 for header
            self._set_register(SunSpecRegisterMap.STORAGE_MODEL_BASE + i, 0xFFFF)
        
        # Set scale factors for storage model
        self._set_register(SunSpecRegisterMap.STORAGE_SF_ENERGY, 0)  # Energy scale factor: 0 (1) - values in Wh
        self._set_register(SunSpecRegisterMap.STORAGE_SF_PERCENT, -1)  # Percentage scale factor: -1 (0.1)
        
        ###############################################
        # DC Measurement Model (714)
        ###############################################
        # DC Model (714) header
        self._set_register(SunSpecRegisterMap.DC_MODEL_ID, self.dc_model.model_id)
        self._set_register(SunSpecRegisterMap.DC_MODEL_LENGTH, self.dc_model.model_length)
        
        # Initialize DC model general registers
        self._set_register_32bit(SunSpecRegisterMap.DC_PORT_ALARMS, 0)  # No port alarms initially
        self._set_register(SunSpecRegisterMap.DC_NUM_PORTS, self.dc_model.num_ports)
        self._set_register(SunSpecRegisterMap.DC_TOTAL_CURRENT, 0)  # Will be updated with real data
        self._set_register(SunSpecRegisterMap.DC_TOTAL_POWER, 0)  # Will be updated with real data
        
        # Initialize total energy registers (64-bit values)
        for i in range(4):
            self._set_register(SunSpecRegisterMap.DC_TOTAL_ENERGY_INJ + i, 0)
            self._set_register(SunSpecRegisterMap.DC_TOTAL_ENERGY_ABS + i, 0)
        
        # Set scale factors for DC model
        self._set_register(SunSpecRegisterMap.DC_CURRENT_SF, self.dc_model.current_sf)
        self._set_register(SunSpecRegisterMap.DC_VOLTAGE_SF, self.dc_model.voltage_sf)
        self._set_register(SunSpecRegisterMap.DC_POWER_SF, self.dc_model.power_sf)
        self._set_register(SunSpecRegisterMap.DC_ENERGY_SF, self.dc_model.energy_sf)
        self._set_register(SunSpecRegisterMap.DC_TEMP_SF, self.dc_model.temperature_sf)
        
        # Initialize DC ports dynamically based on actual number of ports
        port_bases = [SunSpecRegisterMap.DC_PORT1_BASE, SunSpecRegisterMap.DC_PORT2_BASE,
                     SunSpecRegisterMap.DC_PORT3_BASE, SunSpecRegisterMap.DC_PORT4_BASE,
                     SunSpecRegisterMap.DC_PORT5_BASE]
        
        # Add 6th port base only if we have 6 ports (3-phase systems)
        if self.dc_model.num_ports == 6:
            port_bases.append(SunSpecRegisterMap.DC_PORT6_BASE)
        
        for i, port_base in enumerate(port_bases):
            if i >= len(self.dc_model.ports):
                break  # Don't initialize ports that don't exist
                
            port = self.dc_model.ports[i]
            
            # Port type and ID
            self._set_register(port_base + 0, port.port_type)  # PrtTyp
            self._set_register(port_base + 1, port.port_id)    # ID
            
            # Port ID string (8 registers)
            self._set_string_registers(port_base + 2, port.port_id_string, 8)
            
            # Initialize port measurements (will be updated with real data)
            if i == 3:  # Port 4 (PV4) - set as uninitialized
                self._set_register(port_base + 10, 0xFFFF)  # DCA - uninitialized
                self._set_register(port_base + 11, 0xFFFF)  # DCV - uninitialized
                self._set_register(port_base + 12, 0xFFFF)  # DCW - uninitialized
                self._set_register(port_base + 21, 0x8000)  # Tmp - uninitialized (signed)
                self._set_register(port_base + 22, 0xFFFF)  # DCSta - uninitialized
            elif i == 5 and self.dc_model.num_ports == 6:  # Port 6 (Battery 2) - only for 3-phase
                self._set_register(port_base + 10, 0)  # DCA - initialized to 0
                self._set_register(port_base + 11, 0)  # DCV - initialized to 0
                self._set_register(port_base + 12, 0)  # DCW - initialized to 0
                self._set_register(port_base + 21, 0)  # Tmp - initialized to 0
                self._set_register(port_base + 22, 0)  # DCSta - OFF
            else:
                self._set_register(port_base + 10, 0)  # DCA
                self._set_register(port_base + 11, 0)  # DCV
                self._set_register(port_base + 12, 0)  # DCW
                self._set_register(port_base + 21, 0)  # Tmp
                self._set_register(port_base + 22, 0)  # DCSta - OFF
            
            # Initialize energy registers (64-bit values)
            for j in range(4):
                if i == 3:  # Port 4 - uninitialized
                    self._set_register(port_base + 13 + j, 0xFFFF)  # DCWhInj
                    self._set_register(port_base + 17 + j, 0xFFFF)  # DCWhAbs
                else:
                    self._set_register(port_base + 13 + j, 0)  # DCWhInj
                    self._set_register(port_base + 17 + j, 0)  # DCWhAbs
            
            # Initialize alarm register (32-bit)
            if i == 3:  # Port 4 - uninitialized
                self._set_register_32bit(port_base + 23, 0xFFFFFFFF)  # DCAlrm
            else:
                self._set_register_32bit(port_base + 23, 0)  # DCAlrm
        
        # End-of-map marker (Model ID 65535, Length 0) - calculated dynamically
        end_model_id, end_model_length = SunSpecRegisterMap.get_end_model_registers(self.dc_model.num_ports)
        self._set_register(end_model_id, 65535)  # 0xFFFF
        self._set_register(end_model_length, 0)
    
    def _initialize_dc_model_registers(self):
        """Re-initialize DC model registers when port configuration changes"""
        # DC Model (714) header
        self._set_register(SunSpecRegisterMap.DC_MODEL_ID, self.dc_model.model_id)
        self._set_register(SunSpecRegisterMap.DC_MODEL_LENGTH, self.dc_model.model_length)
        
        # Initialize DC model general registers
        self._set_register_32bit(SunSpecRegisterMap.DC_PORT_ALARMS, 0)  # No port alarms initially
        self._set_register(SunSpecRegisterMap.DC_NUM_PORTS, self.dc_model.num_ports)
        self._set_register(SunSpecRegisterMap.DC_TOTAL_CURRENT, 0)  # Will be updated with real data
        self._set_register(SunSpecRegisterMap.DC_TOTAL_POWER, 0)  # Will be updated with real data
        
        # Initialize total energy registers (64-bit values)
        for i in range(4):
            self._set_register(SunSpecRegisterMap.DC_TOTAL_ENERGY_INJ + i, 0)
            self._set_register(SunSpecRegisterMap.DC_TOTAL_ENERGY_ABS + i, 0)
        
        # Set scale factors for DC model
        self._set_register(SunSpecRegisterMap.DC_CURRENT_SF, self.dc_model.current_sf)
        self._set_register(SunSpecRegisterMap.DC_VOLTAGE_SF, self.dc_model.voltage_sf)
        self._set_register(SunSpecRegisterMap.DC_POWER_SF, self.dc_model.power_sf)
        self._set_register(SunSpecRegisterMap.DC_ENERGY_SF, self.dc_model.energy_sf)
        self._set_register(SunSpecRegisterMap.DC_TEMP_SF, self.dc_model.temperature_sf)
        
        # Initialize DC ports dynamically based on actual number of ports
        port_bases = [SunSpecRegisterMap.DC_PORT1_BASE, SunSpecRegisterMap.DC_PORT2_BASE,
                     SunSpecRegisterMap.DC_PORT3_BASE, SunSpecRegisterMap.DC_PORT4_BASE,
                     SunSpecRegisterMap.DC_PORT5_BASE]
        
        # Add 6th port base only if we have 6 ports (3-phase systems)
        if self.dc_model.num_ports == 6:
            port_bases.append(SunSpecRegisterMap.DC_PORT6_BASE)
        
        for i, port_base in enumerate(port_bases):
            if i >= len(self.dc_model.ports):
                break  # Don't initialize ports that don't exist
                
            port = self.dc_model.ports[i]
            
            # Port type and ID
            self._set_register(port_base + 0, port.port_type)  # PrtTyp
            self._set_register(port_base + 1, port.port_id)    # ID
            
            # Port ID string (8 registers)
            self._set_string_registers(port_base + 2, port.port_id_string, 8)
            
            # Initialize port measurements (will be updated with real data)
            if i == 3:  # Port 4 (PV4) - set as uninitialized
                self._set_register(port_base + 10, 0xFFFF)  # DCA - uninitialized
                self._set_register(port_base + 11, 0xFFFF)  # DCV - uninitialized
                self._set_register(port_base + 12, 0xFFFF)  # DCW - uninitialized
                self._set_register(port_base + 21, 0x8000)  # Tmp - uninitialized (signed)
                self._set_register(port_base + 22, 0xFFFF)  # DCSta - uninitialized
            elif i == 5 and self.dc_model.num_ports == 6:  # Port 6 (Battery 2) - only for 3-phase
                self._set_register(port_base + 10, 0)  # DCA - initialized to 0
                self._set_register(port_base + 11, 0)  # DCV - initialized to 0
                self._set_register(port_base + 12, 0)  # DCW - initialized to 0
                self._set_register(port_base + 21, 0)  # Tmp - initialized to 0
                self._set_register(port_base + 22, 0)  # DCSta - OFF
            else:
                self._set_register(port_base + 10, 0)  # DCA
                self._set_register(port_base + 11, 0)  # DCV
                self._set_register(port_base + 12, 0)  # DCW
                self._set_register(port_base + 21, 0)  # Tmp
                self._set_register(port_base + 22, 0)  # DCSta - OFF
            
            # Initialize energy registers (64-bit values)
            for j in range(4):
                if i == 3:  # Port 4 - uninitialized
                    self._set_register(port_base + 13 + j, 0xFFFF)  # DCWhInj
                    self._set_register(port_base + 17 + j, 0xFFFF)  # DCWhAbs
                else:
                    self._set_register(port_base + 13 + j, 0)  # DCWhInj
                    self._set_register(port_base + 17 + j, 0)  # DCWhAbs
            
            # Initialize alarm register (32-bit)
            if i == 3:  # Port 4 - uninitialized
                self._set_register_32bit(port_base + 23, 0xFFFFFFFF)  # DCAlrm
            else:
                self._set_register_32bit(port_base + 23, 0)  # DCAlrm
        
        # Update end-of-map marker with new port configuration
        end_model_id, end_model_length = SunSpecRegisterMap.get_end_model_registers(self.dc_model.num_ports)
        self._set_register(end_model_id, 65535)  # 0xFFFF
        self._set_register(end_model_length, 0)
    
    def _set_register(self, address, value):
        """Set a single register value with validation"""
        if not isinstance(address, int) or address < 0:
            raise ValueError(f"Invalid register address: {address}")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid register value type: {type(value)}")
        
        # Ensure value fits in 16-bit register
        self.registers[address] = int(value) & 0xFFFF
    
    def _set_signed_registers_to_null(self, base_address, offsets):
        """
        Set multiple signed registers to NULL_INT16 value in bulk
        
        Args:
            base_address: Base register address
            offsets: List of register offsets from base address
        """
        try:
            for offset in offsets:
                register_addr = base_address + offset
                self._set_register(register_addr, self.NULL_INT16)
                
                # Log register initialization for debugging
                description = self.REGISTER_DESCRIPTIONS.get(offset, f"Register {offset}")
                self.logger.debug(f"Initialized {description} at address {register_addr} to NULL_INT16")
                
        except Exception as e:
            self.logger.error(f"Error setting signed registers to null: {e}")
            raise
    
    def _set_registers_bulk(self, register_map):
        """
        Set multiple registers from a dictionary mapping
        
        Args:
            register_map: Dictionary of {address: value} pairs
        """
        try:
            for address, value in register_map.items():
                self._set_register(address, value)
        except Exception as e:
            self.logger.error(f"Error in bulk register setting: {e}")
            raise
    
    def _validate_register_range(self, base_address, offsets, model_length):
        """
        Validate that register offsets are within model bounds
        
        Args:
            base_address: Base register address
            offsets: List of register offsets
            model_length: Maximum model length
        """
        for offset in offsets:
            if offset >= model_length:
                raise ValueError(f"Register offset {offset} exceeds model length {model_length}")
    
    def _set_register_32bit(self, address, value):
        """Set a 32-bit value across two registers"""
        self.registers[address] = (value >> 16) & 0xFFFF
        self.registers[address + 1] = value & 0xFFFF
    
    def _set_string_registers(self, start_address, text, num_registers):
        """Set string value across multiple registers"""
        # Pad or truncate string to fit in registers
        text = text.ljust(num_registers * 2)[:num_registers * 2]
        
        for i in range(num_registers):
            char1 = ord(text[i * 2]) if i * 2 < len(text) else 0
            char2 = ord(text[i * 2 + 1]) if i * 2 + 1 < len(text) else 0
            value = (char1 << 8) | char2
            self.registers[start_address + i] = value
    
    def _scale_value(self, value, scale_factor):
        """Apply SunSpec scaling factor to a value"""
        if scale_factor >= 0:
            return int(value * (10 ** scale_factor))
        else:
            return int(value / (10 ** abs(scale_factor)))
    
    def update_from_inverter(self, inverter_data):
        """Update SunSpec models with inverter data (supports both split-phase and 3-phase)"""
        try:
            phase_count = inverter_data.get_phase_count()

            #Log the interpreted phase type as read from the inverter registers
            self.logger.debug(f"Inverter reported phase type: {phase_count}")
            
            # Configure DC model ports based on actual inverter phase count
            if self.dc_model.num_ports != (6 if phase_count == 3 else 5):
                self.dc_model.configure_ports_for_inverter_type(phase_count)
                # Re-initialize DC model registers with new port configuration
                self._initialize_dc_model_registers()
            
            # Update Grid model with grid-side measurements
            if phase_count == 2:
                # Split-phase calculations
                self.grid_model.ac_current = abs(inverter_data.grid_current_l1 + inverter_data.grid_current_l2)
                self.grid_model.ac_current_a = inverter_data.grid_current_l1
                self.grid_model.ac_current_b = inverter_data.grid_current_l2
            elif phase_count == 3:
                # 3-phase calculations
                self.grid_model.ac_current = abs(inverter_data.grid_current_l1 + inverter_data.grid_current_l2 +
                                                getattr(inverter_data, 'grid_current_l3', 0))
                self.grid_model.ac_current_a = inverter_data.grid_current_l1
                self.grid_model.ac_current_b = inverter_data.grid_current_l2
                # For 3-phase, we'll use the existing fields and add L3 in register updates
            
            self.grid_model.ac_voltage_ab = inverter_data.grid_voltage_l1l2
            self.grid_model.ac_power = inverter_data.grid_power
            self.grid_model.ac_frequency = inverter_data.grid_frequency
            self.grid_model.ac_energy = inverter_data.grid_sell_energy * 1000  # Convert kWh to Wh
            
            # Update Load model with load-side measurements
            if phase_count == 2:
                # Split-phase calculations
                self.load_model.ac_current = abs(inverter_data.load_current_l1 + inverter_data.load_current_l2)
                self.load_model.ac_current_a = inverter_data.load_current_l1
                self.load_model.ac_current_b = inverter_data.load_current_l2
            elif phase_count == 3:
                # 3-phase calculations
                self.load_model.ac_current = abs(inverter_data.load_current_l1 + inverter_data.load_current_l2 +
                                                getattr(inverter_data, 'load_current_l3', 0))
                self.load_model.ac_current_a = inverter_data.load_current_l1
                self.load_model.ac_current_b = inverter_data.load_current_l2
            
            self.load_model.ac_voltage_ab = inverter_data.inverter_voltage  # Load voltage from inverter side
            self.load_model.ac_power = inverter_data.load_power_total
            self.load_model.ac_frequency = inverter_data.load_frequency
            self.load_model.ac_energy = inverter_data.load_energy * 1000  # Convert kWh to Wh
            
            # DC measurements (battery side) - shared between models
            dc_current = abs(inverter_data.battery_current)
            dc_voltage = inverter_data.battery_voltage
            dc_power = abs(inverter_data.battery_power)
            
            self.grid_model.dc_current = dc_current
            self.grid_model.dc_voltage = dc_voltage
            self.grid_model.dc_power = dc_power
            
            self.load_model.dc_current = dc_current
            self.load_model.dc_voltage = dc_voltage
            self.load_model.dc_power = dc_power
            
            # Operating state mapping - shared between models
            operating_state = self._map_inverter_state(inverter_data.inverter_status)
            vendor_state = self._map_vendor_state(inverter_data)
            
            self.grid_model.operating_state = operating_state
            self.grid_model.vendor_operating_state = vendor_state
            self.load_model.operating_state = operating_state
            self.load_model.vendor_operating_state = vendor_state
            
            # Update battery model with Model 713 and 714 data
            # Use Model 714 battery fields if available, otherwise fallback to legacy fields
            if hasattr(inverter_data, 'battery_1_voltage'):
                self.battery_model.battery_voltage = inverter_data.battery_1_voltage
            else:
                self.battery_model.battery_voltage = getattr(inverter_data, 'battery_voltage', 0.0)
            
            if hasattr(inverter_data, 'battery_1_current'):
                self.battery_model.battery_current = inverter_data.battery_1_current
            else:
                self.battery_model.battery_current = getattr(inverter_data, 'battery_current', 0.0)
            
            if hasattr(inverter_data, 'battery_1_power'):
                self.battery_model.battery_power = inverter_data.battery_1_power
            else:
                self.battery_model.battery_power = getattr(inverter_data, 'battery_power', 0.0)
            
            self.battery_model.battery_soc = getattr(inverter_data, 'battery_soc', 0.0)
            self.battery_model.battery_temperature = getattr(inverter_data, 'battery_temperature', 0.0)
            self.battery_model.battery_capacity = getattr(inverter_data, 'battery_capacity', 0.0)
            
            # Model 713 specific fields from CSV mapping
            self.battery_model.battery_calculated_capacity = getattr(inverter_data, 'battery_calculated_capacity', 0.0)
            self.battery_model.battery_soc_713 = getattr(inverter_data, 'battery_soc_713', 0.0)
            self.battery_model.battery_soh = getattr(inverter_data, 'battery_soh', 100.0)
            
            # Calculate energy capacity using Model 713 data (register 592 * actual measured voltage)
            capacity_ah = self.battery_model.battery_calculated_capacity if self.battery_model.battery_calculated_capacity > 0 else self.battery_model.battery_capacity
            # Use Model 714 battery voltage if available (register 587), otherwise use legacy voltage
            voltage = getattr(inverter_data, 'battery_1_voltage', self.battery_model.battery_voltage)
            if voltage <= 0:
                voltage = 51.2  # Fallback to nominal voltage if no measurement available
            self.battery_model.battery_energy_capacity = capacity_ah * voltage
            self.logger.debug(f"Battery Energy Capacity - Capacity: {capacity_ah}Ah, Voltage: {voltage:.1f}V, Energy: {self.battery_model.battery_energy_capacity:.0f}Wh")
            
            self.battery_model.battery_status = self._map_storage_status(inverter_data)
            
            # Update Modbus registers for both models
            self.update_grid_registers_from_inverter(inverter_data)
            self.update_load_registers_from_inverter(inverter_data)
            self._update_battery_registers(inverter_data)
            self._update_dc_model_from_inverter(inverter_data)
            
            self.logger.debug(f"Updated SunSpec Grid, Load, and DC models with {inverter_data.get_inverter_type()} data")
            
        except Exception as e:
            self.logger.error(f"Error updating SunSpec models: {e}")
    
    def _map_inverter_state(self, inverter_status):
        """Map Sol-Ark inverter status to SunSpec operating state"""
        # Sol-Ark: 1=Self-test, 2=Normal, 3=Alarm, 4=Fault
        # SunSpec: 1=Off, 2=Sleeping, 4=Starting, 8=MPPT, 16=Throttled, 32=Shutting Down, 64=Fault, 128=Standby
        
        if inverter_status == 1:  # Self-test
            return 4  # Starting
        elif inverter_status == 2:  # Normal
            return 8  # MPPT
        elif inverter_status == 3:  # Alarm
            return 16  # Throttled
        elif inverter_status == 4:  # Fault
            return 64  # Fault
        else:
            return 0  # Off
    
    def _map_vendor_state(self, inverter_data):
        """Map inverter data to vendor-specific state bits"""
        state = 0
        
        if inverter_data.grid_relay_status > 0:
            state |= 0x0001  # Grid connected
        
        if inverter_data.generator_relay_status > 0:
            state |= 0x0002  # Generator connected
        
        if inverter_data.battery_power < 0:
            state |= 0x0004  # Battery charging
        
        if inverter_data.battery_power > 0:
            state |= 0x0008  # Battery discharging
        
        if inverter_data.grid_power < 0:
            state |= 0x0010  # Selling to grid
        
        if inverter_data.grid_power > 0:
            state |= 0x0020  # Buying from grid
        
        return state
    
    def _map_storage_status(self, inverter_data):
        """Map inverter BMS data to SunSpec storage status """
        # SunSpec Storage Status enumeration:
        # 0 = OK
        # 1 = Warning
        # 2 = Error/Fault
        
        if inverter_data.bms_fault > 0:
            return 2  # Error
        elif inverter_data.bms_warning > 0:
            return 1  # Warning
        else:
            return 0  # OK
    

    ###############################################
    # Grid Model (701) header - First instance
    ###############################################    
    def update_grid_registers_from_inverter(self, inverter_data):
        """Update grid registers from inverter data (supports both split-phase and 3-phase)"""
        self._update_grid_registers_common(inverter_data)
    
    def _update_grid_registers_common(self, inverter_data):
        # Determine phase count and AC wiring type
        phase_count = inverter_data.get_phase_count()

        # Set AC wiring type based on phase count and grid type from CSV mapping
        # SunSpec Type enumeration:
        # 0 = SINGLE_PHASE
        # 1 = SPLIT_PHASE
        # 2 = THREE_PHASE
        
        # Sol-Ark LV enumeration:
        # 000 = # Single phase 240V - 230V - 220V
        # 001 = # Two Phase (Split-Phase) 120/240
        # 002 = # Three phase 120/208V
        
        # Sol-Ark HV enumeration:
        # 000 = # Three phase
        # 001 = # Single phase 240V - 230V - 220V
        # 002 = # Two Phase (Split-Phase) 120/240
        sunspec_ac_type = 0  # Default to Single Phase

        # Conditional logic required becuase the 3 phase modbus map inverts the logic vs the split-phase modbus map
        
        if phase_count == 2: #LV Inverter
            # Use grid type from register 184 Grid Type
            if hasattr(inverter_data, 'grid_type'):
                self.logger.debug(f"LV | Grid type read from inverter: 0x{inverter_data.grid_type:04X}")
                if inverter_data.grid_type == 0x0000:
                    sunspec_ac_type = 0 # SINGLE_PHASE
                elif inverter_data.grid_type == 0x0001:
                    sunspec_ac_type = 1 # SPLIT_PHASE
                elif inverter_data.grid_type == 0x0002:
                    sunspec_ac_type = 2 #THREE_PHASE
        
        elif phase_count == 3: #HV Inverter
            # Use grid type from register 184 Grid Type
            if hasattr(inverter_data, 'grid_type'):
                self.logger.debug(f"HV 3P | Grid type read from inverter: 0x{inverter_data.grid_type:04X}")
                if inverter_data.grid_type == 0x0000:  # Three Phase (default)
                    sunspec_ac_type = 2  # Three Phase
                elif inverter_data.grid_type == 0x0001:  # Single Phase
                    sunspec_ac_type = 0  # Single Phase
                elif inverter_data.grid_type == 0x0002:  # Split Phase
                    sunspec_ac_type = 1  # Split Phase
            else:
                sunspec_ac_type = 2  # Default to Three Phase for 3-phase systems
        
        # SunSpec AC Wiring Type - Offset (2)
        self._set_register(SunSpecRegisterMap.GRID_AC_TYPE, sunspec_ac_type)
        
        # SunSpec Operating State - Offset (3) - from CSV register 551 (Power Button Status)
        operating_state = 1  # Default to ON
        if hasattr(inverter_data, 'power_button_status'):
            self.logger.debug(f"Power Button status from inverter: 0x{inverter_data.power_button_status:04X}")
            operating_state = 1 if inverter_data.power_button_status == 1 else 0

        self._set_register(SunSpecRegisterMap.GRID_OPERATING_STATE, operating_state)
        
        # Inverter state mapping from CSV register 500 (Operation Status)
        inv_state = 0  # Default to O
        if inverter_data.inverter_status == 0:  # Standby
            inv_state = 7  # STANDBY
        elif inverter_data.inverter_status == 1:  # Self-test
            inv_state = 2  # STARTING
        elif inverter_data.inverter_status == 2:  # Normal
            if inverter_data.grid_power > 100:
                inv_state = 3  # RUNNING
            else:
                inv_state = 7  # STANDBY
        elif inverter_data.inverter_status == 3:  # Alarm
            inv_state = 4  # THROTTLED
        elif inverter_data.inverter_status == 4:  # Fault
            inv_state = 6  # FAULT
        elif inverter_data.inverter_status == 5:  # Activating
            inv_state = 2  # STARTING
        else:
            inv_state = 0  # OFF
        
        # SunSpec Inverter State - Offset (4)
        self._set_register(SunSpecRegisterMap.GRID_STATUS, inv_state)
        
        # SunSpec Grid Connection State - Offset (5) - Different registers for LV vs HV inverters
        grid_connected = 0  # Default to DISCONNECTED
        
        # Check inverter type to determine which register to use
        inverter_type_str = getattr(inverter_data, 'get_inverter_type', lambda: self.inverter_type)()
        
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # LV Inverter (Single/Split-phase) - Use register 194 (Grid side relay status)
            # Direct value: 0=Open(Disconnect), 1=Closed(Connected)
            if hasattr(inverter_data, 'grid_side_relay_status'):
                grid_connected = 1 if inverter_data.grid_side_relay_status == 1 else 0
        else:
            # HV Inverter (3-phase) - Use register 552 (AC Relay Status)
            # Bit 2: Grid relay (0: off 1: on)
            if hasattr(inverter_data, 'grid_relay_status'):
                grid_connected = 1 if (inverter_data.grid_relay_status & 0x04) != 0 else 0
        self._set_register(SunSpecRegisterMap.GRID_CONNECTION, grid_connected)
        
        # DER operational characteristics
        der_mode = 0
        if grid_connected == 1:  # Connected to grid
            der_mode |= 0x0000  # Grid Following
        else:  # Disconnected from grid
            der_mode |= 0x0001  # Grid Forming
        
        # SunSpec DER Mode - Offset (8-9) - 32-bit bitfield
        self._set_register(SunSpecRegisterMap.GRID_DER_MODE, (der_mode >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.GRID_DER_MODE + 1, der_mode & 0xFFFF)
        
        # Alarm bitfield - Offset (6-7) - 32-bit bitfield
        self._set_register(SunSpecRegisterMap.GRID_ALARM, 0)
        self._set_register(SunSpecRegisterMap.GRID_ALARM + 1, 0)
        
        # Power measurements - Different registers for LV vs HV inverters
        # Check inverter type to determine which registers to use
        inverter_type_str = getattr(inverter_data, 'get_inverter_type', lambda: self.inverter_type)()
        
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # LV Inverter (Single/Split-phase)
            # Total Active Power - Offset (10) - from register 169 (Total power of grid side L1L2)
            self._set_register(SunSpecRegisterMap.GRID_AC_POWER, int(getattr(inverter_data, 'grid_power_total_l1l2', inverter_data.grid_power)))
            
            # Apparent Power (VA) - Offset (11) - from register 38 (Apparent Power reading)
            self._set_register(SunSpecRegisterMap.GRID_AC_VA, int(getattr(inverter_data, 'apparent_power_lv', inverter_data.apparent_power)))
            
            # Power Factor (PF) - Offset (13) - from register 89 (Grid Real Power Factor)
            self._set_register(SunSpecRegisterMap.GRID_AC_PF, int(getattr(inverter_data, 'grid_real_power_factor', inverter_data.grid_power_factor) * 100))
            
            # Reactive Power (VAR) - Offset (12) - calculated from sqrt(VA^2 - W^2)
            try:
                va_squared = getattr(inverter_data, 'apparent_power_lv', inverter_data.apparent_power) ** 2
                w_squared = getattr(inverter_data, 'grid_power_total_l1l2', inverter_data.grid_power) ** 2
                if va_squared >= w_squared:
                    reactive_power = int((va_squared - w_squared) ** 0.5)
                    if getattr(inverter_data, 'grid_real_power_factor', inverter_data.grid_power_factor) < 0:
                        reactive_power = -reactive_power
                else:
                    reactive_power = 0
            except (ValueError, ZeroDivisionError):
                reactive_power = 0
            self._set_register(SunSpecRegisterMap.GRID_AC_VAR, reactive_power)
            
        else:
            # HV Inverter (3-phase)
            # Total Active Power - Offset (10) - from registers 625/690 (32-bit)
            self._set_register(SunSpecRegisterMap.GRID_AC_POWER, int(inverter_data.grid_power))
            
            # Apparent Power (VA) - Offset (11) - from registers 608/704 (32-bit)
            self._set_register(SunSpecRegisterMap.GRID_AC_VA, int(inverter_data.apparent_power))
            
            # Power Factor (PF) - Offset (13) - from register 621 (Grid Power Factor)
            self._set_register(SunSpecRegisterMap.GRID_AC_PF, int(inverter_data.grid_power_factor * 100))
            
            # Reactive Power (VAR) - Offset (12) - from registers 710-712 (sum of L1, L2, L3)
            if hasattr(inverter_data, 'grid_reactive_power_total'):
                reactive_power = int(inverter_data.grid_reactive_power_total)
            else:
                # Fallback calculation if reactive power not available
                try:
                    va_squared = inverter_data.apparent_power ** 2
                    w_squared = inverter_data.grid_power ** 2
                    if va_squared >= w_squared:
                        reactive_power = int((va_squared - w_squared) ** 0.5)
                        if inverter_data.grid_power_factor < 0:
                            reactive_power = -reactive_power
                    else:
                        reactive_power = 0
                except (ValueError, ZeroDivisionError):
                    reactive_power = 0
            self._set_register(SunSpecRegisterMap.GRID_AC_VAR, reactive_power)
        
        # Current and voltage measurements - from CSV mapping
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # Split-phase calculations
            grid_current_total = abs(inverter_data.grid_current_l1 + inverter_data.grid_current_l2)
        else:
            # 3-phase calculations - from registers 610-612
            grid_current_total = abs(inverter_data.grid_current_l1 + inverter_data.grid_current_l2 + getattr(inverter_data, 'grid_current_l3', 0))
    
        # Total AC Current - Offset (14)
        self._set_register(SunSpecRegisterMap.GRID_AC_CURRENT, int(grid_current_total * 100))  # Scale by 100
        
        # Voltage LL - Offset (15) - Line-to-Line voltage (calculated from L-N * sqrt(3))
        self._set_register(SunSpecRegisterMap.GRID_AC_VOLTAGE_LL, int(inverter_data.grid_voltage_l1l2 * 10))
        
        # Voltage LN - Offset (16) - Line-to-Neutral voltage from register 598
        self._set_register(SunSpecRegisterMap.GRID_AC_VOLTAGE_LN, int(inverter_data.grid_voltage_l1n * 10))
        
        # Frequency - Offset (17-18) - 32-bit from CSV register 609
        frequency_scaled = int(inverter_data.grid_frequency * 100)
        self._set_register(SunSpecRegisterMap.GRID_AC_FREQUENCY, (frequency_scaled >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.GRID_AC_FREQUENCY + 1, frequency_scaled & 0xFFFF)
        
        # Energy measurements - placeholder (marked as UNIMPLEMENTED in CSV)
        energy_injected_wh = int(getattr(inverter_data, 'grid_sell_energy', 0) * 1000)
        energy_absorbed_wh = int(getattr(inverter_data, 'grid_buy_energy', 0) * 1000)
        
        # Total Energy Injected (TotWhInj) - Offset (19-22) - 4 registers for uint64
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 19, 0)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 20, 0)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 21, (energy_injected_wh >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 22, energy_injected_wh & 0xFFFF)
        
        # Total Energy Absorbed (TotWhAbs) - Offset (23-26) - 4 registers for uint64
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 23, 0)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 24, 0)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 25, (energy_absorbed_wh >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 26, energy_absorbed_wh & 0xFFFF)
        
        # Temperature measurements - from CSV registers 540-541
        # Heat Sink Temperature - Offset (37) - from CSV register 541
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 37, int(inverter_data.dcdc_xfrmr_temp * 10))
        # Transformer Temperature - Offset (38) - set to unimplemented
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 38, self.NULL_INT16)
        # IGBT/MOSFET Temperature - Offset (39) - from CSV register 540
        self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 39, int(inverter_data.igbt_temp * 10))
        
        # Phase-specific measurements using actual register mappings from CSV
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # Split-phase L1 and L2 measurements
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 41, int(inverter_data.grid_power / 2))  # WL1
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 45, int(inverter_data.grid_current_l1 * 100))  # AL1
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 46, int(inverter_data.grid_voltage_l1l2 * 10))  # VL1L2
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 47, int(inverter_data.grid_voltage_l1n * 10))  # VL1
            
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 64, int(inverter_data.grid_power / 2))  # WL2
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 68, int(inverter_data.grid_current_l2 * 100))  # AL2
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 70, int(inverter_data.grid_voltage_l2n * 10))  # VL2
        
        else:
            # 3-phase L1, L2, and L3 measurements using actual power values from CSV
            # WL1 - Offset (41) - from registers 622/687 (32-bit)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 41, int(getattr(inverter_data, 'grid_power_l1', inverter_data.grid_power / 3)))
            # VarL1 - Offset (43) - from register 710
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 43, int(getattr(inverter_data, 'grid_reactive_power_l1', 0)))
            # AL1 - Offset (45) - from register 610
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 45, int(inverter_data.grid_current_l1 * 100))
            # VL1L2 - Offset (46) - calculated from register 598 * sqrt(3)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 46, int(inverter_data.grid_voltage_l1l2 * 10))
            # VL1 - Offset (47) - from register 598
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 47, int(inverter_data.grid_voltage_l1n * 10))
            
            # WL2 - Offset (64) - from registers 623/688 (32-bit)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 64, int(getattr(inverter_data, 'grid_power_l2', inverter_data.grid_power / 3)))
            # VarL2 - Offset (66) - from register 711
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 66, int(getattr(inverter_data, 'grid_reactive_power_l2', 0)))
            # AL2 - Offset (68) - from register 611
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 68, int(inverter_data.grid_current_l2 * 100))
            # VL2L3 - Offset (69) - calculated from register 599 * sqrt(3)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 69, int(getattr(inverter_data, 'grid_voltage_l2l3', 0) * 10))
            # VL2 - Offset (70) - from register 599
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 70, int(getattr(inverter_data, 'grid_voltage_l2n', 0) * 10))
            
            # WL3 - Offset (87) - from registers 624/689 (32-bit)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 87, int(getattr(inverter_data, 'grid_power_l3', inverter_data.grid_power / 3)))
            # VarL3 - Offset (89) - from register 712
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 89, int(getattr(inverter_data, 'grid_reactive_power_l3', 0)))
            # AL3 - Offset (91) - from register 612
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 91, int(getattr(inverter_data, 'grid_current_l3', 0) * 100))
            # VL3L1 - Offset (92) - calculated from register 600 * sqrt(3)
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 92, int(getattr(inverter_data, 'grid_voltage_l3l1', 0) * 10))
            # VL3 - Offset (93) - from register 600
            self._set_register(SunSpecRegisterMap.GRID_MODEL_BASE + 93, int(getattr(inverter_data, 'grid_voltage_l3n', 0) * 10))
        
        # Vendor-specific status information - Offset (123-154) - 32 registers for string
        if phase_count == 3:
            alarm_info = alarm_info = f"Grid Port Model"
        else:
            alarm_info = f"Grid Port Model"
        self._set_string_registers(SunSpecRegisterMap.GRID_MODEL_BASE + 123, alarm_info, 32)
    
    
    ###############################################
    # Load Model (701) header - Second instance
    ###############################################
    def update_load_registers_from_inverter(self, inverter_data):
        """Update load registers from inverter data (supports both split-phase and 3-phase)"""
        self._update_load_registers_common(inverter_data)
    
    def _update_load_registers_common(self, inverter_data):
        # Determine phase count and AC wiring type
        phase_count = inverter_data.get_phase_count()

        # Set AC wiring type based on phase count and grid type from CSV mapping
        # SunSpec Type enumeration:
        # 0 = SINGLE_PHASE
        # 1 = SPLIT_PHASE
        # 2 = THREE_PHASE
        
        # Sol-Ark LV enumeration:
        # 000 = # Single phase 240V - 230V - 220V
        # 001 = # Two Phase (Split-Phase) 120/240
        # 002 = # Three phase 120/208V
        
        # Sol-Ark HV enumeration:
        # 000 = # Three phase
        # 001 = # Single phase 240V - 230V - 220V
        # 002 = # Two Phase (Split-Phase) 120/240
        sunspec_ac_type = 0  # Default to Single Phase

        # Conditional logic required becuase the 3 phase modbus map inverts the logic vs the split-phase modbus map
        
        if phase_count == 2: #LV Inverter
            # Use grid type from register 184 Grid Type
            if hasattr(inverter_data, 'grid_type'):
                self.logger.debug(f"LV | Grid type read from inverter: 0x{inverter_data.grid_type:04X}")
                if inverter_data.grid_type == 0x0000:
                    sunspec_ac_type = 0 # SINGLE_PHASE
                elif inverter_data.grid_type == 0x0001:
                    sunspec_ac_type = 1 # SPLIT_PHASE
                elif inverter_data.grid_type == 0x0002:
                    sunspec_ac_type = 2 #THREE_PHASE
        
        elif phase_count == 3: #HV Inverter
            # Use grid type from register 184 Grid Type
            if hasattr(inverter_data, 'grid_type'):
                self.logger.debug(f"HV 3P | Grid type read from inverter: 0x{inverter_data.grid_type:04X}")
                if inverter_data.grid_type == 0x0000:  # Three Phase (default)
                    sunspec_ac_type = 2  # Three Phase
                elif inverter_data.grid_type == 0x0001:  # Single Phase
                    sunspec_ac_type = 0  # Single Phase
                elif inverter_data.grid_type == 0x0002:  # Split Phase
                    sunspec_ac_type = 1  # Split Phase
            else:
                sunspec_ac_type = 2  # Default to Three Phase for 3-phase systems
        
        self._set_register(SunSpecRegisterMap.LOAD_AC_TYPE, sunspec_ac_type)
        
        # Operating state based on inverter status
        self._set_register(SunSpecRegisterMap.LOAD_OPERATING_STATE, 0xFFFF)
        
        self._set_register(SunSpecRegisterMap.LOAD_STATUS, 0xFFFF)
        
        # Grid connection state - same as Grid model
        self._set_register(SunSpecRegisterMap.LOAD_CONNECTION, 0xFFFF)
        
        # DER operational characteristics - same as Grid model
        der_mode = 0
        if inverter_data.grid_relay_status == 1:  # Connected to grid
            der_mode |= 0x0000  # Grid Following
        else:  # Disconnected from grid
            der_mode |= 0x0001  # Grid Forming
        
        self._set_register(SunSpecRegisterMap.LOAD_DER_MODE, (der_mode >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.LOAD_DER_MODE + 1, der_mode & 0xFFFF)
        
        # Alarm bitfield
        self._set_register(SunSpecRegisterMap.LOAD_ALARM, 0)
        self._set_register(SunSpecRegisterMap.LOAD_ALARM + 1, 0)
        
        # Power measurements
        self._set_register(SunSpecRegisterMap.LOAD_AC_POWER, int(inverter_data.load_power_total))
        
        # Apparent Power (VA)
        self._set_register(SunSpecRegisterMap.LOAD_AC_VA, int(inverter_data.apparent_power))
        
        # Reactive Power (VAR) - calculated as sqrt(VA^2 - W^2)
        try:
            va_squared = inverter_data.apparent_power ** 2
            w_squared = inverter_data.load_power_total ** 2
            if va_squared >= w_squared:
                reactive_power = int((va_squared - w_squared) ** 0.5)
                # For load side, assume lagging power factor (positive VAR)
                # since load typically consumes reactive power
            else:
                reactive_power = 0  # Avoid negative square root
            self._set_register(SunSpecRegisterMap.LOAD_AC_VAR, reactive_power)
        except (ValueError, ZeroDivisionError):
            self._set_register(SunSpecRegisterMap.LOAD_AC_VAR, 0)
        
        # Power Factor (PF) - Load side power factor often not implemented
        self._set_register(SunSpecRegisterMap.LOAD_AC_PF, self.NULL_INT16)  # Not implemented
        
        # Get inverter type string for phase-specific logic
        inverter_type_str = getattr(inverter_data, 'get_inverter_type', lambda: self.inverter_type)()
        
        # Current and voltage measurements
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # Split-phase calculations
            load_current_total = abs(inverter_data.load_current_l1 + inverter_data.load_current_l2)
        else:
            # 3-phase calculations
            load_current_total = abs(inverter_data.load_current_l1 + inverter_data.load_current_l2 +
                                   getattr(inverter_data, 'load_current_l3', 0))
        
        self._set_register(SunSpecRegisterMap.LOAD_AC_CURRENT, int(load_current_total * 100))  # Scale by 100
        
        # Voltage measurements - different for 3-phase vs split-phase
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # Split-phase: use inverter voltage as approximation for load voltage
            self._set_register(SunSpecRegisterMap.LOAD_AC_VOLTAGE_LL, int(inverter_data.inverter_voltage * 10))
            self._set_register(SunSpecRegisterMap.LOAD_AC_VOLTAGE_LN, int(getattr(inverter_data, 'inverter_voltage_ln', 0) * 10))
        else:
            # 3-phase: use actual load voltage from registers 644-646
            load_voltage_l1n = getattr(inverter_data, 'load_voltage_l1n', 0)
            self._set_register(SunSpecRegisterMap.LOAD_AC_VOLTAGE_LL, int(load_voltage_l1n * 1.732 * 10))  # LLV: Load Phase A Voltage * sqrt(3)
            self._set_register(SunSpecRegisterMap.LOAD_AC_VOLTAGE_LN, int(load_voltage_l1n * 10))  # LNV: Load Phase A Voltage (register 644)
            self.logger.debug(f"SunSpec Load LLV/LNV - L1N: {load_voltage_l1n:.1f}V, LLV: {int(load_voltage_l1n * 1.732 * 10)}, LNV: {int(load_voltage_l1n * 10)}")
        
        # Frequency
        frequency_scaled = int(inverter_data.load_frequency * 100)
        self._set_register(SunSpecRegisterMap.LOAD_AC_FREQUENCY, (frequency_scaled >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.LOAD_AC_FREQUENCY + 1, frequency_scaled & 0xFFFF)
        
        # Energy measurements
        energy_injected_wh = int(inverter_data.load_energy * 1000)  # Convert kWh to Wh
        
        # Total Energy Injected (TotWhInj) - 4 registers for uint64
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 19, 0)  # High 32 bits (upper 16)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 20, 0)  # High 32 bits (lower 16)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 21, (energy_injected_wh >> 16) & 0xFFFF)
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 22, energy_injected_wh & 0xFFFF)
        
        # Temperature measurements - shared with Grid model
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 37, int(inverter_data.igbt_temp * 10))  # Heat Sink temp
        self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 38, int(inverter_data.dcdc_xfrmr_temp * 10))  # Transformer temp
        
        # Phase-specific measurements
        if 'split_phase' in inverter_type_str.lower() or 'single' in inverter_type_str.lower():
            # Split-phase L1 and L2 measurements
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 41, int(inverter_data.load_power_l1))  # WL1: Load L1 power
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 45, int(inverter_data.load_current_l1 * 100))  # Current L1
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 46, int(inverter_data.inverter_voltage * 10))  # VL1L2: Load voltage
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 47, int(getattr(inverter_data, 'inverter_voltage_ln', 0) * 10))  # VL1: Load voltage L1
            
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 64, int(inverter_data.load_power_l2))  # WL2: Load L2 power
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 68, int(inverter_data.load_current_l2 * 100))  # Current L2
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 70, int(getattr(inverter_data, 'inverter_voltage_l2n', 0) * 10))  # VL2: Load voltage L2
        
        else:
            # 3-phase L1, L2, and L3 measurements
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 41, int(inverter_data.load_power_l1))  # WL1: Load L1 power
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 45, int(inverter_data.load_current_l1 * 100))  # Current L1
            
            # Load voltage measurements from registers 644, 645, 646
            load_voltage_l1n = getattr(inverter_data, 'load_voltage_l1n', 0)
            load_voltage_l2n = getattr(inverter_data, 'load_voltage_l2n', 0)
            load_voltage_l3n = getattr(inverter_data, 'load_voltage_l3n', 0)
            
            self.logger.debug(f"SunSpec Load Voltages - L1N: {load_voltage_l1n:.1f}V, L2N: {load_voltage_l2n:.1f}V, L3N: {load_voltage_l3n:.1f}V")
            
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 46, int(load_voltage_l1n * 1.732 * 10))  # VL1L2: Load voltage L1-L2 (L1N * sqrt(3))
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 47, int(load_voltage_l1n * 10))  # VL1: Load Phase A Voltage (register 644)
            
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 64, int(inverter_data.load_power_l2))  # WL2: Load L2 power
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 68, int(inverter_data.load_current_l2 * 100))  # Current L2
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 70, int(load_voltage_l2n * 10))  # VL2: Load Phase B Voltage (register 645)
            
            # L3 measurements (using L3 registers in SunSpec Model 701)
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 87, int(getattr(inverter_data, 'load_power_l3', 0)))  # WL3: Load L3 power
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 91, int(getattr(inverter_data, 'load_current_l3', 0) * 100))  # Current L3
            self._set_register(SunSpecRegisterMap.LOAD_MODEL_BASE + 89, int(load_voltage_l3n * 10))  # VL3: Load Phase C Voltage (register 646)
            
            self.logger.debug(f"SunSpec Load Register Values - VL1: {int(load_voltage_l1n * 10)}, VL2: {int(load_voltage_l2n * 10)}, VL3: {int(load_voltage_l3n * 10)}")
        
        # Vendor-specific status information
        if phase_count == 3:
            alarm_info = alarm_info = f"Load Port Model"
        else:
            alarm_info = alarm_info = f"Load Port Model"
        self._set_string_registers(SunSpecRegisterMap.LOAD_MODEL_BASE + 123, alarm_info, 32)
    
    
    def _update_battery_registers(self, inverter_data):
        """Update storage model (713) registers using correct Sol-Ark register mappings from CSV"""
        # SunSpec Model 713 implementation based on CSV mapping
        
        # Energy Rating (WHRtg) - from register 592 (Battery 1 Calculated Capacity)
        # CSV notes: "In Ah, battery_capacity_ah * 409.6"
        # Convert Ah to Wh using actual measured DC battery voltage
        if hasattr(self.battery_model, 'battery_calculated_capacity') and self.battery_model.battery_calculated_capacity > 0:
            battery_capacity_ah = self.battery_model.battery_calculated_capacity
        else:
            battery_capacity_ah = self.battery_model.battery_capacity
        
        # Use actual measured DC battery voltage instead of nominal voltage
        # Use Model 714 battery voltage if available (register 587), otherwise use legacy voltage
        actual_voltage = getattr(inverter_data, 'battery_1_voltage', self.battery_model.battery_voltage)
        
        if actual_voltage <= 0:
            actual_voltage = 51.2  # Fallback to nominal voltage if no measurement available
        
        energy_rating = int(battery_capacity_ah * actual_voltage)  # Wh = Ah * V
        self._set_register(SunSpecRegisterMap.STORAGE_ENERGY_RATING, energy_rating)
        self.logger.debug(f"Energy Rating - Capacity: {battery_capacity_ah}Ah, Voltage: {actual_voltage:.1f}V, Rating: {energy_rating}Wh")
        
        # State of Charge (SoC) - from register 588 (Battery 1 SOC)
        if hasattr(self.battery_model, 'battery_soc_713') and self.battery_model.battery_soc_713 > 0:
            soc_percent = self.battery_model.battery_soc_713
        else:
            soc_percent = self.battery_model.battery_soc
        
        # State of Health (SoH) - from register 10006 (Battery SOH)
        if hasattr(self.battery_model, 'battery_soh') and self.battery_model.battery_soh > 0:
            soh_percent = self.battery_model.battery_soh
        else:
            soh_percent = 100.0  # Default to 100% if not available
        
        # Energy Available (WHAvail = WHRtg * SoC * SoH)
        soc_fraction = soc_percent / 100.0
        soh_fraction = soh_percent / 100.0
        energy_available = int(energy_rating * soc_fraction * soh_fraction)
        self._set_register(SunSpecRegisterMap.STORAGE_ENERGY_AVAILABLE, energy_available)
        
        # State of charge (%) - scaled by 10 for 0.1 scale factor
        self._set_register(SunSpecRegisterMap.STORAGE_SOC, int(soc_percent * 10))
        
        # State of health (%) - scaled by 10 for 0.1 scale factor
        self._set_register(SunSpecRegisterMap.STORAGE_SOH, int(soh_percent * 10))
        
        # Storage status - use the corrected enumerated values (0=OK, 1=Warning, 2=Error)
        self._set_register(SunSpecRegisterMap.STORAGE_STATUS, self.battery_model.battery_status)
        
        # Scale factors
        self._set_register(SunSpecRegisterMap.STORAGE_SF_ENERGY, 0)  # Energy scale factor: 0 (1) - values in Wh
        self._set_register(SunSpecRegisterMap.STORAGE_SF_PERCENT, -1)  # Percentage scale factor: -1 (0.1)
    
    def _update_dc_model_from_inverter(self, inverter_data):
        """Update DC model (714) registers with inverter data using correct Model 714 fields"""
        try:
            phase_count = inverter_data.get_phase_count()
            
            # Update DC model data from Model 714 register mappings
            # PV Port 1 - from registers 676 (voltage), 677 (current), 672 (power)
            if hasattr(inverter_data, 'pv1_voltage') and hasattr(inverter_data, 'pv1_current') and hasattr(inverter_data, 'pv1_power'):
                self.dc_model.ports[0].dc_voltage = inverter_data.pv1_voltage
                self.dc_model.ports[0].dc_current = inverter_data.pv1_current
                self.dc_model.ports[0].dc_power = inverter_data.pv1_power
                self.dc_model.ports[0].dc_status = 1 if inverter_data.pv1_power > 10 else 0  # ON if power > 10W
                self.dc_model.ports[0].temperature = getattr(inverter_data, 'igbt_temp', 25.0)
            
            # PV Port 2 - from registers 678 (voltage), 679 (current), 673 (power)
            if hasattr(inverter_data, 'pv2_voltage') and hasattr(inverter_data, 'pv2_current') and hasattr(inverter_data, 'pv2_power'):
                self.dc_model.ports[1].dc_voltage = inverter_data.pv2_voltage
                self.dc_model.ports[1].dc_current = inverter_data.pv2_current
                self.dc_model.ports[1].dc_power = inverter_data.pv2_power
                self.dc_model.ports[1].dc_status = 1 if inverter_data.pv2_power > 10 else 0  # ON if power > 10W
                self.dc_model.ports[1].temperature = getattr(inverter_data, 'igbt_temp', 25.0)
            
            # PV Port 3 - from registers 680 (voltage), 681 (current), 674 (power)
            if hasattr(inverter_data, 'pv3_voltage') and hasattr(inverter_data, 'pv3_current') and hasattr(inverter_data, 'pv3_power'):
                self.dc_model.ports[2].dc_voltage = inverter_data.pv3_voltage
                self.dc_model.ports[2].dc_current = inverter_data.pv3_current
                self.dc_model.ports[2].dc_power = inverter_data.pv3_power
                self.dc_model.ports[2].dc_status = 1 if inverter_data.pv3_power > 10 else 0  # ON if power > 10W
                self.dc_model.ports[2].temperature = getattr(inverter_data, 'igbt_temp', 25.0)
            
            # PV Port 4 - from registers 682 (voltage), 683 (current), 675 (power) - Keep uninitialized
            # No updates for port 4 - it remains uninitialized as requested
            
            # ESS Port 1 - Battery measurements using Model 714 fields
            # Use battery_1_* fields if available (from registers 587, 591, 590), otherwise fallback to legacy fields
            if hasattr(inverter_data, 'battery_1_voltage') and hasattr(inverter_data, 'battery_1_current') and hasattr(inverter_data, 'battery_1_power'):
                # Use Model 714 battery fields (registers 587, 591, 590)
                self.dc_model.ports[4].dc_voltage = inverter_data.battery_1_voltage
                self.dc_model.ports[4].dc_current = inverter_data.battery_1_current
                self.dc_model.ports[4].dc_power = inverter_data.battery_1_power  # No scaling - register 590 is already in watts
                self.logger.debug(f"Battery 1 Power - Raw value: {inverter_data.battery_1_power}W (register 590)")
            else:
                # Fallback to legacy battery fields for backward compatibility
                self.dc_model.ports[4].dc_voltage = getattr(inverter_data, 'battery_voltage', 0.0)
                self.dc_model.ports[4].dc_current = getattr(inverter_data, 'battery_current', 0.0)
                self.dc_model.ports[4].dc_power = getattr(inverter_data, 'battery_power', 0.0)
            
            self.dc_model.ports[4].dc_status = 1 if abs(self.dc_model.ports[4].dc_power) > 10 else 0  # ON if power > 10W
            # Use 3-phase specific battery 1 temperature if available, otherwise fallback to legacy
            self.dc_model.ports[4].temperature = getattr(inverter_data, 'battery_1_temperature', getattr(inverter_data, 'battery_temperature', 25.0))
            
            # ESS Port 2 - Battery 2 measurements (only for 3-phase systems with 6 ports)
            if self.dc_model.num_ports == 6 and len(self.dc_model.ports) > 5:
                if hasattr(inverter_data, 'battery_2_voltage') and hasattr(inverter_data, 'battery_2_current') and hasattr(inverter_data, 'battery_2_power'):
                    self.dc_model.ports[5].dc_voltage = inverter_data.battery_2_voltage
                    self.dc_model.ports[5].dc_current = inverter_data.battery_2_current
                    self.dc_model.ports[5].dc_power = inverter_data.battery_2_power  # No scaling - register 595 is already in watts
                    self.dc_model.ports[5].dc_status = 1 if abs(inverter_data.battery_2_power) > 10 else 0  # ON if power > 10W
                    # Use 3-phase specific battery 2 temperature if available, otherwise fallback to legacy
                    self.dc_model.ports[5].temperature = getattr(inverter_data, 'battery_2_temperature', getattr(inverter_data, 'battery_temperature', 25.0))
                else:
                    # Battery 2 not available - set to zero
                    self.dc_model.ports[5].dc_voltage = 0.0
                    self.dc_model.ports[5].dc_current = 0.0
                    self.dc_model.ports[5].dc_power = 0.0
                    self.dc_model.ports[5].dc_status = 0  # OFF
                    self.dc_model.ports[5].temperature = 25.0
            
            # Calculate totals for all active ports (excluding port 4 which is uninitialized)
            total_current = 0.0
            total_power = 0.0
            
            for i, port in enumerate(self.dc_model.ports):
                if i != 3:  # Skip port 4 (PV4 - uninitialized)
                    total_current += abs(port.dc_current)
                    total_power += port.dc_power
            
            self.dc_model.total_dc_current = total_current
            self.dc_model.total_dc_power = total_power
            
            # Update DC model registers
            self._update_dc_registers()
            
            # Log debug info based on actual number of ports
            if self.dc_model.num_ports == 6:
                self.logger.debug(f"Updated SunSpec DC model (714) with {inverter_data.get_inverter_type()} data - "
                                f"PV1:{self.dc_model.ports[0].dc_power:.0f}W PV2:{self.dc_model.ports[1].dc_power:.0f}W "
                                f"PV3:{self.dc_model.ports[2].dc_power:.0f}W ESS1:{self.dc_model.ports[4].dc_power:.0f}W "
                                f"ESS2:{self.dc_model.ports[5].dc_power:.0f}W")
            else:
                self.logger.debug(f"Updated SunSpec DC model (714) with {inverter_data.get_inverter_type()} data - "
                                f"PV1:{self.dc_model.ports[0].dc_power:.0f}W PV2:{self.dc_model.ports[1].dc_power:.0f}W "
                                f"PV3:{self.dc_model.ports[2].dc_power:.0f}W ESS1:{self.dc_model.ports[4].dc_power:.0f}W")
            
        except Exception as e:
            self.logger.error(f"Error updating DC model: {e}")
    
    def _update_dc_registers(self):
        """Update DC model (714) registers"""
        # Update total measurements
        self._set_register(SunSpecRegisterMap.DC_TOTAL_CURRENT, int(self.dc_model.total_dc_current * 100))  # Scale by 100
        self._set_register(SunSpecRegisterMap.DC_TOTAL_POWER, int(self.dc_model.total_dc_power))
        
        # Update port alarms (none for now)
        self._set_register_32bit(SunSpecRegisterMap.DC_PORT_ALARMS, 0)
        
        # Update individual port registers dynamically based on actual number of ports
        port_bases = [SunSpecRegisterMap.DC_PORT1_BASE, SunSpecRegisterMap.DC_PORT2_BASE,
                     SunSpecRegisterMap.DC_PORT3_BASE, SunSpecRegisterMap.DC_PORT4_BASE,
                     SunSpecRegisterMap.DC_PORT5_BASE]
        
        # Add 6th port base only if we have 6 ports (3-phase systems)
        if self.dc_model.num_ports == 6:
            port_bases.append(SunSpecRegisterMap.DC_PORT6_BASE)
        
        for i, port_base in enumerate(port_bases):
            if i >= len(self.dc_model.ports):
                break  # Don't update ports that don't exist
                
            port = self.dc_model.ports[i]
            
            # Skip port 4 (PV4) - keep it uninitialized
            if i == 3:
                continue
            
            # Update port measurements
            self._set_register(port_base + 10, int(port.dc_current * 100))  # DCA - scale by 100
            self._set_register(port_base + 11, int(port.dc_voltage * 10))   # DCV - scale by 10
            self._set_register(port_base + 12, int(port.dc_power))          # DCW
            self._set_register(port_base + 21, int(port.temperature * 10))  # Tmp - scale by 10
            self._set_register(port_base + 22, port.dc_status)              # DCSta
            
            # Update energy registers (simplified - could be enhanced with actual energy tracking)
            energy_injected = int(port.dc_energy_injected)
            energy_absorbed = int(port.dc_energy_absorbed)
            
            # DCWhInj (4 registers for uint64)
            self._set_register(port_base + 13, 0)  # High 32 bits (upper 16)
            self._set_register(port_base + 14, 0)  # High 32 bits (lower 16)
            self._set_register(port_base + 15, (energy_injected >> 16) & 0xFFFF)  # Low 32 bits (upper 16)
            self._set_register(port_base + 16, energy_injected & 0xFFFF)  # Low 32 bits (lower 16)
            
            # DCWhAbs (4 registers for uint64)
            self._set_register(port_base + 17, 0)  # High 32 bits (upper 16)
            self._set_register(port_base + 18, 0)  # High 32 bits (lower 16)
            self._set_register(port_base + 19, (energy_absorbed >> 16) & 0xFFFF)  # Low 32 bits (upper 16)
            self._set_register(port_base + 20, energy_absorbed & 0xFFFF)  # Low 32 bits (lower 16)
            
            # Update alarm register (32-bit) - no alarms for now
            self._set_register_32bit(port_base + 23, port.dc_alarm)
    
    def get_register_value(self, address):
        """Get register value by address"""
        return self.registers.get(address)
    
    def get_all_registers(self):
        """Get all register values"""
        return self.registers.copy()