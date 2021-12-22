import re
from dataclasses import dataclass

# Don't like running in global, but this allows us to compile it once for
# performance if we need to test many messages.
_alphabetic = re.compile(r'^[A-Za-z]+$')


@dataclass
class RotorInfo:
    """ Build details of a rotor """
    name: str
    sequence: str
    notches: list[str]


@dataclass
class RotorSetting:
    """ Details about the setting of a specific rotor """
    sequence: str
    notches: list[str]
    offset: int


@dataclass
class EnigmaSetting:
    """
    Settings to encode an enigma message.
    """
    # A list with the rotor's connector sequence, notches and offset
    rotors: list[RotorSetting]
    # A list with 2 letter strings, indicating plugboard settings
    plugs: list[str]
    # Connector sequence of the reflector
    reflector: str

    @classmethod
    def with_indicator(cls, setting: 'EnigmaSetting', indicator: str):
        """ Creates a new enigma setting with a different indicator but
        same rotors and plugs. """
        rotor_settings = list[RotorSetting]()
        rotor_index = 0
        for rotor in setting.rotors:
            offset = find_rotor_offset(indicator[rotor_index], rotor.sequence)
            rotor_settings.append(
                RotorSetting(rotor.sequence, rotor.notches, offset))
            rotor_index += 1
        return EnigmaSetting(rotor_settings, setting.plugs, setting.reflector)


class UnencodableMessageError(ValueError):
    """ This error is raised when a message cannot be encoded by Enigma. """
    pass


def _is_encodable(message: str) -> bool:
    """ Checks that message contains only characters that Enigma can handle. """
    if re.match(_alphabetic, message) is None:
        return False
    return True


def _substitute(message: str, setting: EnigmaSetting) -> str:
    """ Substitutes letters in a message using the provided plugboard
    settings.
    :param message: The message in which to change plug settings.
    :param setting: The settings of the Enigma machine.
    """
    if message is None:
        return ""

    substituted_message = ""
    for character in message:
        for plug in setting.plugs:
            if plug is None or len(plug) != 2:
                continue
            if character in plug:
                character = plug[1] if character == plug[0] else plug[0]
                break
        substituted_message += character
    return substituted_message


def _char_to_int(character: str):
    """ Returns a 0-based index of a character, A being 0 and Z being 25 """
    return ord(character.upper()) - 65


def _reverse_encode_rotor(character: str, rotor: RotorSetting) \
        -> str:
    """
    Finds the rotor input that causes the rotor to output character.
    :param character: Output character to find the input character for.
    :param rotor: Information about the build and current position of the
    rotor.
    """
    result = 0
    for r in rotor.sequence:
        if r == character:
            break
        result += 1
    return chr(((result - rotor.offset + 26) % 26) + 65)


def _advance_rotors(setting: EnigmaSetting) -> EnigmaSetting:
    """ Sets the rotors to their correct positions, where the rightmost rotor
    always advances. If the notches require it, left rotors also
    advance.
    :param setting: Setting of the enigma machine. """
    rotate_next_rotor = True

    rotor_infos = []
    for rotor in setting.rotors[::-1]:
        # The next rotor should rotate before decoding if its notch is
        # reached.
        rotor_offset = rotor.offset
        if rotate_next_rotor:
            # If the rotor is at its notch, we'll rotate the next
            # rotor as well.
            rotate_next_rotor = False
            for notch in rotor.notches:
                if find_rotor_offset(notch, rotor.sequence) == rotor.offset:
                    rotate_next_rotor = True
                    break
            rotor_offset = (rotor.offset + 1) % 26

        rotor_infos.insert(
            0, RotorSetting(rotor.sequence, rotor.notches, rotor_offset))

    return EnigmaSetting(rotor_infos, setting.plugs, setting.reflector)


def _encode_char(character: str, setting: EnigmaSetting):
    """ Encodes a character through the rotors in the Enigma machine,
    then the reflector, then back through the rotors.
    :param character: A character to encode through the Enigma rotor system
    :param setting: Current setting of the enigma machine. """
    new_char = character

    # The first rotor is the rightmost rotor. We'll now encode the
    # message through each rotor, using its offset.
    for rotor in setting.rotors[::-1]:
        index = (_char_to_int(new_char) + rotor.offset) % 26
        new_char = rotor.sequence[index]

    # We then need to reflect the message through the reflector
    new_char = setting.reflector[_char_to_int(new_char)]

    # Then we pass the message back through the rotors again, the
    # other way.
    for rotor in setting.rotors:
        new_char = _reverse_encode_rotor(new_char, rotor)

    return new_char


def _rotor_encode(
        message: str,
        setting: EnigmaSetting) -> str:
    """
    Encodes a message using an enigma machine.
    The message encoded using the provided setting.
    :param message: The message to encode. This is a string that only contains
    alphabet letters a-z. Case insensitive.
    :param setting: The settings to use to encode the message.
    """
    encoded_message = ""
    for char in message:
        setting = _advance_rotors(setting)
        encoded_message += _encode_char(char, setting)

    return encoded_message


def find_rotor_offset(character: str, sequence: str) -> int:
    """ Finds the rotor offset if the character displayed on the rotor's
    display is char.
    :param character: The character displayed on the rotor
    :param sequence: The rotor connection sequence.
    """
    index = 0
    for sequence_char in sequence:
        if sequence_char == character:
            return index
        index += 1
    return -1


def encode(
        message: str,
        setting: EnigmaSetting) -> str:
    """
    Encodes a message using an enigma machine.
    :param message: The message to encode. This is a string that only contains
    alphabet letters a-z. Case insensitive.
    :param setting: The settings to use to encode the message
    :raises UnencodableMessageError: If the message contains non-alphabetic
    characters.
    """
    if not _is_encodable(message):
        raise UnencodableMessageError()

    # Route the message through the plug board
    encoded_message = _substitute(message.upper(), setting)
    # Route the message through the rotors
    encoded_message = _rotor_encode(encoded_message, setting)
    # Then back through the plug board.
    encoded_message = _substitute(encoded_message, setting)

    return encoded_message
