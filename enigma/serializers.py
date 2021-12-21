from rest_framework import serializers


class RotorSerializer(serializers.Serializer):
    """ Serializer for a rotor wheel. """

    name = serializers.CharField(max_length=255)
    sequence = serializers.CharField(max_length=26)
    notch_set = serializers.ListSerializer(
        child=serializers.CharField(max_length=1)
    )


class SettingSerializer(serializers.Serializer):
    """ Object that contains codebook settings. """

    date = serializers.DateField()
    rotors = serializers.ListSerializer(
        child=serializers.CharField(max_length=255)
    )
    plug_settings_set = serializers.ListSerializer(
        child=serializers.CharField(max_length=2)
    )
    indicator = serializers.CharField(max_length=5)
    reflector = serializers.CharField(max_length=255)

