# ENIGMA MACHINE SIMULATOR

This app simulates coding and decoding of messages with an Enigma
machine in Python/Django. 

## URLS
Two URLS are available in this version: one to encode messages and
one to decode messages.

### Encoding
To encode messages, go to

    enigma/encode/<message>/<date>/<indicator_key>/<message_key>/

In future versions, this may be improved to include a POST message and a nice 
form, as that seems a more natural fit, but as a proof of concept this is
ok for now. 

An example would be:

    enigma/encode/hello/2021-12-19/anz/bnq/

This will result in a page displaying a message consisting of the
following parts (without brakcets):

    [AAA][BBB][MESSAGE]

where:
- AAA is the indicator key, encrypted using the day indicator and rotor 
  settings.
- BBB is the message key, encrypted using the indicator key and the rotor  
  settings of the day.
- MESSAGE is the message, encrypted using the message key and rotor settings
  of the day.

### Decoding

To decode a message, go to:

    enigma/decode/<message>/<date>/

This will decrypt the message using the date settings for that day and the
indicator and message indicators that were included the message. This message
thus needs to include the [AAA] and [BBB] parts.