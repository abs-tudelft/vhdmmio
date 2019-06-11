from vhdmmio.core.field import FieldLogic, field_logic
from vhdmmio.core.accesscaps import AccessCapabilities

@field_logic('control')
class ControlField(FieldLogic):
    def __init__(self, dictionary):
        super().__init__(read_caps=AccessCapabilities(), write_caps=AccessCapabilities())

@field_logic('status')
class StatusField(FieldLogic):
    def __init__(self, dictionary):
        super().__init__(read_caps=AccessCapabilities())
