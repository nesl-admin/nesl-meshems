"""
Sol-Ark 3-Phase Register Mapping and Scaling Factors

This module defines the register mappings and scaling factors for Sol-Ark 3-phase inverters,
extending the base Sol-Ark register definitions with 3-phase specific registers.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List
from ..solark_registers import SolArkRegisterMap, SolArkScalingFactors, SolArkBlockType, ModbusReadBlock


class SolArk3PhaseRegisterMap(SolArkRegisterMap):
    """Sol-Ark 3-Phase Modbus register addresses - extends base class"""
    
    # Grid voltage registers (3-phase) - hypothetical register addresses
    # Note: These would need to be confirmed with actual 3-phase Sol-Ark documentation
    GRID_VOLTAGE_L3N = 153      # Line3-to-Neutral voltage (new for 3-phase)
    GRID_VOLTAGE_L2L3 = 154     # Line2-to-Line3 voltage (new for 3-phase)
    GRID_VOLTAGE_L3L1 = 155     # Line3-to-Line1 voltage (new for 3-phase)
    
    # Grid current registers (3-phase)
    GRID_CURRENT_L3 = 163       # Grid current L3 (new for 3-phase)
    GRID_CT_CURRENT_L3 = 166    # Grid CT current L3 (new for 3-phase)
    
    # Inverter voltage registers (3-phase)
    INVERTER_VOLTAGE_L3N = 159  # Line3-to-Neutral voltage (new for 3-phase)
    INVERTER_VOLTAGE_L2L3 = 170 # Line2-to-Line3 voltage (new for 3-phase)
    INVERTER_VOLTAGE_L3L1 = 171 # Line3-to-Line1 voltage (new for 3-phase)
    
    # Inverter current registers (3-phase)
    INVERTER_CURRENT_L3 = 167   # Inverter current L3 (new for 3-phase)
    
    # Load measurements (3-phase)
    LOAD_POWER_L3 = 179         # Load power L3 (new for 3-phase)
    LOAD_CURRENT_L3 = 181       # Load current L3 (new for 3-phase)
    
    # Inverter power (3-phase)
    INVERTER_POWER_L3 = 175     # Line 3 power (WL3) (new for 3-phase)
    
    # PV inputs (3 MPPT for 3-phase)
    PV3_POWER = 189             # PV3 input power (new for 3-phase)
    PV1_VOLTAGE = 109           # DC voltage 1 (existing)
    PV1_CURRENT = 110           # DC current 1 (existing)
    PV2_VOLTAGE = 111           # DC voltage 2 (existing)
    PV2_CURRENT = 112           # DC current 2 (existing)
    PV3_VOLTAGE = 113           # DC voltage 3 (new for 3-phase)
    PV3_CURRENT = 114           # DC current 3 (new for 3-phase)


class SolArk3PhaseBlockType(Enum):
    """Enum to identify different logical blocks of Sol-Ark 3-phase registers"""
    
    # Inherit all base block types
    ENERGY = "energy"
    PV_ENERGY = "pv_energy"
    INVERTER_STATUS = "inverter_status"
    TEMPERATURES = "temperatures"
    APPARENT_POWER_38 = "apparent_power_38"
    GRID_POWER_FACTOR_89 = "grid_power_factor_89"
    GRID_INVERTER_150 = "grid_inverter_150"
    POWER_BATTERY_170 = "power_battery_170"
    BATTERY_STATUS_190 = "battery_status_190"
    BATTERY_CAPACITY_204 = "battery_capacity_204"
    CORRECTED_BATTERY_CAPACITY_107 = "corrected_battery_capacity_107"
    BATTERY_EMPTY_VOLTAGE_205 = "battery_empty_voltage_205"
    BATTERY_VOLTAGE_THRESHOLDS_220 = "battery_voltage_thresholds_220"
    BATTERY_PERCENT_THRESHOLDS_217 = "battery_percent_thresholds_217"
    BMS_DATA_312 = "bms_data_312"
    GRID_TYPE_286 = "grid_type_286"
    DIAGNOSTICS = "diagnostics"
    
    # New 3-phase specific blocks
    GRID_3PHASE_VOLTAGES = "grid_3phase_voltages"
    GRID_3PHASE_CURRENTS = "grid_3phase_currents"
    INVERTER_3PHASE_VOLTAGES = "inverter_3phase_voltages"
    INVERTER_3PHASE_CURRENTS = "inverter_3phase_currents"
    LOAD_3PHASE_MEASUREMENTS = "load_3phase_measurements"
    PV_3PHASE_MEASUREMENTS = "pv_3phase_measurements"


# Define the blocks of registers to be read for 3-phase Sol-Ark (max 20 registers per block)
SOLARK_3PHASE_READ_BLOCKS: List[ModbusReadBlock] = [
    # Base blocks (same as split-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.ENERGY,
        SolArk3PhaseRegisterMap.BATTERY_CHARGE_ENERGY,
        15,
        "Energy Data (70-84)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.PV_ENERGY,
        SolArk3PhaseRegisterMap.PV_ENERGY,
        1,
        "PV Energy (108)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.INVERTER_STATUS,
        SolArk3PhaseRegisterMap.INVERTER_STATUS,
        1,
        "Inverter Status (59)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.TEMPERATURES,
        SolArk3PhaseRegisterMap.DCDC_XFRMR_TEMP,
        2,
        "Temperatures (90-91)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.APPARENT_POWER_38,
        SolArk3PhaseRegisterMap.APPARENT_POWER,
        1,
        "Apparent Power (38)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_POWER_FACTOR_89,
        SolArk3PhaseRegisterMap.GRID_POWER_FACTOR,
        1,
        "Grid Power Factor (89)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_INVERTER_150,
        150,
        25,  # Extended to include L3 measurements
        "Grid/Inverter Data (150-174)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.POWER_BATTERY_170,
        170,
        25,  # Extended to include L3 measurements
        "Power/Battery Data (170-194)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_STATUS_190,
        SolArk3PhaseRegisterMap.BATTERY_POWER,
        10,
        "Battery Status (190-199)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_CAPACITY_204,
        SolArk3PhaseRegisterMap.BATTERY_CAPACITY,
        1,
        "Battery Capacity (204)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.CORRECTED_BATTERY_CAPACITY_107,
        SolArk3PhaseRegisterMap.CORRECTED_BATTERY_CAPACITY,
        1,
        "Corrected Battery Capacity (107)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_EMPTY_VOLTAGE_205,
        SolArk3PhaseRegisterMap.BATTERY_EMPTY_VOLTAGE,
        1,
        "Battery Empty Voltage (205)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_VOLTAGE_THRESHOLDS_220,
        SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_VOLTAGE,
        3,
        "Battery Voltage Thresholds (220-222)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_PERCENT_THRESHOLDS_217,
        SolArk3PhaseRegisterMap.BATTERY_SHUTDOWN_PERCENT,
        3,
        "Battery Percent Thresholds (217-219)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BMS_DATA_312,
        SolArk3PhaseRegisterMap.BMS_CHARGING_VOLTAGE,
        12,
        "BMS Data (312-323)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_TYPE_286,
        SolArk3PhaseRegisterMap.GRID_TYPE,
        1,
        "Grid Type (286)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.DIAGNOSTICS,
        SolArk3PhaseRegisterMap.COMM_VERSION,
        6,
        "Diagnostics (2-7)"
    ),
    # New 3-phase specific blocks
    ModbusReadBlock(
        SolArk3PhaseBlockType.PV_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV1_VOLTAGE,
        6,  # PV1-3 voltage and current (109-114)
        "PV 3-Phase Measurements (109-114)"
    ),
]