from django.contrib import admin
from .models import BrandPortfolio, Product, Ingredient, AnalysisTask, UserSession


@admin.register(BrandPortfolio)
class BrandPortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_date', 'total_products', 'products_with_ingredients']
    list_filter = ['created_date', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_date', 'updated_date']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Metadata', {
            'fields': ('total_products', 'products_with_ingredients', 'analysis_file'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )


class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 0
    readonly_fields = ['source', 'found_date']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'portfolio', 'category', 'has_ingredients']
    list_filter = ['portfolio', 'category']
    search_fields = ['name', 'description']
    inlines = [IngredientInline]
    
    def has_ingredients(self, obj):
        return hasattr(obj, 'ingredient')
    has_ingredients.short_description = 'Has Ingredients'
    has_ingredients.boolean = True


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['product', 'source', 'barcode', 'quality_score', 'found_date']
    list_filter = ['source', 'found_date']
    search_fields = ['product__name', 'barcode']
    readonly_fields = ['found_date']


@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'portfolio', 'status', 'progress', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['task_id', 'portfolio__name']
    readonly_fields = ['task_id', 'created_date', 'completed_date']
    
    def has_add_permission(self, request):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'num_selected_portfolios', 'updated_date']
    list_filter = ['updated_date']
    search_fields = ['user__username']
    readonly_fields = ['user', 'updated_date']
    
    def num_selected_portfolios(self, obj):
        return obj.selected_portfolios.count()
    num_selected_portfolios.short_description = 'Selected Portfolios'
    
    def has_add_permission(self, request):
        return False
