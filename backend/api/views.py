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
from .agents import Agent4Answerer


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
            
            # Get brand names for Agent 4
            brand_names = list(portfolios.values_list('name', flat=True))
            
            # Import Agent 4
            from .agents import Agent4Answerer
            import os
            
            # Initialize Agent 4
            openai_api_key = os.getenv("OPENAI_API_KEY")
            answerer = Agent4Answerer(
                chroma_db_path="/app/chroma_db",
                openai_api_key=openai_api_key
            )
            
            print(f"🤖 Agent 4 answering question: {question}")
            print(f"📚 Using brands: {brand_names}")
            
            # Use Agent 4 to answer
            answer, products_used = answerer.answer_question(
                question=question,
                brand_names=brand_names,
                top_k=5,
                use_web_search=False  # Set to True if you want web search
            )
            
            # Get product names
            product_names = [p['metadata'].get('product', 'Unknown') for p in products_used]
            
            response_data = {
                'answer': answer,
                'brands_used': brand_names,
                'products_referenced': product_names,
                'tokens_used': len(question.split()) + len(answer.split())  # Rough estimate
            }
            
            print(f"✅ Agent 4 response: {len(answer)} chars, {len(products_used)} products used")
            
            serializer = QuestionResponseSerializer(response_data)
            return Response(serializer.data)
        
        except Exception as e:
            import traceback
            print(f"❌ Error in ask_question: {str(e)}")
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)