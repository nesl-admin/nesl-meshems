"""
Sol-Ark 3-Phase Modbus RTU Client

This module implements the Modbus RTU client for communicating with Sol-Ark 3-phase inverters
over RS485, extending the split-phase implementation with 3-phase specific functionality.
"""

import logging
import time
from typing import Optional, List

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

from .base import InverterClient
from .solark_data import SolArk3PhaseData
from .solark_3phase_registers import (
    SolArk3PhaseRegisterMap,
    SolArk3PhaseBlockType,
    ModbusReadBlock,
    SOLARK_3PHASE_READ_BLOCKS
)
from ..solark_registers import SolArkScalingFactors


class SolArk3PhaseClient(InverterClient):
    """Modbus RTU client for Sol-Ark 3-phase inverters"""
    
    def __init__(self, port: str, baudrate: int = 9600, modbus_address: int = 1):
        """
        Initialize Sol-Ark 3-phase Modbus client
        
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0')
            baudrate: Serial baudrate (default: 9600)
            modbus_address: Modbus slave address (default: 1)
        """
        super().__init__(port, baudrate, modbus_address)
        self.logger = logging.getLogger(__name__)
        self._data = SolArk3PhaseData()
        
        # Initialize Modbus client
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1.0
        )
        
        self.logger.info(f"Initialized Sol-Ark 3-phase client on {port} at {baudrate} baud, address {modbus_address}")
    
    @property
    def data(self) -> SolArk3PhaseData:
        """Get current inverter data"""
        return self._data
    
    def get_inverter_type(self) -> str:
        """Get inverter type identifier"""
        return "solark_3phase"
    
    def connect(self) -> bool:
        """Connect to the Modbus device"""
        try:
            if self.client.connect():
                self.logger.info(f"Connected to Sol-Ark 3-phase on {self.port}")
                return True
            else:
                self.logger.error(f"Failed to connect to Sol-Ark 3-phase on {self.port}")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to Sol-Ark 3-phase: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the Modbus device"""
        try:
            self.client.close()
            self.logger.info("Disconnected from Sol-Ark 3-phase")
        except Exception as e:
            self.logger.error(f"Error disconnecting from Sol-Ark 3-phase: {e}")
    
    def _correct_signed_value(self, value: int) -> int:
        """Convert unsigned 16-bit value to signed if necessary"""
        if value > 32767:
            return value - 65536
        return value
    
    def _combine_32bit(self, high_word: int, low_word: int) -> int:
        """Combine high and low 16-bit words into a 32-bit signed value"""
        combined = (high_word << 16) | low_word
        # Convert to signed 32-bit if necessary
        if combined > 2147483647:  # 2^31 - 1
            combined -= 4294967296  # 2^32
        return combined
    
    def _read_holding_registers(self, start_register: int, num_registers: int) -> Optional[List[int]]:
        """Read holding registers from the device"""
        try:
            result = self.client.read_holding_registers(
                address=start_register,
                count=num_registers,
                device_id=self.modbus_address
            )
            
            if result.isError():
                self.logger.error(f"Modbus error reading registers {start_register}-{start_register + num_registers - 1}: {result}")
                return None
            
            return result.registers
        
        except ModbusException as e:
            self.logger.error(f"Modbus exception reading registers {start_register}-{start_register + num_registers - 1}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading registers {start_register}-{start_register + num_registers - 1}: {e}")
            return None
    
    def _process_block(self, block: ModbusReadBlock, registers: List[int]):
        """Process data from a read block using correct Sol-Ark register mappings"""
        try:
            if block.block_type == SolArk3PhaseBlockType.GRID_TYPE_286:
                # Grid Type (AC Wiring Type) - Register 184
                self._data.grid_type = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.INVERTER_STATUS:
                # Operation Status - Register 500
                self._data.inverter_status = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_STATUS_190:
                # Power Button Status - Register 551
                self._data.power_button_status = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_INVERTER_150:
                # AC Relay Status - Register 552
                self._data.grid_relay_status = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_3PHASE_VOLTAGES:
                # Grid Phase Voltages - Registers 598-600 (L1N, L2N, L3N)
                self._data.grid_voltage_l1n = registers[0] / SolArkScalingFactors.VOLTAGE  # 0.1V scale
                self._data.grid_voltage_l2n = registers[1] / SolArkScalingFactors.VOLTAGE  # 0.1V scale
                self._data.grid_voltage_l3n = registers[2] / SolArkScalingFactors.VOLTAGE  # 0.1V scale
                
                # Calculate line-to-line voltages (L-L = L-N * sqrt(3))
                self._data.grid_voltage_l1l2 = self._data.grid_voltage_l1n * 1.732
                self._data.grid_voltage_l2l3 = self._data.grid_voltage_l2n * 1.732
                self._data.grid_voltage_l3l1 = self._data.grid_voltage_l3n * 1.732
                
                # Legacy grid_voltage for backward compatibility - use L1L2 voltage
                self._data.grid_voltage = self._data.grid_voltage_l1l2
            
            elif block.block_type == SolArk3PhaseBlockType.ENERGY:
                # Grid Frequency - Register 609
                self._data.grid_frequency = registers[0] / SolArkScalingFactors.FREQUENCY  # 0.01Hz scale
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_3PHASE_CURRENTS:
                # Grid CT Currents - Registers 610-612 (L1, L2, L3)
                self._data.grid_ct_current_l1 = registers[0] / SolArkScalingFactors.CURRENT  # 0.01A scale
                self._data.grid_ct_current_l2 = registers[1] / SolArkScalingFactors.CURRENT  # 0.01A scale
                self._data.grid_ct_current_l3 = registers[2] / SolArkScalingFactors.CURRENT  # 0.01A scale
                
                # Set legacy grid current values for compatibility
                self._data.grid_current_l1 = self._data.grid_ct_current_l1
                self._data.grid_current_l2 = self._data.grid_ct_current_l2
                self._data.grid_current_l3 = self._data.grid_ct_current_l3
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_POWER_FACTOR_89:
                # Grid Power Factor - Register 621 (signed 16-bit integer)
                signed_value = self._correct_signed_value(registers[0])
                self._data.grid_power_factor = signed_value / 1000.0  # 0.001 scale factor
            
            elif block.block_type == SolArk3PhaseBlockType.POWER_BATTERY_170:
                # Grid Power Low Words - Registers 622-624 (L1, L2, L3)
                self._grid_power_l1_low = registers[0]
                self._grid_power_l2_low = registers[1]
                self._grid_power_l3_low = registers[2]
            
            elif block.block_type == SolArk3PhaseBlockType.APPARENT_POWER_38:
                # Grid Total Power Low - Register 625
                self._grid_total_power_low = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS:
                # Grid Power High Words - Registers 687-690 (L1, L2, L3, Total)
                grid_power_l1_high = registers[0]
                grid_power_l2_high = registers[1]
                grid_power_l3_high = registers[2]
                grid_total_power_high = registers[3]
                
                # Combine high and low words to get 32-bit power values
                if hasattr(self, '_grid_power_l1_low'):
                    self._data.grid_power_l1 = self._combine_32bit(grid_power_l1_high, self._grid_power_l1_low)
                if hasattr(self, '_grid_power_l2_low'):
                    self._data.grid_power_l2 = self._combine_32bit(grid_power_l2_high, self._grid_power_l2_low)
                if hasattr(self, '_grid_power_l3_low'):
                    self._data.grid_power_l3 = self._combine_32bit(grid_power_l3_high, self._grid_power_l3_low)
                if hasattr(self, '_grid_total_power_low'):
                    self._data.grid_power = self._combine_32bit(grid_total_power_high, self._grid_total_power_low)
            
            elif block.block_type == SolArk3PhaseBlockType.CORRECTED_BATTERY_CAPACITY_107:
                # Grid Apparent Power Low - Register 608
                self._grid_apparent_power_low = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_CAPACITY_204:
                # Grid Apparent Power High - Register 704
                if hasattr(self, '_grid_apparent_power_low'):
                    self._data.apparent_power = self._combine_32bit(registers[0], self._grid_apparent_power_low)
            
            elif block.block_type == SolArk3PhaseBlockType.INVERTER_3PHASE_CURRENTS:
                # Grid Reactive Power - Registers 710-712 (L1, L2, L3)
                self._data.grid_reactive_power_l1 = registers[0] * 10  # 10 VAR scale
                self._data.grid_reactive_power_l2 = registers[1] * 10  # 10 VAR scale
                self._data.grid_reactive_power_l3 = registers[2] * 10  # 10 VAR scale
                
                # Calculate total reactive power
                self._data.grid_reactive_power_total = (self._data.grid_reactive_power_l1 +
                                                       self._data.grid_reactive_power_l2 +
                                                       self._data.grid_reactive_power_l3)
            
            elif block.block_type == SolArk3PhaseBlockType.TEMPERATURES:
                # Temperature measurements - Registers 540-541 (IGBT, Heat Sink)
                self._data.igbt_temp = (registers[0] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
                self._data.dcdc_xfrmr_temp = (registers[1] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
            
            elif block.block_type == SolArk3PhaseBlockType.PV_3PHASE_MEASUREMENTS:
                # PV measurements - Registers 109-114 (PV1-3 voltage and current)
                self._data.pv1_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                self._data.pv1_current = registers[1] / SolArkScalingFactors.CURRENT
                self._data.pv2_voltage = registers[2] / SolArkScalingFactors.VOLTAGE
                self._data.pv2_current = registers[3] / SolArkScalingFactors.CURRENT
                self._data.pv3_voltage = registers[4] / SolArkScalingFactors.VOLTAGE
                self._data.pv3_current = registers[5] / SolArkScalingFactors.CURRENT
                
                # Calculate PV power
                self._data.pv1_power = self._data.pv1_voltage * self._data.pv1_current
                self._data.pv2_power = self._data.pv2_voltage * self._data.pv2_current
                self._data.pv3_power = self._data.pv3_voltage * self._data.pv3_current
                self._data.pv_power_total = (self._data.pv1_power + self._data.pv2_power + self._data.pv3_power) / 1000.0
            
            # SunSpec Model 713 (DER Storage Capacity) blocks
            elif block.block_type == SolArk3PhaseBlockType.MODEL_713_BATTERY_CAPACITY:
                # Battery Calculated Capacity - Register 592 (Ah)
                # Note: CSV says "In Ah, battery_capacity_ah * 409.6"
                self._data.battery_calculated_capacity = registers[0]  # Already in Ah
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_713_BATTERY_SOC:
                # Battery SOC - Register 588 (%)
                self._data.battery_soc_713 = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_713_BATTERY_SOH:
                # Battery SOH - Register 10006 (%)
                self._data.battery_soh = registers[0]
            
            # SunSpec Model 714 (DER DC Measurement) blocks
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_PV1_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.PV1_POWER:
                    # PV1 Power - Register 672
                    self._data.pv1_power = registers[0]
                elif block.start_register == SolArk3PhaseRegisterMap.PV1_VOLTAGE:
                    # PV1 Voltage/Current - Registers 676-677
                    self._data.pv1_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                    self._data.pv1_current = registers[1] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_PV2_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.PV2_POWER:
                    # PV2 Power - Register 673
                    self._data.pv2_power = registers[0]
                elif block.start_register == SolArk3PhaseRegisterMap.PV2_VOLTAGE:
                    # PV2 Voltage/Current - Registers 678-679
                    self._data.pv2_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                    self._data.pv2_current = registers[1] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_PV3_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.PV3_POWER:
                    # PV3 Power - Register 674
                    self._data.pv3_power = registers[0]
                elif block.start_register == SolArk3PhaseRegisterMap.PV3_VOLTAGE:
                    # PV3 Voltage/Current - Registers 680-681
                    self._data.pv3_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                    self._data.pv3_current = registers[1] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_PV4_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.PV4_POWER:
                    # PV4 Power - Register 675
                    self._data.pv4_power = registers[0]
                elif block.start_register == SolArk3PhaseRegisterMap.PV4_VOLTAGE:
                    # PV4 Voltage/Current - Registers 682-683
                    self._data.pv4_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                    self._data.pv4_current = registers[1] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_BATTERY1_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.BATTERY_1_VOLTAGE:
                    # Battery 1 Voltage - Register 587
                    self._data.battery_1_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                elif block.start_register == SolArk3PhaseRegisterMap.BATTERY_1_POWER:
                    # Battery 1 Power/Current - Registers 590-591
                    self._data.battery_1_power = self._correct_signed_value(registers[0])  # int16
                    self._data.battery_1_current = self._correct_signed_value(registers[1]) / SolArkScalingFactors.CURRENT  # int16
            
            elif block.block_type == SolArk3PhaseBlockType.MODEL_714_BATTERY2_MEASUREMENTS:
                if block.start_register == SolArk3PhaseRegisterMap.BATTERY_2_VOLTAGE:
                    # Battery 2 Voltage - Register 593
                    self._data.battery_2_voltage = registers[0] / SolArkScalingFactors.VOLTAGE
                elif block.start_register == SolArk3PhaseRegisterMap.BATTERY_2_CURRENT:
                    # Battery 2 Current/Power - Registers 594-595
                    self._data.battery_2_current = self._correct_signed_value(registers[0]) / SolArkScalingFactors.CURRENT  # int16
                    self._data.battery_2_power = self._correct_signed_value(registers[1])  # int16
            
            # Update total PV power to include PV4
            if hasattr(self._data, 'pv4_power'):
                self._data.pv_power_total = (self._data.pv1_power + self._data.pv2_power +
                                           self._data.pv3_power + self._data.pv4_power) / 1000.0
            
            # Legacy blocks for compatibility (using existing register definitions)
            elif block.block_type == SolArk3PhaseBlockType.PV_ENERGY:
                # PV Energy - Register 108
                self._data.pv_energy = registers[0] / SolArkScalingFactors.ENERGY
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_EMPTY_VOLTAGE_205:
                # Battery Empty Voltage - Register 205
                self._data.battery_empty_voltage = registers[0] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_VOLTAGE_THRESHOLDS_220:
                # Battery Voltage Thresholds - Registers 220-222
                offset = SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_VOLTAGE - block.start_register
                self._data.battery_shutdown_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BATTERY_RESTART_VOLTAGE - block.start_register
                self._data.battery_restart_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BATTERY_LOW_VOLTAGE - block.start_register
                self._data.battery_low_voltage = registers[offset] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_PERCENT_THRESHOLDS_217:
                # Battery Percent Thresholds - Registers 217-219
                offset = SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_PERCENT - block.start_register
                self._data.battery_shutdown_percent = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BATTERY_RESTART_PERCENT - block.start_register
                self._data.battery_restart_percent = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BATTERY_LOW_PERCENT - block.start_register
                self._data.battery_low_percent = registers[offset]
            
            elif block.block_type == SolArk3PhaseBlockType.BMS_DATA_312:
                # BMS Data - Registers 312-323
                offset = SolArk3PhaseRegisterMap.BMS_CHARGING_VOLTAGE - block.start_register
                self._data.bms_charging_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BMS_DISCHARGE_VOLTAGE - block.start_register
                self._data.bms_discharge_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BMS_CHARGING_CURRENT_LIMIT - block.start_register
                self._data.bms_charging_current_limit = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BMS_DISCHARGE_CURRENT_LIMIT - block.start_register
                self._data.bms_discharge_current_limit = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BMS_REAL_TIME_SOC - block.start_register
                self._data.bms_real_time_soc = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BMS_REAL_TIME_VOLTAGE - block.start_register
                self._data.bms_real_time_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BMS_REAL_TIME_CURRENT - block.start_register
                self._data.bms_real_time_current = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BMS_REAL_TIME_TEMP - block.start_register
                self._data.bms_real_time_temp = (registers[offset] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
                
                offset = SolArk3PhaseRegisterMap.BMS_WARNING - block.start_register
                self._data.bms_warning = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BMS_FAULT - block.start_register
                self._data.bms_fault = registers[offset]
            
            elif block.block_type == SolArk3PhaseBlockType.DIAGNOSTICS:
                # Diagnostics - Registers 2-7
                offset = SolArk3PhaseRegisterMap.COMM_VERSION - block.start_register
                self._data.comm_version = registers[offset]
                
                for i in range(5):
                    offset = (SolArk3PhaseRegisterMap.SN_BYTE_01 + i) - block.start_register
                    if offset < len(registers):
                        self._data.serial_number_parts[i] = registers[offset]
            
            else:
                self.logger.warning(f"Unknown block type: {block.block_type}")
        
        except Exception as e:
            self.logger.error(f"Error processing block {block.description}: {e}")
    
    def poll(self) -> bool:
        """Poll all register blocks from the Sol-Ark 3-phase inverter"""
        success_count = 0
        total_blocks = len(SOLARK_3PHASE_READ_BLOCKS)
        
        for block in SOLARK_3PHASE_READ_BLOCKS:
            registers = self._read_holding_registers(block.start_register, block.num_registers)
            
            if registers is not None:
                self._process_block(block, registers)
                self.logger.debug(f"Successfully polled block: {block.description}")
                success_count += 1
            else:
                self.logger.error(f"Failed to poll block: {block.description}")
                self._data.last_failure = time.time()
        
        if success_count > 0:
            self._data.last_update = time.time()
            self.logger.info(f"Poll completed: {success_count}/{total_blocks} blocks successful")
            return True
        else:
            self.logger.error("Poll failed: No blocks read successfully")
            return False
    
    # Convenience methods for status checking
    def is_grid_connected(self) -> bool:
        """Check if grid is connected"""
        return self._data.grid_relay_status > 0
    
    def is_generator_connected(self) -> bool:
        """Check if generator is connected"""
        return self._data.generator_relay_status > 0
    
    def is_battery_charging(self) -> bool:
        """Check if battery is charging"""
        return self._data.battery_power < 0
    
    def is_battery_discharging(self) -> bool:
        """Check if battery is discharging"""
        return self._data.battery_power > 0
    
    def is_selling_to_grid(self) -> bool:
        """Check if selling power to grid"""
        return self._data.grid_power < 0
    
    def is_buying_from_grid(self) -> bool:
        """Check if buying power from grid"""
        return self._data.grid_power > 0
    
    def get_serial_number(self) -> str:
        """Get formatted serial number string"""
        serial_str = ""
        for part in self._data.serial_number_parts:
            if part == 0:
                break
            char1 = (part >> 8) & 0xFF
            char2 = part & 0xFF
            if char1 != 0:
                serial_str += chr(char1)
            if char2 != 0:
                serial_str += chr(char2)
        return serial_str
    
    def get_battery_temperature_f(self) -> float:
        """Get battery temperature in Fahrenheit"""
        return (self._data.battery_temperature * 9.0 / 5.0) + 32.0