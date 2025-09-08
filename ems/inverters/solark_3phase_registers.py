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
    """Sol-Ark 3-Phase Modbus register addresses - based on HV Sol-Ark to SunSpec mapping CSV"""
    
    # SunSpec Model 701 register mappings from CSV
    # Grid Type (AC Wiring Type) - Register 184
    GRID_TYPE = 184
    
    # Operating State - Register 551 (Power Button Status)
    POWER_BUTTON_STATUS = 551
    
    # Inverter State - Register 500 (Operation Status)
    OPERATION_STATUS = 500
    
    # Grid Connection State - Register 552 (AC Relay Status)
    AC_RELAY_STATUS = 552
    
    # Grid measurements (3-phase) - from CSV mapping
    GRID_VOLTAGE_L1N = 598      # Grid Phase A Voltage (VL1)
    GRID_VOLTAGE_L2N = 599      # Grid Phase B Voltage (VL2)
    GRID_VOLTAGE_L3N = 600      # Grid Phase C Voltage (VL3)
    
    # Line-to-line voltages calculated from line-to-neutral
    # VL1L2 = Register 598 * 1.732 (Grid Phase A Voltage * sqrt(3))
    # VL2L3 = Register 599 * 1.732 (Grid Phase B Voltage * sqrt(3))
    # VL3L1 = Register 600 * 1.732 (Grid Phase C Voltage * sqrt(3))
    
    # Grid current registers (3-phase) - from CSV
    GRID_CT_CURRENT_L1 = 610    # Grid Internal CT Phase A Current
    GRID_CT_CURRENT_L2 = 611    # Grid Internal CT Phase B Current
    GRID_CT_CURRENT_L3 = 612    # Grid Internal CT Phase C Current
    
    # Grid power registers (3-phase) - from CSV
    GRID_POWER_L1_LOW = 622     # Grid Side Phase A Power Low Word
    GRID_POWER_L1_HIGH = 687    # Grid Side Phase A Power High Word
    GRID_POWER_L2_LOW = 623     # Grid Side Phase B Power Low Word
    GRID_POWER_L2_HIGH = 688    # Grid Side Phase B Power High Word
    GRID_POWER_L3_LOW = 624     # Grid Side Phase C Power Low Word
    GRID_POWER_L3_HIGH = 689    # Grid Side Phase C Power High Word
    
    # Total grid power - from CSV
    GRID_TOTAL_POWER_LOW = 625  # Grid Side Total Power Low Word
    GRID_TOTAL_POWER_HIGH = 690 # Grid Side Total Power High Word
    
    # Grid reactive power (3-phase) - from CSV
    GRID_REACTIVE_POWER_L1 = 710  # Grid Phase A Reactive Power
    GRID_REACTIVE_POWER_L2 = 711  # Grid Phase B Reactive Power
    GRID_REACTIVE_POWER_L3 = 712  # Grid Phase C Reactive Power
    
    # Grid power factor - from CSV
    GRID_POWER_FACTOR = 621     # Grid Power Factor
    
    # Grid frequency - from CSV
    GRID_FREQUENCY = 609        # Grid Frequency
    
    # Grid apparent power - from CSV
    GRID_APPARENT_POWER_LOW = 608   # Grid Internal CT Total Apparent Power Low Word
    GRID_APPARENT_POWER_HIGH = 704  # Grid Internal CT Total Apparent Power High Word
    
    # Temperature measurements - from CSV
    HEAT_SINK_TEMPERATURE = 541     # Heat Sink Temperature
    IGBT_TEMPERATURE = 540          # IGBT/MOSFET Temperature
    
    # PV inputs (4 MPPT for 3-phase) - from CSV Model 714 mapping
    PV1_VOLTAGE = 676           # PV1 Voltage
    PV1_CURRENT = 677           # PV1 Current
    PV1_POWER = 672             # PV1 Input Power
    PV2_VOLTAGE = 678           # PV2 Voltage
    PV2_CURRENT = 679           # PV2 Current
    PV2_POWER = 673             # PV2 Input Power
    PV3_VOLTAGE = 680           # PV3 Voltage
    PV3_CURRENT = 681           # PV3 Current
    PV3_POWER = 674             # PV3 Input Power
    PV4_VOLTAGE = 682           # PV4 Voltage
    PV4_CURRENT = 683           # PV4 Current
    PV4_POWER = 675             # PV4 Input Power
    
    # SunSpec Model 713 (DER Storage Capacity) registers - from CSV mapping
    BATTERY_CALCULATED_CAPACITY = 592   # Battery 1 Calculated Capacity (Ah)
    BATTERY_SOC = 588                   # Battery 1 SOC (%)
    BATTERY_SOH = 10006                 # Battery SOH (%)
    
    # SunSpec Model 714 (DER DC Measurement) battery registers - from CSV mapping
    BATTERY_1_VOLTAGE = 587             # Battery 1 Voltage
    BATTERY_1_CURRENT = 591             # Battery 1 Current (int16)
    BATTERY_1_POWER = 590               # Battery 1 Output Power (int16)
    BATTERY_2_VOLTAGE = 593             # Battery 2 Voltage
    BATTERY_2_CURRENT = 594             # Battery 2 Current (int16)
    BATTERY_2_POWER = 595               # Battery 2 Output Power (int16)
    
    # Load voltage measurements (3-phase) - from CSV mapping
    LOAD_VOLTAGE_L1N = 644              # Load Phase A Voltage
    LOAD_VOLTAGE_L2N = 645              # Load Phase B Voltage
    LOAD_VOLTAGE_L3N = 646              # Load Phase C Voltage
    LOAD_FREQUENCY = 655                # Load Frequency
    
    # Battery temperatures (3-phase specific) - from CSV mapping
    BATTERY_1_TEMPERATURE = 586         # Battery 1 Temperature
    BATTERY_2_TEMPERATURE = 596         # Battery 2 Temperature
    
    # Load power measurements (3-phase) - from CSV mapping
    LOAD_POWER_L1_LOW = 650             # Load Side Phase A Power Low Word
    LOAD_POWER_L2_LOW = 651             # Load Side Phase B Power Low Word
    LOAD_POWER_L3_LOW = 652             # Load Side Phase C Power Low Word
    LOAD_POWER_TOTAL_LOW = 653          # Load Side Total Active Power Low Word
    LOAD_POWER_L1_HIGH = 656            # Load Side Phase A Power High Word
    LOAD_POWER_L2_HIGH = 657            # Load Side Phase B Power High Word
    LOAD_POWER_L3_HIGH = 658            # Load Side Phase C Power High Word
    LOAD_POWER_TOTAL_HIGH = 659         # Load Side Total Active Power High Word


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
    
    # SunSpec Model 713 (DER Storage Capacity) blocks
    MODEL_713_BATTERY_CAPACITY = "model_713_battery_capacity"
    MODEL_713_BATTERY_SOC = "model_713_battery_soc"
    MODEL_713_BATTERY_SOH = "model_713_battery_soh"
    
    # SunSpec Model 714 (DER DC Measurement) blocks
    MODEL_714_PV1_MEASUREMENTS = "model_714_pv1_measurements"
    MODEL_714_PV2_MEASUREMENTS = "model_714_pv2_measurements"
    MODEL_714_PV3_MEASUREMENTS = "model_714_pv3_measurements"
    MODEL_714_PV4_MEASUREMENTS = "model_714_pv4_measurements"
    MODEL_714_BATTERY1_MEASUREMENTS = "model_714_battery1_measurements"
    MODEL_714_BATTERY2_MEASUREMENTS = "model_714_battery2_measurements"


