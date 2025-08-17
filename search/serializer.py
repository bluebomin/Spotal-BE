from rest_framework import serializers
from .models import SeaerchShop

class SearchShopSerializer(serializers.ModelSerializer):
    
    
    class Meta:
        model = SeaerchShop
        fields = ['shop_id', 'emotion','name', 'address', 'status', 'uptaenm']
        read_only_fields = ['shop_id']
    
   