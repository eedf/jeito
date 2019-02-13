from rest_framework import serializers
from members.models import Adhesion


class AdhesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adhesion
        fields = ('person', 'structure')
