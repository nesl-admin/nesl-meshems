"""
Sol-Ark inverter data structures

This module defines data structures for different Sol-Ark inverter types,
including split-phase and 3-phase variants.
"""

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
    battery_empty_voltage: float = 0.0
    battery_shutdown_voltage: float = 0.0
    battery_restart_voltage: float = 0.0
    battery_low_voltage: float = 0.0
    battery_shutdown_percent: int = 0
    battery_restart_percent: int = 0
    battery_low_percent: int = 0
    
    # BMS variables
    bms_charging_voltage: float = 0.0
    bms_discharge_voltage: float = 0.0
    bms_charging_current_limit: float = 0.0
    bms_discharge_current_limit: float = 0.0
    bms_real_time_soc: float = 0.0
    bms_real_time_voltage: float = 0.0
    bms_real_time_current: float = 0.0
    bms_real_time_temp: float = 0.0
    bms_warning: int = 0
    bms_fault: int = 0
    
    # Timestamps
    last_update: float = field(default_factory=time.time)
    last_failure: float = 0.0


@dataclass
class SolArkSplitPhaseData(SolArkDataBase):
    """Sol-Ark split-phase specific data"""
    
    # Grid measurements (L1, L2)
    grid_voltage: float = 0.0  # Legacy - will be set to grid_voltage_l1l2 for backward compatibility
    grid_voltage_l1l2: float = 0.0  # Line1-to-Line2 voltage (register 152)
    grid_voltage_l1n: float = 0.0   # Line1-to-Neutral voltage (register 150)
    grid_voltage_l2n: float = 0.0   # Line2-to-Neutral voltage (register 151)
    grid_current_l1: float = 0.0
    grid_current_l2: float = 0.0
    grid_ct_current_l1: float = 0.0
    grid_ct_current_l2: float = 0.0
    grid_frequency: float = 0.0
    
    # Load measurements (L1, L2)
    load_power_l1: float = 0.0
    load_power_l2: float = 0.0
    load_current_l1: float = 0.0
    load_current_l2: float = 0.0
    load_frequency: float = 0.0
    
    # Inverter measurements (L1, L2)
    inverter_voltage: float = 0.0      # Line-to-Line voltage
    inverter_voltage_ln: float = 0.0   # Line1-to-Neutral voltage (VL1)
    inverter_voltage_l2n: float = 0.0  # Line2-to-Neutral voltage (VL2)
    inverter_current_l1: float = 0.0
    inverter_current_l2: float = 0.0
    inverter_frequency: float = 0.0
    inverter_power_l1: float = 0.0     # Line 1 power (WL1)
    inverter_power_l2: float = 0.0     # Line 2 power (WL2)
    
    # PV measurements (2 MPPT inputs)
    pv1_power: float = 0.0
    pv2_power: float = 0.0
    pv1_voltage: float = 0.0
    pv1_current: float = 0.0
    pv2_voltage: float = 0.0
    pv2_current: float = 0.0
    pv3_voltage: float = 0.0  # For compatibility with 3-phase
    pv3_current: float = 0.0  # For compatibility with 3-phase
    pv3_power: float = 0.0    # For compatibility with 3-phase
    
    def get_phase_count(self) -> int:
        return 2
    
    def get_inverter_type(self) -> str:
        return "solark_split_phase"


