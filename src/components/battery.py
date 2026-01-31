"""
Battery Storage Model
Manages charge/discharge cycles, state of charge, and capacity limits.
"""


class Battery:
    """
    Represents a DC-coupled battery storage system.

    Attributes:
        capacity_wh: Total energy capacity in watt-hours
        current_charge_wh: Current stored energy in watt-hours
        max_charge_rate_w: Maximum charging power in watts
        max_discharge_rate_w: Maximum discharge power in watts
    """

    def __init__(
        self,
        capacity_wh: float,
        initial_charge_wh: float,
        max_charge_rate_w: float,
        max_discharge_rate_w: float,
        min_soc: float = 0.0,
        max_soc: float = 1.0
    ):
        """
        Initialize a battery storage system.

        Args:
            capacity_wh: Total capacity in watt-hours
            initial_charge_wh: Starting charge level
            max_charge_rate_w: Maximum charge power in watts
            max_discharge_rate_w: Maximum discharge power in watts
            min_soc: Minimum state of charge (0.0 to 1.0)
            max_soc: Maximum state of charge (0.0 to 1.0)
        """
        self.capacity_wh = capacity_wh
        self.current_charge_wh = min(initial_charge_wh, capacity_wh)
        self.max_charge_rate_w = max_charge_rate_w
        self.max_discharge_rate_w = max_discharge_rate_w
        self.min_soc = min_soc
        self.max_soc = max_soc

    def state_of_charge(self) -> float:
        """
        Calculate current state of charge as a percentage.

        Returns:
            State of charge (0.0 to 1.0)
        """
        return self.current_charge_wh / self.capacity_wh

    def available_charge_capacity(self) -> float:
        """
        Calculate how much more energy can be stored.

        Returns:
            Available capacity in watt-hours
        """
        max_charge = self.capacity_wh * self.max_soc
        return max(0.0, max_charge - self.current_charge_wh)

    def available_discharge_capacity(self) -> float:
        """
        Calculate how much energy can be discharged.

        Returns:
            Available discharge in watt-hours
        """
        min_charge = self.capacity_wh * self.min_soc
        return max(0.0, self.current_charge_wh - min_charge)

    def can_charge(self, power_w: float, duration_s: float = 60) -> bool:
        """
        Check if battery can accept charge at given power.

        Args:
            power_w: Charging power in watts
            duration_s: Duration in seconds (default 60s = 1 minute)

        Returns:
            True if battery can accept this charge
        """
        if power_w > self.max_charge_rate_w:
            return False

        energy_wh = (power_w * duration_s) / 3600.0
        return energy_wh <= self.available_charge_capacity()

    def can_discharge(self, power_w: float, duration_s: float = 60) -> bool:
        """
        Check if battery can provide discharge at given power.

        Args:
            power_w: Discharge power in watts
            duration_s: Duration in seconds (default 60s = 1 minute)

        Returns:
            True if battery can provide this discharge
        """
        if power_w > self.max_discharge_rate_w:
            return False

        energy_wh = (power_w * duration_s) / 3600.0
        return energy_wh <= self.available_discharge_capacity()

    def charge(self, power_w: float, duration_s: float = 60) -> float:
        """
        Charge the battery for a given duration.

        Args:
            power_w: Charging power in watts
            duration_s: Duration in seconds (default 60s = 1 minute)

        Returns:
            Actual energy charged in watt-hours
        """
        # Limit by charge rate
        actual_power = min(power_w, self.max_charge_rate_w)

        # Calculate energy
        energy_wh = (actual_power * duration_s) / 3600.0

        # Limit by available capacity
        energy_wh = min(energy_wh, self.available_charge_capacity())

        # Update charge
        self.current_charge_wh += energy_wh

        return energy_wh

    def discharge(self, power_w: float, duration_s: float = 60) -> float:
        """
        Discharge the battery for a given duration.

        Args:
            power_w: Discharge power in watts
            duration_s: Duration in seconds (default 60s = 1 minute)

        Returns:
            Actual energy discharged in watt-hours
        """
        # Limit by discharge rate
        actual_power = min(power_w, self.max_discharge_rate_w)

        # Calculate energy
        energy_wh = (actual_power * duration_s) / 3600.0

        # Limit by available discharge
        energy_wh = min(energy_wh, self.available_discharge_capacity())

        # Update charge
        self.current_charge_wh -= energy_wh

        return energy_wh

    def __repr__(self) -> str:
        return (
            f"Battery(capacity={self.capacity_wh}Wh, "
            f"charge={self.current_charge_wh:.1f}Wh, "
            f"SOC={self.state_of_charge():.1%})"
        )
