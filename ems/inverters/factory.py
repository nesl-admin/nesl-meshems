"""
Inverter Factory

This module provides a factory for creating inverter clients based on configuration,
enabling support for multiple inverter types through a unified interface.
"""

import logging
from typing import Dict, Any, List, Type

from .base import InverterClient
from .solark_split_phase import SolArkSplitPhaseClient
from .solark_3phase import SolArk3PhaseClient


class InverterFactory:
    """Factory for creating inverter clients"""
    
    # Registry of supported inverter types
    INVERTER_TYPES: Dict[str, Type[InverterClient]] = {
        "solark_split_phase": SolArkSplitPhaseClient,
        "solark_3phase": SolArk3PhaseClient,
    }
    
    # Aliases for backward compatibility
    INVERTER_ALIASES: Dict[str, str] = {
        "sol-ark": "solark_split_phase",
        "solark_2phase": "solark_split_phase",
        "solark_splitphase": "solark_split_phase",
        "split-phase": "solark_split_phase",
        "solark_three_phase": "solark_3phase",
        "solark_threephase": "solark_3phase",
        "3-phase": "solark_3phase",
    }
    
    @classmethod
    def create_client(cls, config: Dict[str, Any]) -> InverterClient:
        """
        Create inverter client based on configuration
        
        Args:
            config: Configuration dictionary containing inverter and serial settings
            
        Returns:
            InverterClient: Configured inverter client instance
            
        Raises:
            ValueError: If inverter type is not supported
            KeyError: If required configuration is missing
        """
        logger = logging.getLogger(__name__)
        
        # Extract inverter configuration
        inverter_config = config.get("inverter", {})
        serial_config = config.get("serial", {})
        
        # Get inverter type with fallback to legacy configuration
        inverter_type = cls._get_inverter_type(config)
        
        # Resolve aliases
        if inverter_type in cls.INVERTER_ALIASES:
            resolved_type = cls.INVERTER_ALIASES[inverter_type]
            logger.info(f"Resolved inverter type alias '{inverter_type}' to '{resolved_type}'")
            inverter_type = resolved_type
        
        # Validate inverter type
        if inverter_type not in cls.INVERTER_TYPES:
            supported_types = list(cls.INVERTER_TYPES.keys()) + list(cls.INVERTER_ALIASES.keys())
            raise ValueError(f"Unsupported inverter type: '{inverter_type}'. Supported types: {supported_types}")
        
        # Get client class
        client_class = cls.INVERTER_TYPES[inverter_type]
        
        # Extract connection parameters
        port = serial_config.get("port")
        if not port:
            raise KeyError("Serial port not specified in configuration")
        
        baudrate = serial_config.get("baudrate", 9600)
        modbus_address = cls._get_modbus_address(config)
        
        # Create and return client instance
        logger.info(f"Creating {inverter_type} client on {port} at {baudrate} baud, address {modbus_address}")
        
        return client_class(
            port=port,
            baudrate=baudrate,
            modbus_address=modbus_address
        )
    
    @classmethod
    def _get_inverter_type(cls, config: Dict[str, Any]) -> str:
        """
        Get inverter type from configuration with fallback logic
        
        Args:
            config: Configuration dictionary
            
        Returns:
            str: Inverter type identifier
        """
        # Try new inverter.type configuration first
        inverter_config = config.get("inverter", {})
        if "type" in inverter_config:
            return inverter_config["type"]
        
        # Default fallback
        return "solark_split_phase"
    
    @classmethod
    def _get_modbus_address(cls, config: Dict[str, Any]) -> int:
        """
        Get Modbus address from configuration with fallback logic
        
        Args:
            config: Configuration dictionary
            
        Returns:
            int: Modbus slave address
        """
        # Try new inverter.modbus_address configuration first
        inverter_config = config.get("inverter", {})
        if "modbus_address" in inverter_config:
            return inverter_config["modbus_address"]
        
        # Default fallback
        return 1
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """
        Get list of supported inverter types
        
        Returns:
            List[str]: List of supported inverter type identifiers
        """
        return list(cls.INVERTER_TYPES.keys())
    
    @classmethod
    def get_supported_aliases(cls) -> Dict[str, str]:
        """
        Get dictionary of supported aliases and their resolved types
        
        Returns:
            Dict[str, str]: Dictionary mapping aliases to resolved types
        """
        return cls.INVERTER_ALIASES.copy()
    
    @classmethod
    def register_inverter_type(cls, type_name: str, client_class: Type[InverterClient]):
        """
        Register a new inverter type (for extensibility)
        
        Args:
            type_name: Unique identifier for the inverter type
            client_class: InverterClient subclass for this type
        """
        logger = logging.getLogger(__name__)
        
        if not issubclass(client_class, InverterClient):
            raise ValueError(f"Client class must be a subclass of InverterClient")
        
        cls.INVERTER_TYPES[type_name] = client_class
        logger.info(f"Registered new inverter type: {type_name}")
    
    @classmethod
    def register_alias(cls, alias: str, target_type: str):
        """
        Register a new alias for an existing inverter type
        
        Args:
            alias: Alias name
            target_type: Target inverter type that the alias resolves to
        """
        logger = logging.getLogger(__name__)
        
        if target_type not in cls.INVERTER_TYPES:
            raise ValueError(f"Target type '{target_type}' is not registered")
        
        cls.INVERTER_ALIASES[alias] = target_type
        logger.info(f"Registered new alias: '{alias}' -> '{target_type}'")
    
    @classmethod
    def validate_configuration(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate inverter configuration and return validation results
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Dict[str, Any]: Validation results with 'valid', 'errors', and 'warnings' keys
        """
        errors = []
        warnings = []
        
        # Check for required serial configuration
        serial_config = config.get("serial", {})
        if not serial_config.get("port"):
            errors.append("Serial port not specified")
        
        # Check inverter type
        try:
            inverter_type = cls._get_inverter_type(config)
            if inverter_type in cls.INVERTER_ALIASES:
                inverter_type = cls.INVERTER_ALIASES[inverter_type]
            
            if inverter_type not in cls.INVERTER_TYPES:
                errors.append(f"Unsupported inverter type: {inverter_type}")
        except Exception as e:
            errors.append(f"Error determining inverter type: {e}")
        
        # Check Modbus address
        try:
            modbus_address = cls._get_modbus_address(config)
            if not (1 <= modbus_address <= 247):
                warnings.append(f"Modbus address {modbus_address} is outside typical range (1-247)")
        except Exception as e:
            errors.append(f"Error determining Modbus address: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }