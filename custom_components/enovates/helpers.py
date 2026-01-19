"""Helpers for Enovates integration."""

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from enovates_modbus.base import RegisterMap


class EnovatesDUCoordinator[T: RegisterMap](DataUpdateCoordinator[T]):
    """
    Enovates Data Update Coordinator.

    Exists for correct typing constraints only.
    """
