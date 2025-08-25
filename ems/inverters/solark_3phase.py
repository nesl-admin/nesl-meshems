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
        """Process data from a read block"""
        try:
            if block.block_type == SolArk3PhaseBlockType.ENERGY:
                # Registers 70-84 (15 regs) - same as split-phase
                offset = SolArk3PhaseRegisterMap.BATTERY_CHARGE_ENERGY - block.start_register
                self._data.battery_charge_energy = registers[offset] / SolArkScalingFactors.ENERGY
                
                offset = SolArk3PhaseRegisterMap.BATTERY_DISCHARGE_ENERGY - block.start_register
                self._data.battery_discharge_energy = registers[offset] / SolArkScalingFactors.ENERGY
                
                offset = SolArk3PhaseRegisterMap.GRID_BUY_ENERGY - block.start_register
                self._data.grid_buy_energy = registers[offset] / SolArkScalingFactors.ENERGY
                
                offset = SolArk3PhaseRegisterMap.GRID_SELL_ENERGY - block.start_register
                self._data.grid_sell_energy = registers[offset] / SolArkScalingFactors.ENERGY
                
                offset = SolArk3PhaseRegisterMap.GRID_FREQUENCY - block.start_register
                self._data.grid_frequency = registers[offset] / SolArkScalingFactors.FREQUENCY
                
                offset = SolArk3PhaseRegisterMap.LOAD_ENERGY - block.start_register
                self._data.load_energy = registers[offset] / SolArkScalingFactors.ENERGY
            
            elif block.block_type == SolArk3PhaseBlockType.PV_ENERGY:
                # Register 108 (1 reg) - same as split-phase
                self._data.pv_energy = registers[0] / SolArkScalingFactors.ENERGY
            
            elif block.block_type == SolArk3PhaseBlockType.INVERTER_STATUS:
                # Register 59 (1 reg) - same as split-phase
                self._data.inverter_status = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.TEMPERATURES:
                # Registers 90-91 (2 regs) - same as split-phase
                offset = SolArk3PhaseRegisterMap.DCDC_XFRMR_TEMP - block.start_register
                self._data.dcdc_xfrmr_temp = (registers[offset] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
                
                offset = SolArk3PhaseRegisterMap.IGBT_HEATSINK_TEMP - block.start_register
                self._data.igbt_temp = (registers[offset] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
            
            elif block.block_type == SolArk3PhaseBlockType.APPARENT_POWER_38:
                # Register 38 (1 reg) - same as split-phase
                self._data.apparent_power = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_POWER_FACTOR_89:
                # Register 89 (1 reg) - same as split-phase
                self._data.grid_power_factor = registers[0] / SolArkScalingFactors.CURRENT  # Power factor is scaled by 100
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_INVERTER_150:
                # Registers 150-174 (25 regs) - extended for 3-phase
                # Grid voltage registers (3-phase)
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L1N - block.start_register
                self._data.grid_voltage_l1n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L2N - block.start_register
                self._data.grid_voltage_l2n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L3N - block.start_register
                self._data.grid_voltage_l3n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L1L2 - block.start_register
                self._data.grid_voltage_l1l2 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L2L3 - block.start_register
                self._data.grid_voltage_l2l3 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.GRID_VOLTAGE_L3L1 - block.start_register
                self._data.grid_voltage_l3l1 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                # Legacy grid_voltage for backward compatibility - use L1L2 voltage
                self._data.grid_voltage = self._data.grid_voltage_l1l2
                
                # Inverter voltage registers (3-phase)
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L1N - block.start_register
                self._data.inverter_voltage_l1n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L2N - block.start_register
                self._data.inverter_voltage_l2n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L3N - block.start_register
                self._data.inverter_voltage_l3n = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L1L2 - block.start_register
                self._data.inverter_voltage_l1l2 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L2L3 - block.start_register
                self._data.inverter_voltage_l2l3 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.INVERTER_VOLTAGE_L3L1 - block.start_register
                self._data.inverter_voltage_l3l1 = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                # Legacy inverter_voltage for backward compatibility - use L1L2 voltage
                self._data.inverter_voltage = self._data.inverter_voltage_l1l2
                self._data.inverter_voltage_ln = self._data.inverter_voltage_l1n  # Legacy compatibility
                
                # Grid current registers (3-phase)
                offset = SolArk3PhaseRegisterMap.GRID_CURRENT_L1 - block.start_register
                self._data.grid_current_l1 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.GRID_CURRENT_L2 - block.start_register
                self._data.grid_current_l2 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.GRID_CURRENT_L3 - block.start_register
                self._data.grid_current_l3 = registers[offset] / SolArkScalingFactors.CURRENT
                
                # Grid CT current registers (3-phase)
                offset = SolArk3PhaseRegisterMap.GRID_CT_CURRENT_L1 - block.start_register
                self._data.grid_ct_current_l1 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.GRID_CT_CURRENT_L2 - block.start_register
                self._data.grid_ct_current_l2 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.GRID_CT_CURRENT_L3 - block.start_register
                self._data.grid_ct_current_l3 = registers[offset] / SolArkScalingFactors.CURRENT
                
                # Inverter current registers (3-phase)
                offset = SolArk3PhaseRegisterMap.INVERTER_CURRENT_L1 - block.start_register
                self._data.inverter_current_l1 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.INVERTER_CURRENT_L2 - block.start_register
                self._data.inverter_current_l2 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.INVERTER_CURRENT_L3 - block.start_register
                self._data.inverter_current_l3 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.SMART_LOAD_POWER - block.start_register
                self._data.smart_load_power = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.GRID_POWER - block.start_register
                self._data.grid_power = self._correct_signed_value(registers[offset])
            
            elif block.block_type == SolArk3PhaseBlockType.POWER_BATTERY_170:
                # Registers 170-194 (25 regs) - extended for 3-phase
                offset = SolArk3PhaseRegisterMap.INVERTER_OUTPUT_POWER - block.start_register
                self._data.inverter_output_power = self._correct_signed_value(registers[offset])
                
                # Load power (3-phase)
                offset = SolArk3PhaseRegisterMap.LOAD_POWER_L1 - block.start_register
                self._data.load_power_l1 = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.LOAD_POWER_L2 - block.start_register
                self._data.load_power_l2 = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.LOAD_POWER_L3 - block.start_register
                self._data.load_power_l3 = registers[offset]
                
                self._data.load_power_total = self._data.load_power_l1 + self._data.load_power_l2 + self._data.load_power_l3
                
                # Load current (3-phase)
                offset = SolArk3PhaseRegisterMap.LOAD_CURRENT_L1 - block.start_register
                self._data.load_current_l1 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.LOAD_CURRENT_L2 - block.start_register
                self._data.load_current_l2 = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.LOAD_CURRENT_L3 - block.start_register
                self._data.load_current_l3 = registers[offset] / SolArkScalingFactors.CURRENT
                
                # Battery measurements (same as split-phase)
                offset = SolArk3PhaseRegisterMap.BATTERY_TEMPERATURE - block.start_register
                self._data.battery_temperature = (registers[offset] - SolArkScalingFactors.TEMPERATURE_OFFSET) / SolArkScalingFactors.TEMPERATURE_SCALE
                
                offset = SolArk3PhaseRegisterMap.BATTERY_VOLTAGE - block.start_register
                self._data.battery_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BATTERY_SOC - block.start_register
                self._data.battery_soc = registers[offset]
                
                # PV measurements (3 MPPT for 3-phase)
                offset = SolArk3PhaseRegisterMap.PV1_POWER - block.start_register
                self._data.pv1_power = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.PV2_POWER - block.start_register
                self._data.pv2_power = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.PV3_POWER - block.start_register
                self._data.pv3_power = registers[offset]
                
                # Inverter power (3-phase)
                offset = SolArk3PhaseRegisterMap.INVERTER_POWER_L1 - block.start_register
                self._data.inverter_power_l1 = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.INVERTER_POWER_L2 - block.start_register
                self._data.inverter_power_l2 = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.INVERTER_POWER_L3 - block.start_register
                self._data.inverter_power_l3 = registers[offset]
                
                self._data.pv_power_total = (self._data.pv1_power + self._data.pv2_power + self._data.pv3_power) / 1000.0
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_STATUS_190:
                # Registers 190-199 (10 regs) - same as split-phase
                offset = SolArk3PhaseRegisterMap.BATTERY_POWER - block.start_register
                self._data.battery_power = self._correct_signed_value(registers[offset])
                
                offset = SolArk3PhaseRegisterMap.BATTERY_CURRENT - block.start_register
                self._data.battery_current = self._correct_signed_value(registers[offset]) / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.LOAD_FREQUENCY - block.start_register
                self._data.load_frequency = registers[offset] / SolArkScalingFactors.FREQUENCY
                
                offset = SolArk3PhaseRegisterMap.INVERTER_FREQUENCY - block.start_register
                self._data.inverter_frequency = registers[offset] / SolArkScalingFactors.FREQUENCY
                
                offset = SolArk3PhaseRegisterMap.GRID_RELAY_STATUS - block.start_register
                self._data.grid_relay_status = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.GENERATOR_RELAY_STATUS - block.start_register
                self._data.generator_relay_status = registers[offset]
            
            elif block.block_type == SolArk3PhaseBlockType.PV_3PHASE_MEASUREMENTS:
                # Registers 109-114 (6 regs) - PV voltage and current measurements
                offset = SolArk3PhaseRegisterMap.PV1_VOLTAGE - block.start_register
                self._data.pv1_voltage = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.PV1_CURRENT - block.start_register
                self._data.pv1_current = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.PV2_VOLTAGE - block.start_register
                self._data.pv2_voltage = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.PV2_CURRENT - block.start_register
                self._data.pv2_current = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.PV3_VOLTAGE - block.start_register
                self._data.pv3_voltage = registers[offset] / SolArkScalingFactors.VOLTAGE
                
                offset = SolArk3PhaseRegisterMap.PV3_CURRENT - block.start_register
                self._data.pv3_current = registers[offset] / SolArkScalingFactors.CURRENT
            
            # Handle remaining block types same as split-phase
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_CAPACITY_204:
                self._data.battery_capacity = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.CORRECTED_BATTERY_CAPACITY_107:
                self._data.corrected_battery_capacity = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_EMPTY_VOLTAGE_205:
                self._data.battery_empty_voltage = registers[0] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_VOLTAGE_THRESHOLDS_220:
                offset = SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_VOLTAGE - block.start_register
                self._data.battery_shutdown_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BATTERY_RESTART_VOLTAGE - block.start_register
                self._data.battery_restart_voltage = registers[offset] / SolArkScalingFactors.CURRENT
                
                offset = SolArk3PhaseRegisterMap.BATTERY_LOW_VOLTAGE - block.start_register
                self._data.battery_low_voltage = registers[offset] / SolArkScalingFactors.CURRENT
            
            elif block.block_type == SolArk3PhaseBlockType.BATTERY_PERCENT_THRESHOLDS_217:
                offset = SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_PERCENT - block.start_register
                self._data.battery_shutdown_percent = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BATTERY_RESTART_PERCENT - block.start_register
                self._data.battery_restart_percent = registers[offset]
                
                offset = SolArk3PhaseRegisterMap.BATTERY_LOW_PERCENT - block.start_register
                self._data.battery_low_percent = registers[offset]
            
            elif block.block_type == SolArk3PhaseBlockType.BMS_DATA_312:
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
            
            elif block.block_type == SolArk3PhaseBlockType.GRID_TYPE_286:
                self._data.grid_type = registers[0]
            
            elif block.block_type == SolArk3PhaseBlockType.DIAGNOSTICS:
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