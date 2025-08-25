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
    """Sol-Ark 3-phase specific data"""
    
    # Grid measurements (L1, L2, L3)
    grid_voltage: float = 0.0  # Legacy - will be set to grid_voltage_l1l2 for backward compatibility
    grid_voltage_l1l2: float = 0.0
    grid_voltage_l2l3: float = 0.0
    grid_voltage_l3l1: float = 0.0
    grid_voltage_l1n: float = 0.0
    grid_voltage_l2n: float = 0.0
    grid_voltage_l3n: float = 0.0
    grid_current_l1: float = 0.0
    grid_current_l2: float = 0.0
    grid_current_l3: float = 0.0
    grid_ct_current_l1: float = 0.0
    grid_ct_current_l2: float = 0.0
    grid_ct_current_l3: float = 0.0
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
    
    # PV measurements (3 MPPT inputs for 3-phase)
    pv1_power: float = 0.0
    pv2_power: float = 0.0
    pv3_power: float = 0.0
    pv1_voltage: float = 0.0
    pv1_current: float = 0.0
    pv2_voltage: float = 0.0
    pv2_current: float = 0.0
    pv3_voltage: float = 0.0
    pv3_current: float = 0.0
    
    def get_phase_count(self) -> int:
        return 3
    
    def get_inverter_type(self) -> str:
        return "solark_3phase"