@dataclass
class SolArk3PhaseData(SolArkDataBase):
    """Sol-Ark 3-phase specific data with SunSpec Model 701 mappings"""
    
    # SunSpec Model 701 specific fields from CSV mapping
    power_button_status: int = 0       # Register 551 - Power Button Status
    
    # Grid measurements (L1, L2, L3) - from CSV mapping
    grid_voltage: float = 0.0  # Legacy - will be set to grid_voltage_l1l2 for backward compatibility
    grid_voltage_l1l2: float = 0.0     # Calculated from L1N * sqrt(3)
    grid_voltage_l2l3: float = 0.0     # Calculated from L2N * sqrt(3)
    grid_voltage_l3l1: float = 0.0     # Calculated from L3N * sqrt(3)
    grid_voltage_l1n: float = 0.0      # Register 598 - Grid Phase A Voltage
    grid_voltage_l2n: float = 0.0      # Register 599 - Grid Phase B Voltage
    grid_voltage_l3n: float = 0.0      # Register 600 - Grid Phase C Voltage
    grid_current_l1: float = 0.0       # Register 610 - Grid Internal CT Phase A Current
    grid_current_l2: float = 0.0       # Register 611 - Grid Internal CT Phase B Current
    grid_current_l3: float = 0.0       # Register 612 - Grid Internal CT Phase C Current
    grid_ct_current_l1: float = 0.0    # Register 610 - Grid Internal CT Phase A Current
    grid_ct_current_l2: float = 0.0    # Register 611 - Grid Internal CT Phase B Current
    grid_ct_current_l3: float = 0.0    # Register 612 - Grid Internal CT Phase C Current
    grid_frequency: float = 0.0        # Register 609 - Grid Frequency
    
    # Grid power measurements (3-phase) - from CSV mapping
    grid_power_l1: float = 0.0         # Registers 622/687 - Grid Side Phase A Power (32-bit)
    grid_power_l2: float = 0.0         # Registers 623/688 - Grid Side Phase B Power (32-bit)
    grid_power_l3: float = 0.0         # Registers 624/689 - Grid Side Phase C Power (32-bit)
    
    # Grid reactive power measurements (3-phase) - from CSV mapping
    grid_reactive_power_l1: float = 0.0    # Register 710 - Grid Phase A Reactive Power
    grid_reactive_power_l2: float = 0.0    # Register 711 - Grid Phase B Reactive Power
    grid_reactive_power_l3: float = 0.0    # Register 712 - Grid Phase C Reactive Power
    grid_reactive_power_total: float = 0.0 # Sum of L1, L2, L3 reactive power
    
    # Load measurements (L1, L2, L3) - from CSV mapping
    load_power_l1: float = 0.0
    load_power_l2: float = 0.0
    load_power_l3: float = 0.0
    load_current_l1: float = 0.0
    load_current_l2: float = 0.0
    load_current_l3: float = 0.0
    load_voltage_l1n: float = 0.0      # Register 644 - Load Phase A Voltage
    load_voltage_l2n: float = 0.0      # Register 645 - Load Phase B Voltage
    load_voltage_l3n: float = 0.0      # Register 646 - Load Phase C Voltage
    load_frequency: float = 0.0
    
    # Inverter measurements (L1, L2, L3) - placeholder for future implementation
    inverter_voltage: float = 0.0      # Line-to-Line voltage (L1-L2 for compatibility)
    inverter_voltage_l1l2: float = 0.0
    inverter_voltage_l2l3: float = 0.0
    inverter_voltage_l3l1: float = 0.0
    inverter_voltage_ln: float = 0.0   # Line1-to-Neutral voltage (VL1)
    inverter_voltage_l1n: float = 0.0  # Line1-to-Neutral voltage
    inverter_voltage_l2n: float = 0.0  # Line2-to-Neutral voltage
    inverter_voltage_l3n: float = 0.0  # Line3-to-Neutral voltage
    inverter_current_l1: float = 0.0
    inverter_current_l2: float = 0.0
    inverter_current_l3: float = 0.0
    inverter_frequency: float = 0.0
    inverter_power_l1: float = 0.0     # Line 1 power (WL1)
    inverter_power_l2: float = 0.0     # Line 2 power (WL2)
    inverter_power_l3: float = 0.0     # Line 3 power (WL3)
    
    # PV measurements (4 MPPT inputs for 3-phase) - from CSV Model 714 mapping
    pv1_power: float = 0.0             # Register 672 - PV1 Input Power
    pv2_power: float = 0.0             # Register 673 - PV2 Input Power
    pv3_power: float = 0.0             # Register 674 - PV3 Input Power
    pv4_power: float = 0.0             # Register 675 - PV4 Input Power
    pv1_voltage: float = 0.0           # Register 676 - PV1 Voltage
    pv1_current: float = 0.0           # Register 677 - PV1 Current
    pv2_voltage: float = 0.0           # Register 678 - PV2 Voltage
    pv2_current: float = 0.0           # Register 679 - PV2 Current
    pv3_voltage: float = 0.0           # Register 680 - PV3 Voltage
    pv3_current: float = 0.0           # Register 681 - PV3 Current
    pv4_voltage: float = 0.0           # Register 682 - PV4 Voltage
    pv4_current: float = 0.0           # Register 683 - PV4 Current
    
    # SunSpec Model 713 (DER Storage Capacity) fields - from CSV mapping
    battery_calculated_capacity: float = 0.0    # Register 592 - Battery 1 Calculated Capacity (Ah)
    battery_soc_713: float = 0.0               # Register 588 - Battery 1 SOC (%)
    battery_soh: float = 0.0                   # Register 10006 - Battery SOH (%)
    
    # SunSpec Model 714 (DER DC Measurement) battery fields - from CSV mapping
    battery_1_voltage: float = 0.0             # Register 587 - Battery 1 Voltage
    battery_1_current: float = 0.0             # Register 591 - Battery 1 Current (int16)
    battery_1_power: float = 0.0               # Register 590 - Battery 1 Output Power (int16)
    battery_1_temperature: float = 0.0         # Register 586 - Battery 1 Temperature
    battery_2_voltage: float = 0.0             # Register 593 - Battery 2 Voltage
    battery_2_current: float = 0.0             # Register 594 - Battery 2 Current (int16)
    battery_2_power: float = 0.0               # Register 595 - Battery 2 Output Power (int16)
    battery_2_temperature: float = 0.0         # Register 596 - Battery 2 Temperature
    
    def get_phase_count(self) -> int:
        return 3
    
    def get_inverter_type(self) -> str:
        return "solark_3phase"