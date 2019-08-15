"""Submodule for interrupt field behavior."""

from .base import Behavior, behavior, BusAccessBehavior, BusBehavior
from ...config.behavior import Interrupt

@behavior(Interrupt)
class InterruptBehavior(Behavior):
    """Behavior class for interrupt fields."""

    def __init__(self, _, field, behavior_cfg, read_allow_cfg, write_allow_cfg):
        # TODO
        read_behavior = BusAccessBehavior(read_allow_cfg)
        write_behavior = BusAccessBehavior(write_allow_cfg)
        bus_behavior = BusBehavior(read_behavior, write_behavior, True)

        super().__init__(field, behavior_cfg, bus_behavior)
