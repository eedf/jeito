from rest_framework import serializers
from members.models import Adhesion


class AdhesionSerializer(serializers.ModelSerializer):
    number = serializers.CharField(source='person.number')
    first_name = serializers.CharField(source='person.first_name')
    last_name = serializers.CharField(source='person.last_name')
    gender = serializers.IntegerField(source='person.gender')
    email = serializers.CharField(source='person.email')
    structure = serializers.CharField(source='structure.name')
    sla = serializers.CharField(source='structure.sla')
    region = serializers.CharField(source='structure.region')

    class Meta:
        model = Adhesion
        fields = ('number', 'first_name', 'last_name', 'gender', 'email', 'structure', 'sla', 'region')
