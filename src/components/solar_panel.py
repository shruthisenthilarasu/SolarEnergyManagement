"""
Solar Panel Model
Simulates DC power output based on irradiance, capacity, and efficiency.
"""


class SolarPanel:
    """
    Represents a solar panel array with realistic power output modeling.

    Attributes:
        max_output_w: Maximum rated power output in watts (at 1.0 irradiance)
        current_irradiance: Current solar irradiance (0.0 to 1.0)
        efficiency: Panel efficiency factor (0.0 to 1.0)
    """

    def __init__(
        self,
        max_output_w: float,
        efficiency: float = 0.20,
        initial_irradiance: float = 0.0
    ):
        """
        Initialize a solar panel array.

        Args:
            max_output_w: Maximum power output in watts
            efficiency: Panel efficiency (default 20%, typical for commercial panels)
            initial_irradiance: Starting irradiance level (0.0 to 1.0)
        """
        self.max_output_w = max_output_w
        self.efficiency = efficiency
        self.current_irradiance = initial_irradiance

    def current_output(self) -> float:
        """
        Calculate current power output based on irradiance.

        Returns:
            Current power output in watts
        """
        return self.max_output_w * self.current_irradiance * self.efficiency

    def update_irradiance(self, irradiance: float) -> None:
        """
        Update the current irradiance level.

        Args:
            irradiance: New irradiance level (0.0 = night, 1.0 = peak sun)
        """
        self.current_irradiance = max(0.0, min(1.0, irradiance))

    def apply_degradation(self, degradation_factor: float) -> None:
        """
        Apply degradation to panel efficiency (e.g., dust, aging).

        Args:
            degradation_factor: Percentage reduction (0.0 to 1.0)
        """
        self.efficiency *= (1.0 - degradation_factor)
        self.efficiency = max(0.0, self.efficiency)

    def __repr__(self) -> str:
        return (
            f"SolarPanel(max={self.max_output_w}W, "
            f"efficiency={self.efficiency:.2%}, "
            f"irradiance={self.current_irradiance:.2f}, "
            f"current_output={self.current_output():.1f}W)"
        )
