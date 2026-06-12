from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt  # modify - added
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
import tempfile
import os

from .models import BrandPortfolio, Product, Ingredient, AnalysisTask, UserSession
from .serializers import (
    BrandPortfolioSerializer, BrandPortfolioListSerializer,
    BrandPortfolioDetailSerializer, ProductSerializer, IngredientSerializer,
    AnalysisTaskSerializer, UserSessionSerializer, QuestionRequestSerializer,
    QuestionResponseSerializer, AnalysisInputSerializer
)
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin
from .tasks import analyze_portfolio_task
from .utils import ask_gemini_question

    
def ask_gemini_question(question, products, ingredients, brands):
    """
    Ask Gemini AI a question about the products from selected brands
    Returns: (answer, tokens_used)
    """
    import google.generativeai as genai
    from django.conf import settings
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Build context about the products
    products_context = "\n".join([
        f"- {p['name']} ({p['category']}): {p['description']}"
        for p in products
    ])
    
    ingredients_context = "\n".join([
        f"- {name}: {ing}"
        for name, ing in ingredients.items()
    ]) if ingredients else "No ingredient data available"
    
    # Build the prompt
    prompt = f"""You are a skincare expert assistant. Answer questions about these products from {', '.join(brands)}:

PRODUCTS:
{products_context}

INGREDIENTS:
{ingredients_context}

USER QUESTION: {question}

Please provide a helpful, accurate answer based only on the product information provided above. Do not mention products or brands not listed above."""
    
    try:
        response = model.generate_content(prompt)
        answer = response.text
        
        # Estimate tokens (rough approximation)
        tokens_used = len(prompt.split()) + len(answer.split())
        
        return answer, tokens_used
        
    except Exception as e:
        print(f"❌ Gemini API Error: {str(e)}")
        return f"Sorry, I couldn't answer that question. Error: {str(e)}", 0



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_admin_status(request):
    """Check if current user is admin/staff"""
    return Response({
        'is_admin': request.user.is_staff,
        'username': request.user.username,
        'email': request.user.email
    })

# modify # - Disable CSRF for public registration endpoint
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')

    if not all([username, email, password, password_confirm]):
        return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

    if password != password_confirm:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username, 'email': user.email}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
# modify #


class BrandPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = BrandPortfolioSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        return BrandPortfolio.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BrandPortfolioListSerializer
        elif self.action == 'retrieve':
            return BrandPortfolioDetailSerializer
        return BrandPortfolioSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def upload_and_analyze(self, request):
        import uuid
        import os
        
        UPLOAD_DIR = '/app/uploads'
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        serializer = AnalysisInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            portfolio = BrandPortfolio.objects.create(
                name=serializer.validated_data['brand_name'],
                description=serializer.validated_data.get('description', ''),
                created_by=request.user
            )
            
            pdf_file = serializer.validated_data['pdf_file']
            
            # Save to persistent directory (not /tmp)
            filename = f"{uuid.uuid4()}_{pdf_file.name}"
            pdf_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            
            print(f"✅ PDF saved: {pdf_path}")
            
            task = analyze_portfolio_task.delay(
                portfolio_id=portfolio.id,
                pdf_path=pdf_path,
                lookup_ingredients=serializer.validated_data['lookup_ingredients']
            )
            
            analysis_task = AnalysisTask.objects.create(
                task_id=task.id,
                portfolio=portfolio,
                status='pending'
            )
            
            return Response({
                'portfolio_id': portfolio.id,
                'task_id': task.id,
                'status': 'started',
                'message': f'Analysis started for {portfolio.name}'
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)





    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def analysis_tasks(self, request):
        tasks = AnalysisTask.objects.all().order_by('-created_date')
        serializer = AnalysisTaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_portfolios(self, request):
        portfolios = BrandPortfolio.objects.all()
        serializer = BrandPortfolioListSerializer(portfolios, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated, IsAdmin])
    def delete_portfolio(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        
        if not portfolio_id:
            return Response({'error': 'portfolio_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        portfolio = get_object_or_404(BrandPortfolio, id=portfolio_id)
        portfolio.delete()
        
        return Response({'message': f'Portfolio {portfolio.name} deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        portfolio_id = self.request.query_params.get('portfolio_id')
        if portfolio_id:
            return Product.objects.filter(portfolio_id=portfolio_id)
        return Product.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return Ingredient.objects.filter(product_id=product_id)
        return Ingredient.objects.all()


class UserSessionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get', 'post'])
    def selected_brands(self, request):
        session, created = UserSession.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = UserSessionSerializer(session)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            brand_ids = request.data.get('brand_ids', [])
            session.selected_portfolios.set(brand_ids)
            session.save()
            serializer = UserSessionSerializer(session)
            return Response(serializer.data)


    @action(detail=False, methods=['post'])
    def ask_question(self, request):
        serializer = QuestionRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            question = serializer.validated_data['question']
            brand_ids = serializer.validated_data.get('brand_ids', [])
            
            if not brand_ids:
                session, _ = UserSession.objects.get_or_create(user=request.user)
                brand_ids = list(session.selected_portfolios.values_list('id', flat=True))
            
            portfolios = BrandPortfolio.objects.filter(id__in=brand_ids)
            
            if not portfolios.exists():
                return Response({'error': 'No portfolios selected'}, status=status.HTTP_400_BAD_REQUEST)
            
            products_data = []
            ingredients_data = {}
            
            for portfolio in portfolios:
                for product in portfolio.products.all():
                    products_data.append({
                        'name': product.name,
                        'description': product.description,
                        'benefits': product.benefits,
                        'category': product.category,
                        'how_to_use': product.how_to_use
                    })
                    
                    # Combine all ingredient sources for this product
                    all_ingredients = []

                    # Add PDF ingredients from the Product model
                    if product.pdf_ingredients:
                        all_ingredients.append(product.pdf_ingredients)
                        
                    # Add ingredients from the Ingredient table (API sources, etc)
                    for ingredient in product.ingredients.all():
                        if ingredient.ingredients_list:
                            all_ingredients.append(ingredient.ingredients_list)

                    if all_ingredients:
                        combined = " | ".join(all_ingredients)  # Combine multiple sources
                        ingredients_data[product.name] = combined
            
            answer, tokens_used = ask_gemini_question(
                question=question,
                products=products_data,
                ingredients=ingredients_data,
                brands=[p.name for p in portfolios]
            )
            
            response_data = {
                'answer': answer,
                'brands_used': list(portfolios.values_list('name', flat=True)),
                'products_referenced': [p['name'] for p in products_data],
                'tokens_used': tokens_used
            }
            
            serializer = QuestionResponseSerializer(response_data)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
