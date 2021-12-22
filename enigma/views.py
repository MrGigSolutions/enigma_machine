import datetime
from typing import List, OrderedDict, Dict, Optional

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

import requests

from . import encoder
from .serializers import RotorSerializer, SettingSerializer

ROTOR_ENDPOINT = 'http://localhost:8000/enigma/api/v1/rotors/'
CODEBOOK_ENDPOINT = 'http://localhost:8000/enigma/api/v1/codes/{date}/'


class RotorNotFoundError(ValueError):
    """ Error that fires when a rotor is looked up by name but is not
    stored in the code book."""
    pass


class CodebookSettingsInvalidError(ValueError):
    """ Occurs when codebook information cannot be deserialized. """
    pass


class RotorInformationNotFoundError(IOError):
    """ Occurs when rotor information could not be retrieved from the
     endpoint. """
    pass


class CodeBookSettingNotFoundError(IOError):
    """ Occurs when codebook information could not be retrieved from the
     endpoint. """
    pass


class MultipleCodeBookSettingFoundError(IOError):
    """ Occurs when multiple code books are found for a date. """
    pass


def _find_rotor_info(name: str, rotors: List[encoder.RotorInfo]) \
        -> encoder.RotorInfo:
    """ Looks through the rotor serializers to.
    :param name: Name of the rotor
    :param rotors: Build details of all rotors."""
    for rotor in rotors:
        if rotor.name == name:
            return rotor
    raise RotorNotFoundError


def _get_rotor_info() -> list[encoder.RotorInfo]:
    """ Looks up the rotor information for the specified date"""
    # TODO: Request string is hard coded. Should be configurable.
    rotor_response = requests.get(ROTOR_ENDPOINT)
    rotors = RotorSerializer(data=rotor_response.json(), many=True)
    result = list[encoder.RotorInfo]()
    if rotors.is_valid():
        rotor_data = rotors.validated_data
        for rotor in rotor_data:
            rotor_info = encoder.RotorInfo(
                rotor['name'], rotor['sequence'], rotor['notch_set'])
            result.append(rotor_info)

        return result
    raise RotorInformationNotFoundError


def _get_enigma_setting(
        date: datetime.date, rotor_infos: list[encoder.RotorInfo]) \
        -> encoder.EnigmaSetting:
    """
    Retrieves codebook settings from the code book.
    :param date: The date for which to retrieve code book settings
    :param rotor_infos:
    :return: An EnigmaSetting objects with a machine correctly configured.
    """
    # Retrieve code book settings
    # TODO: Request string is hard coded. Should be configurable.
    endpoint = CODEBOOK_ENDPOINT.format(date=date.strftime('%Y-%m-%d'))
    codebook_response = requests.get(endpoint)
    codebook_json = codebook_response.json()
    codebooks_serializer = SettingSerializer(data=codebook_json, many=True)
    if not codebooks_serializer.is_valid():
        raise CodebookSettingsInvalidError
    codebooks = codebooks_serializer.validated_data
    if codebooks is None or len(codebooks) == 0:
        raise CodeBookSettingNotFoundError
    if len(codebooks) != 1:
        raise MultipleCodeBookSettingFoundError
    codebook = codebooks[0]

    # We'll now retrieve the rotor data. The setting from the endpoint
    # only contains the name of the rotor, so we'll need to look it
    # up in the rotor_info.
    rotor_settings = list[encoder.RotorSetting]()
    rotor_index = 0
    for rotor in codebook['rotors']:
        rotor_info = _find_rotor_info(rotor, rotor_infos)
        # Find the offset based on the letter that it displays
        offset = encoder.find_rotor_offset(
            codebook['indicator'][rotor_index], rotor_info.sequence)
        rotor_settings.append(
            encoder.RotorSetting(
                rotor_info.sequence, rotor_info.notches, offset)
        )
        rotor_index += 1
    reflector = _find_rotor_info(codebook['reflector'], rotor_infos)

    result = encoder.EnigmaSetting(
        rotors=rotor_settings, plugs=codebook['plug_settings_set'],
        reflector=reflector.sequence)

    return result


def _decode(message: str, setting: encoder.EnigmaSetting) -> str:
    """ Decodes a message given the provided codebook data.
    :param message: The message to decode.
    :param setting: Enigma machine setting."""
    rotor_count = len(setting.rotors)
    # Consume the first prefix and decode using the day indicator.

    # This will decode the message indicator
    indicator_prefix = encoder.encode(message.upper()[:rotor_count], setting)

    # Consume the second prefix and decode using the first indicator.
    message_prefix = encoder.encode(
        message.upper()[rotor_count:2 * rotor_count],
        encoder.EnigmaSetting.with_indicator(setting, indicator_prefix))

    # Finally, decode the message itself using the message indicator.
    new_message = encoder.encode(
        message.upper()[2 * rotor_count:],
        encoder.EnigmaSetting.with_indicator(setting, message_prefix))
    return new_message


def _encode(message: str, indicator_indicator: str, message_indicator: str,
            day_setting: encoder.EnigmaSetting) -> str:
    """ Encodes a message using the provided indicator and codebook data.
    :param message: The message to encode.
    :param indicator_indicator: The indicator settings to use to encode the
    message_indicator.
    :param message_indicator: The indicator settings to use to encode the
    message.
    :param codebook_data: Codebooks settings and rotor information.
    """
    indicator_setting = encoder.EnigmaSetting.with_indicator(
        day_setting, indicator_indicator.upper())
    message_setting = encoder.EnigmaSetting.with_indicator(
        indicator_setting, message_indicator.upper())

    indicator_prefix = encoder.encode(
        indicator_indicator,
        day_setting)
    message_prefix = encoder.encode(
        message_indicator, indicator_setting)
    encoded_message = encoder.encode(message, message_setting)

    # Add the prefixes before the message
    return f'{indicator_prefix}{message_prefix}{encoded_message}'


def decode_view(request, message: str, date: datetime.date):
    """ This view decodes a message in the url using the settings of the
    provided date."""
    rotor_info = _get_rotor_info()
    setting = _get_enigma_setting(date, rotor_info)
    return HttpResponse(_decode(message, setting))


def encode_view(request, message: str, date: datetime.date,
                indicator_indicator: str, message_indicator: str):
    """ This view encodes a message using the codebook settings on the
    provided date, an indicator to encode the message, and a separate
     indicator te encode the message indicator."""
    rotor_info = _get_rotor_info()
    setting = _get_enigma_setting(date, rotor_info)
    return HttpResponse(
        _encode(message, indicator_indicator, message_indicator, setting))
