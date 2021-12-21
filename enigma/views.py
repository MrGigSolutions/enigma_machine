import datetime
from typing import List, OrderedDict, Dict, Optional

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

import requests

from .encoder import rotor_encode, substitute
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


def _find_rotor_data(rotors: List, name: str) -> (str, List):
    """ Looks through the rotor serializers to """
    for rotor in rotors:
        if rotor['name'] == name:
            return rotor['sequence'], rotor.get('notch_set', [])
    raise RotorNotFoundError


def _get_rotor_info():
    """ Looks up the rotor information for the specified date"""
    # TODO: Request string is hard coded. Should be configurable.
    rotor_response = requests.get(ROTOR_ENDPOINT)
    rotors = RotorSerializer(data=rotor_response.json(), many=True)
    if rotors.is_valid():
        return rotors.validated_data
    raise RotorInformationNotFoundError


def _get_codebook_setting(date: datetime.date, rotor_info: List) \
        -> Optional[Dict]:
    """
    Retrieves codebook settings from the code book.
    :param date: The date for which to retrieve code book settings
    :return: A dictionary containing codebook settings, with the following
    data:<br />
    - rotor_data: a list of tuples where the first member is the sequence
    string, and the second member is a list of notches<br/>
    - plug_settings: a list of 2 letter strings with plug subsitutions<br />
    - day_indicator: the default encoding indicator for that day.
    Message indicators are encoded using that indicator.<br />
    - reflector: the reflector sequence string.
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
    for codebook in codebooks:
        rotor_settings = codebook['rotors']

        # We'll now retrieve the rotor data. The raw information was
        result = dict()
        result['rotor_data'] = \
            [rs for rs in map(
                lambda r: _find_rotor_data(rotor_info, r),
                rotor_settings)]
        result['plug_settings'] = codebook['plug_settings_set']
        result['day_indicator'] = codebook['indicator']
        result['reflector'] = \
            _find_rotor_data(rotor_info, codebook['reflector'])[0]

        return result


def _decode(message: str, codebook_data: Dict) -> str:
    """ Decodes a message given the provided codebook data.
    :param message: The message to decode.
    :param codebook_data: Codebooks settings and rotor information."""
    rotor_count = len(codebook_data['rotor_data'])
    # Consume the first prefix and decode using the day indicator.
    indicator_prefix = message.upper()[:rotor_count]
    indicator_indicator = rotor_encode(
        indicator_prefix, codebook_data['day_indicator'],
        codebook_data['rotor_data'], codebook_data['reflector'])
    indicator_indicator = substitute(
        indicator_indicator, codebook_data['plug_settings'])

    # Consume the second prefix and decode using the first indicator.
    message_prefix = message.upper()[rotor_count:2 * rotor_count]
    message_indicator = rotor_encode(
        message_prefix, indicator_indicator, codebook_data['rotor_data'],
        codebook_data['reflector'])
    message_indicator = substitute(
        message_indicator, codebook_data['plug_settings'])

    # Finally, decode the message itself using the message indicator.
    new_message = message.upper()[2 * rotor_count:]
    new_message = rotor_encode(
        new_message, message_indicator, codebook_data['rotor_data'],
        codebook_data['reflector'])
    new_message = substitute(new_message, codebook_data['plug_settings'])
    return new_message


def _encode(message: str, indicator_indicator: str, message_indicator: str,
            codebook_data: Dict) -> str:
    """ Encodes a message using the provided indicator and codebook data.
    :param message: The message to encode.
    :param indicator_indicator: The indicator settings to use to encode the
    message_indicator.
    :param message_indicator: The indicator settings to use to encode the
    message.
    :param codebook_data: Codebooks settings and rotor information.
    """

    # Create a prefix for the message that indicates the indicator encoder
    indicator_prefix = substitute(
        indicator_indicator.upper(), codebook_data['plug_settings'])
    indicator_prefix = rotor_encode(
        indicator_prefix, codebook_data['day_indicator'],
        codebook_data['rotor_data'], codebook_data['reflector'])

    message_prefix = substitute(
        message_indicator.upper(), codebook_data['plug_settings'])
    message_prefix = rotor_encode(
        message_prefix, indicator_indicator, codebook_data['rotor_data'],
        codebook_data['reflector'])

    new_message = substitute(
        message.upper(), codebook_data['plug_settings'])
    new_message = rotor_encode(
        new_message, message_indicator, codebook_data['rotor_data'],
        codebook_data['reflector'])

    # add the prefix before the message
    return f'{indicator_prefix}{message_prefix}{new_message}'


def decode_view(request, message: str, date: datetime.date):
    """ This view decodes a message in the url using the settings of the
    provided date."""
    rotor_info = _get_rotor_info()
    codebook_data = _get_codebook_setting(date, rotor_info)
    return HttpResponse(_decode(message, codebook_data))


def encode_view(request, message: str, date: datetime.date,
                indicator_indicator: str, message_indicator: str):
    """ This view encodes a message using the codebook settings on the
    provided date, an indicator to encode the message, and a separate
     indicator te encode the message indicator."""
    rotor_info = _get_rotor_info()
    codebook_data = _get_codebook_setting(date, rotor_info)
    return HttpResponse(
        _encode(message, indicator_indicator, message_indicator, codebook_data))
