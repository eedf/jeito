from rest_framework import serializers
from members.models import Adhesion, Nomination


class NominationSerializer(serializers.ModelSerializer):
    structure = serializers.CharField(source='structure.name')
    structure_type = serializers.CharField(source='structure.get_type_display')
    region = serializers.CharField(source='structure.region')
    function = serializers.CharField(source='function.code')

    class Meta:
        model = Nomination
        fields = ('structure', 'structure_type', 'region', 'function', 'main', 'is_responsible')


class AdhesionSerializer(serializers.ModelSerializer):
    number = serializers.CharField(source='person.number')
    first_name = serializers.CharField(source='person.first_name')
    last_name = serializers.CharField(source='person.last_name')
    gender = serializers.IntegerField(source='person.gender')
    email = serializers.CharField(source='person.email')
    structure = serializers.CharField(source='structure.name')
    structure_type = serializers.CharField(source='structure.get_type_display')
    region = serializers.CharField(source='structure.region')
    rate = serializers.CharField(source='rate.name')
    nominations = NominationSerializer(many=True)

    class Meta:
        model = Adhesion
        fields = (
            'number', 'first_name', 'last_name', 'gender', 'email',
            'structure', 'structure_type', 'region', 'rate', 'nominations',
            'adhesions_resp_email', 'structure_resp_email',
        )
