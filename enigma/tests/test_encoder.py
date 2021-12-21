from django.test import TestCase

from enigma import encoder


class EncoderTestCase(TestCase):

    def test_is_encodable(self):
        """ Strings containing only alphabetic characters are encodable;
         numeral, characters, and empty strings are not."""
        self.assertTrue(
            encoder._is_encodable("A"),
            "An uppercase letter should be encodable.")
        self.assertTrue(
            encoder._is_encodable("a"),
            "A lowercase letter should be encodable.")
        self.assertTrue(
            encoder._is_encodable("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "A string containing all possible uppercase letters should be "
            "encodable.")
        self.assertTrue(
            encoder._is_encodable("abcdefghijklmnopqrstuvw"),
            "A string containing all possible lowercase letters should be "
            "encodable.")
        self.assertFalse(
            encoder._is_encodable("A1"),
            "A string containing a number should not be encodable.")
        self.assertFalse(
            encoder._is_encodable(""),
            "An empty string should not be encodable.")

    def test_substitute(self):
        """ Plugs should switch letters in a string. """
        plugs = ["AE", "BQ", "RS"]
        message = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.assertEqual(
            "EQCDAFGHIJKLMNOPBSRTUVWXYZ", encoder.substitute(message, plugs),
            "The provided plugs should cause A and E, B and Q and R and S to "
            "flip positions.")
        self.assertEqual(
            message, encoder.substitute(message, []),
            "If there are no plugs, there should be no flips.")
        self.assertEqual(
            "", encoder.substitute("", []),
            "If there is no message, there should be no flips.")

    def test_char_to_int(self):
        """ Char to int should return an index from 0 to 25 for each letter
        in the alphabet. """
        self.assertEqual(
            0, encoder._char_to_int("A"),
            "An A should have index 0.")
        self.assertEqual(0, encoder._char_to_int("a"))
        self.assertEqual(25, encoder._char_to_int("Z"))
        self.assertEqual(25, encoder._char_to_int("z"))

    def test_find_rotor_offset(self):
        """ _find_rotor_offset should find the index for the rotation of the
        rotor. """
        rotor = "EKMFLGDQVZNTOWYHXUSPAIBRCJ"
        self.assertEqual(
            19, encoder._find_rotor_offset(rotor, "P"),
            "The P is displayed as the 19th char in the rotor string")
        self.assertEqual(
            -1, encoder._find_rotor_offset("", "A"),
            "The function should return -1 if the string does not exist in"
            "the rotor string.")

    def test_reverse_encode_char(self):
        """ _reverse_encode_char should provide the input character on the
        rotor that causes the rotor to ouput the output character."""
        rotor = "EKMFLGDQVZNTOWYHXUSPAIBRCJ"
        self.assertEqual(
            "A", encoder._reverse_encode_rotor("E", rotor, 0),
            "If the rotor is not rotated, it should output an 'E' if the input "
            "is 'A'.")
        self.assertEqual(
            "Z", encoder._reverse_encode_rotor("E", rotor, 1),
            "If the rotor is rotated one position, it should output an 'E' if "
            "the input is 'Z'.")
        self.assertEqual(
            "B", encoder._reverse_encode_rotor("E", rotor, 25),
            "If the rotor is rotated to the last position, it should output an "
            "'E' if the input is 'B'.")
        self.assertEqual(
            "Z", encoder._reverse_encode_rotor("J", rotor, 0),
            "If the rotor is not rotated, it should output a 'J' if the input "
            "is 'Z'.")
        self.assertEqual(
            "Y", encoder._reverse_encode_rotor("J", rotor, 1),
            "If the rotor is rotated one position, it should output a 'J' if "
            "the input is 'Y'.")
        self.assertEqual(
            "A", encoder._reverse_encode_rotor("J", rotor, 25),
            "If the rotor is rotated to the last position, it should output a "
            "'J' if the input is 'A'.")

    def test_advance_rotors(self):
        """ Rightmost rotor should always advance, other rotors should
        advance when the rotor to their right is in its notch position. """
        rotor_data = []
        # Add a left rotor that has its notch at the J position (9) and is
        # not rotated in any way
        rotor_data.append(("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["J"], 0))
        # Add a right rotor that has its notch at the K position (1) and is
        # not rotated in any way
        rotor_data.append(("EKMFLGDQVZNTOWYHXUSPAIBRCJ", ["K"], 0))

        # Base tests
        self.assertEqual(
            0, rotor_data[0][2],
            "Leftmost rotor starts at position 0")
        self.assertEqual(
            0, rotor_data[1][2],
            "Rightmost rotor starts at position 0.")

        rotor_data = encoder._advance_rotors(rotor_data)

        self.assertEqual(
            0, rotor_data[0][2],
            "Leftmost rotor remains at position 0, as the rightmost rotor "
            "did not hit its notch.")
        self.assertEqual(
            1, rotor_data[1][2],
            "Rightmost rotor is now at position 1, as it always advances.")

        rotor_data = encoder._advance_rotors(rotor_data)

        self.assertEqual(
            1, rotor_data[0][2],
            "Leftmost rotor should now be at position 1, "
            "as the rightmost rotor hit its notch.")
        self.assertEqual(
            2, rotor_data[1][2],
            "Rightmost rotor is now at position 2, as it always advances.")

    def test_encode_char(self):
        """ Encode char encodes a character through a provide set of rotor
        settings. """
        # Simple test: two rotors that don't encode anything. The rotors will
        # only advance when they hit Z.
        rotor_settings = \
            [
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0),
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0)
            ]
        reflector = "ZYXWVUTSRQPONMLKJIHGFEDCBA"
        self.assertEqual(
            "Z", encoder._encode_char("A", rotor_settings, reflector),
            "The only rotor changing the letter is the reflector, so it should"
            " return 'Z'.")
        self.assertEqual(
            "A", encoder._encode_char("Z", rotor_settings, reflector),
            "Reverse encoding the 'Z' should again yield the 'A'.")

        # Simulate that the right rotor has moved one step.
        rotor_settings = \
            [
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0),
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 1)
            ]
        self.assertEqual(
            "X", encoder._encode_char("A", rotor_settings, reflector),
            "The rightmost rotor is offset by one notch, and the reflector "
            "mirrors the letter. Then signal goes offset rotor again, shifting "
            "the letter again, so this should be an 'X'.")
        self.assertEqual(
            "A", encoder._encode_char("X", rotor_settings, reflector),
            "Reverse encoding the 'X' should again yield the 'A'.")

        rotor_settings = \
            [
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0),
                ("BCDEFGHIJKLMNOPQRSTUVWXYZA", [], 0)
            ]
        self.assertEqual(
            "X", encoder._encode_char("A", rotor_settings, reflector),
            "This is the same setting as above, but the offset has now been "
            "hardcoded in the rightmost rotor setting. Therefore it should "
            "yield the same result.")
        self.assertEqual(
            "A", encoder._encode_char("X", rotor_settings, reflector),
            "Reverse encoding the 'X' should again yield the 'A'.")

    def test_rotor_encode(self):
        """ Rotor encodes advances rotors and encodes chars. """
        rotor_settings = \
            [
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0),
                ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [], 0)
            ]
        reflector = "ZYXWVUTSRQPONMLKJIHGFEDCBA"

        test_message = "THEQUICKFOXJUMPSOVERTHELAZYDOG"
        self.assertEqual(
            "EOPBVFJZCRGSFLGBDUJUQABSBAZSFL",
            encoder.rotor_encode(test_message, "AA", rotor_settings, reflector),
            "The reverse of T is G. However, the rotor moves before encoding, "
            "so the new character is offset by 2 places, resulting in E. The "
            "reverse of H is S, however there rotor has now moved twice, so "
            "it will become O, etc."
        )
        self.assertEqual(
            test_message,
            encoder.rotor_encode("EOPBVFJZCRGSFLGBDUJUQABSBAZSFL", "AA",
                                 rotor_settings, reflector),
            "Reversing an encoding with the same settings should return the "
            "original message.")