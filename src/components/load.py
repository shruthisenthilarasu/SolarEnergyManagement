"""
Load Model
Represents electrical loads with priority levels for intelligent shedding.
"""


class Load:
    """
    Represents an electrical load with priority-based control.

    Priority levels:
        0 = Critical (never shed if avoidable)
        1 = High (shed only when necessary)
        2 = Deferrable (shed first)

    Attributes:
        name: Human-readable load identifier
        power_draw_w: Power consumption in watts
        priority: Priority level (0-2)
        is_active: Current on/off state
    """

    def __init__(
        self,
        name: str,
        power_draw_w: float,
        priority: int = 2,
        is_active: bool = True
    ):
        """
        Initialize an electrical load.

        Args:
            name: Load identifier (e.g., "Medical Refrigeration")
            power_draw_w: Power consumption in watts
            priority: Priority level (0=critical, 1=high, 2=deferrable)
            is_active: Initial state (default True)
        """
        self.name = name
        self.power_draw_w = power_draw_w
        self.priority = priority
        self.is_active = is_active
        self._shed_count = 0  # Track how many times this load has been shed

    def activate(self) -> None:
        """Turn the load on."""
        self.is_active = True

    def deactivate(self) -> None:
        """Turn the load off (shed)."""
        self.is_active = False
        self._shed_count += 1

    def current_draw(self) -> float:
        """
        Get current power draw.

        Returns:
            Power draw in watts (0 if inactive)
        """
        return self.power_draw_w if self.is_active else 0.0

    def shed_count(self) -> int:
        """
        Get the number of times this load has been shed.

        Returns:
            Count of shedding events
        """
        return self._shed_count

    def priority_label(self) -> str:
        """
        Get human-readable priority label.

        Returns:
            Priority label string
        """
        labels = {0: "CRITICAL", 1: "HIGH", 2: "DEFERRABLE"}
        return labels.get(self.priority, "UNKNOWN")

    def __repr__(self) -> str:
        status = "ACTIVE" if self.is_active else "SHED"
        return (
            f"Load('{self.name}', {self.power_draw_w}W, "
            f"priority={self.priority_label()}, {status})"
        )

    def __lt__(self, other: 'Load') -> bool:
        """
        Comparison operator for sorting loads by priority.
        Higher priority number = shed first (deferrable before critical).
        """
        return self.priority > other.priority
