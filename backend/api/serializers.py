from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BrandPortfolio, Product, Ingredient, AnalysisTask, UserSession


class BrandPortfolioListSerializer(serializers.ModelSerializer):
    """Simple list view of portfolios"""
    class Meta:
        model = BrandPortfolio
        fields = ['id', 'name', 'total_products', 'created_date']


class BrandPortfolioDetailSerializer(serializers.ModelSerializer):
    """Detailed portfolio with products"""
    products = serializers.SerializerMethodField()
    
    class Meta:
        model = BrandPortfolio
        fields = ['id', 'name', 'description', 'total_products', 'products_with_ingredients', 'created_date', 'products']
    
    def get_products(self, obj):
        products = obj.products.all()
        return ProductSerializer(products, many=True).data


class BrandPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandPortfolio
        fields = ['id', 'name', 'description', 'total_products', 'products_with_ingredients', 'created_date', 'updated_date']
        read_only_fields = ['created_date', 'updated_date']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'portfolio', 'name', 'description', 'category', 'benefits', 'how_to_use', 'pdf_ingredients']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'product', 'ingredients_list', 'source', 'barcode', 'quality_score', 'found_date']
        read_only_fields = ['found_date']


class AnalysisTaskSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(source='portfolio.name', read_only=True)
    
    class Meta:
        model = AnalysisTask
        fields = ['id', 'task_id', 'portfolio', 'portfolio_name', 'status', 'progress', 'current_step', 'error_message', 'created_date', 'completed_date']
        read_only_fields = ['created_date', 'completed_date']


class UserSessionSerializer(serializers.ModelSerializer):
    selected_portfolios = BrandPortfolioListSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserSession
        fields = ['id', 'selected_portfolios', 'updated_date']


class AnalysisInputSerializer(serializers.Serializer):
    """For PDF upload and analysis"""
    brand_name = serializers.CharField(max_length=255)
    pdf_file = serializers.FileField()
    lookup_ingredients = serializers.BooleanField(default=True)
    description = serializers.CharField(required=False, allow_blank=True)


class QuestionRequestSerializer(serializers.Serializer):
    """User question input"""
    question = serializers.CharField(max_length=5000)
    brand_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class QuestionResponseSerializer(serializers.Serializer):
    """AI response to question"""
    answer = serializers.CharField()
    brands_used = serializers.ListField(child=serializers.CharField())
    products_referenced = serializers.ListField(child=serializers.CharField())
    tokens_used = serializers.IntegerField()

class ProductIngredientsSerializer(serializers.Serializer):
    """Serializer for admin to manually edit product ingredients"""
    
    product_id = serializers.IntegerField()
    ingredients = serializers.CharField(max_length=5000)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_ingredients(self, value):
        """Validate ingredients aren't empty"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Ingredients must not be empty")
        return value