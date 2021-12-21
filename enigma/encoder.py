import re

from typing import List

# Don't like running in global, but this allows us to compile it once for
# performance if we need to test many messages.
_alphabetic = re.compile(r'^[A-Za-z]+$')


class UnencodableMessageError(ValueError):
    """ This error is raised when a message cannot be encoded by Enigma. """
    pass


def _is_encodable(message: str) -> bool:
    """ Checks that message contains only characters that Enigma can handle. """
    if re.match(_alphabetic, message) is None:
        return False
    return True


def substitute(message: str, plugs: List) -> str:
    """ Substitutes letters in a message using the provided plugboard
    settings.
    :param message: The message in which to change plug settings.
    :param plugs: The plug settings to use, is a list of 2-character strings.
    """

    if message is None:
        return ""

    substituted_message = ""
    for character in message:
        for plug in plugs:
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


def _find_rotor_offset(rotor_string: str, char: str) -> int:
    """ Finds the rotor offset if the character displayed on the rotor's
    display is char. """
    for r in range(len(rotor_string)):
        if rotor_string[r] == char:
            return r
    return -1


def _reverse_encode_rotor(character: str, rotor_string: str, offset: int) \
        -> str:
    """ Finds the rotor input that causes the rotor to output character. """
    result = 0
    for r in rotor_string:
        if r == character:
            break
        result += 1
    return chr(((result - offset + 26) % 26) + 65)


def _advance_rotors(rotor_data: List) -> List:
    """ Sets the rotors to their correct positions, where the right most rotor
    always advances. If the notches require it, left rotors also
    advance. """
    rotate_next_rotor = True

    result = []
    for r in range(len(rotor_data) - 1, -1, -1):
        # The next rotor should rotate before decoding if its notch is
        # reached.
        rotor_string, rotor_notches, rotor_offset = rotor_data[r]

        if rotate_next_rotor:
            # If the rotor is at its notch, we'll rotate the next
            # rotor as well.
            rotate_next_rotor = False
            for notch in rotor_notches:
                if _char_to_int(_reverse_encode_rotor(notch, rotor_string, 0)) == rotor_offset:
                    rotate_next_rotor = True
                    break
            rotor_offset = (rotor_offset + 1) % 26

        result.insert(0, (rotor_string, rotor_notches, rotor_offset))

    return result


def _encode_char(char: str, rotors: List, reflector_string: str):
    """ Encodes a character through the rotors in the Enigma machine,
    then the reflector, then back through the rotors.
    :param char: A character to encode through the Enigma rotor system
    :param rotors: List containing 3-tuples, where the first member is the
    rotor string, the second member indicates the notches, and the third
    member contains its current offset.
    :param reflector_string: The reflector disk that is used."""
    new_char = char

    # The first rotor is the rightmost rotor. We'll now encode the
    # message through each rotor, using its offset.
    for a in range(len(rotors) - 1, -1, -1):
        rotor_string, _, rotor_offset = rotors[a]
        index = (_char_to_int(new_char) + rotor_offset) % 26
        new_char = rotor_string[index]

    # We then need to reflect the message through the reflector
    new_char = reflector_string[_char_to_int(new_char)]

    # Then we pass the message back through the rotors again, the
    # other way.
    for a in range(len(rotors)):
        rotor_string, _, rotor_offset = rotors[a]
        new_char = _reverse_encode_rotor(
            new_char, rotor_string, rotor_offset)

    return new_char


def rotor_encode(
        message: str,
        indicator: str,
        rotors: List,
        reflector_string: str) -> str:
    """
    Encodes a message using an enigma machine.
    The message encoded using the provided indicator.
    :param message: The message to encode. This is a string that only contains
    alphabet letters a-z. Case insensitive.
    :param indicator: The indicator settings used to encode the message.
    :param rotors: The rotors to use for the encoding. Number of rotors
    must match the number of letters in the indicator.
    :param reflector_string: The reflector string, which ensures that messages
    can be decoded and also form the biggest weakness in Enigma.
    """
    encoded_message = ""
    rotors_with_offsets = [
        (rotors[r][0], rotors[r][1], _char_to_int(indicator[r]))
        for r in range(len(rotors))]
    for char in message:
        rotors_with_offsets = _advance_rotors(rotors_with_offsets)
        encoded_message += _encode_char(
            char, rotors_with_offsets, reflector_string)

    return encoded_message