# Define the blocks of registers to be read for 3-phase Sol-Ark based on CSV mapping
SOLARK_3PHASE_READ_BLOCKS: List[ModbusReadBlock] = [
    # System status and configuration
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_TYPE_286,
        SolArk3PhaseRegisterMap.GRID_TYPE,
        1,
        "Grid Type (184)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.INVERTER_STATUS,
        SolArk3PhaseRegisterMap.OPERATION_STATUS,
        1,
        "Operation Status (500)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_STATUS_190,
        SolArk3PhaseRegisterMap.POWER_BUTTON_STATUS,
        1,
        "Power Button Status (551)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_INVERTER_150,
        SolArk3PhaseRegisterMap.AC_RELAY_STATUS,
        1,
        "AC Relay Status (552)"
    ),
    
    # Grid voltage measurements (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_3PHASE_VOLTAGES,
        SolArk3PhaseRegisterMap.GRID_VOLTAGE_L1N,
        3,  # Registers 598-600 (L1N, L2N, L3N)
        "Grid Phase Voltages (598-600)"
    ),
    
    # Grid frequency
    ModbusReadBlock(
        SolArk3PhaseBlockType.ENERGY,
        SolArk3PhaseRegisterMap.GRID_FREQUENCY,
        1,
        "Grid Frequency (609)"
    ),
    
    # Grid current measurements (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_3PHASE_CURRENTS,
        SolArk3PhaseRegisterMap.GRID_CT_CURRENT_L1,
        3,  # Registers 610-612 (L1, L2, L3)
        "Grid CT Currents (610-612)"
    ),
    
    # Grid power factor
    ModbusReadBlock(
        SolArk3PhaseBlockType.GRID_POWER_FACTOR_89,
        SolArk3PhaseRegisterMap.GRID_POWER_FACTOR,
        1,
        "Grid Power Factor (621)"
    ),
    
    # Grid power measurements L1 (32-bit values)
    ModbusReadBlock(
        SolArk3PhaseBlockType.POWER_BATTERY_170,
        SolArk3PhaseRegisterMap.GRID_POWER_L1_LOW,
        3,  # Registers 622-624 (L1, L2, L3 low words)
        "Grid Power Low Words (622-624)"
    ),
    
    # Grid total power (32-bit)
    ModbusReadBlock(
        SolArk3PhaseBlockType.APPARENT_POWER_38,
        SolArk3PhaseRegisterMap.GRID_TOTAL_POWER_LOW,
        1,
        "Grid Total Power Low (625)"
    ),
    
    # Grid power high words
    ModbusReadBlock(
        SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.GRID_POWER_L1_HIGH,
        4,  # Registers 687-690 (L1, L2, L3, Total high words)
        "Grid Power High Words (687-690)"
    ),
    
    # Grid apparent power (32-bit)
    ModbusReadBlock(
        SolArk3PhaseBlockType.CORRECTED_BATTERY_CAPACITY_107,
        SolArk3PhaseRegisterMap.GRID_APPARENT_POWER_LOW,
        1,
        "Grid Apparent Power Low (608)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.BATTERY_CAPACITY_204,
        SolArk3PhaseRegisterMap.GRID_APPARENT_POWER_HIGH,
        1,
        "Grid Apparent Power High (704)"
    ),
    
    # Grid reactive power (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.INVERTER_3PHASE_CURRENTS,
        SolArk3PhaseRegisterMap.GRID_REACTIVE_POWER_L1,
        3,  # Registers 710-712 (L1, L2, L3)
        "Grid Reactive Power (710-712)"
    ),
    
    # Temperature measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.TEMPERATURES,
        SolArk3PhaseRegisterMap.IGBT_TEMPERATURE,
        2,  # Registers 540-541 (IGBT, Heat Sink)
        "Temperatures (540-541)"
    ),
    
    # PV measurements (3 MPPT for 3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.PV_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV1_VOLTAGE,
        6,  # PV1-3 voltage and current (109-114)
        "PV 3-Phase Measurements (109-114)"
    ),
    
    # Legacy blocks for compatibility (using existing register definitions)
    ModbusReadBlock(
        SolArk3PhaseBlockType.PV_ENERGY,
        SolArk3PhaseRegisterMap.PV_ENERGY,
        1,
        "PV Energy (108)"
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
        SolArk3PhaseBlockType.DIAGNOSTICS,
        SolArk3PhaseRegisterMap.COMM_VERSION,
        6,
        "Diagnostics (2-7)"
    ),
    
    # SunSpec Model 713 (DER Storage Capacity) blocks
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_713_BATTERY_CAPACITY,
        SolArk3PhaseRegisterMap.BATTERY_CALCULATED_CAPACITY,
        1,
        "Battery Calculated Capacity (592)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_713_BATTERY_SOC,
        SolArk3PhaseRegisterMap.BATTERY_SOC,
        1,
        "Battery SOC (588)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_713_BATTERY_SOH,
        SolArk3PhaseRegisterMap.BATTERY_SOH,
        1,
        "Battery SOH (10006)"
    ),
    
    # SunSpec Model 714 (DER DC Measurement) blocks
    # PV1 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV1_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV1_POWER,
        1,
        "PV1 Power (672)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV1_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV1_VOLTAGE,
        2,  # Voltage and Current (676-677)
        "PV1 Voltage/Current (676-677)"
    ),
    
    # PV2 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV2_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV2_POWER,
        1,
        "PV2 Power (673)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV2_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV2_VOLTAGE,
        2,  # Voltage and Current (678-679)
        "PV2 Voltage/Current (678-679)"
    ),
    
    # PV3 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV3_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV3_POWER,
        1,
        "PV3 Power (674)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV3_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV3_VOLTAGE,
        2,  # Voltage and Current (680-681)
        "PV3 Voltage/Current (680-681)"
    ),
    
    # PV4 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV4_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV4_POWER,
        1,
        "PV4 Power (675)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_PV4_MEASUREMENTS,
        SolArk3PhaseRegisterMap.PV4_VOLTAGE,
        2,  # Voltage and Current (682-683)
        "PV4 Voltage/Current (682-683)"
    ),
    
    # Battery 1 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY1_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_1_VOLTAGE,
        1,
        "Battery 1 Voltage (587)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY1_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_1_POWER,
        2,  # Power and Current (590-591)
        "Battery 1 Power/Current (590-591)"
    ),
    
    # Battery 2 measurements
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY2_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_2_VOLTAGE,
        1,
        "Battery 2 Voltage (593)"
    ),
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY2_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_2_CURRENT,
        2,  # Current and Power (594-595)
        "Battery 2 Current/Power (594-595)"
    ),
    
    # Load voltage measurements (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.LOAD_VOLTAGE_L1N,
        3,  # Registers 644-646 (L1N, L2N, L3N)
        "Load Phase Voltages (644-646)"
    ),
    
    # Load frequency measurement (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.LOAD_FREQUENCY,
        1,  # Register 655
        "Load Frequency (655)"
    ),
    
    # Load power measurements low words (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.LOAD_POWER_L1_LOW,
        4,  # Registers 650-653 (L1, L2, L3, Total low words)
        "Load Power Low Words (650-653)"
    ),
    
    # Load power measurements high words (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.LOAD_3PHASE_MEASUREMENTS,
        SolArk3PhaseRegisterMap.LOAD_POWER_L1_HIGH,
        4,  # Registers 656-659 (L1, L2, L3, Total high words)
        "Load Power High Words (656-659)"
    ),
    
    # Battery 1 temperature (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY1_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_1_TEMPERATURE,
        1,  # Register 586
        "Battery 1 Temperature (586)"
    ),
    
    # Battery 2 temperature (3-phase)
    ModbusReadBlock(
        SolArk3PhaseBlockType.MODEL_714_BATTERY2_MEASUREMENTS,
        SolArk3PhaseRegisterMap.BATTERY_2_TEMPERATURE,
        1,  # Register 596
        "Battery 2 Temperature (596)"
    ),
]