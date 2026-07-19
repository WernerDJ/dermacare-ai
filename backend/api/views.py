from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings  
import logging
from django.views.decorators.http import require_POST
import uuid
import os
from pathlib import Path

from .models import BrandPortfolio, Product, AnalysisTask
from .tasks import analyze_portfolio_task
from .agents import Agent3Filter, Agent4Answerer

logger = logging.getLogger(__name__)

# Auth helpers
def is_admin(user):
    return user.is_staff

# ============ AUTH VIEWS ============

def login_view(request):
    """Login page"""
    import logging
    logger = logging.getLogger(__name__)
    #
    logger.info(f"🔍 Login request method: {request.method}")
    logger.info(f"🔍 CSRF token in request: {request.POST.get('csrfmiddlewaretoken', 'MISSING')[:20]}")
    logger.info(f"🔍 CSRF cookie: {request.COOKIES.get('csrftoken', 'MISSING')[:20]}")
    logger.info(f"🔍 Allowed origins: {settings.CSRF_TRUSTED_ORIGINS}")
    #
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.info(f"🔍 Login attempt: username={username}")

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_panel')
            return redirect('user_dashboard')
        else:
            logger.warning(f"❌ Login failed for {username}")
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def signup_view(request):
    """Signup page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('user_dashboard')
    
    return render(request, 'signup.html')

def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')

# ============ ADMIN VIEWS ============

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_panel(request):
    """Admin panel for uploading portfolios"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'upload':
            return handle_portfolio_upload(request)
        elif action == 'delete':
            return handle_portfolio_delete(request)
    
    # GET: Show form and existing data
    portfolios = BrandPortfolio.objects.all().order_by('-created_date')
    tasks = AnalysisTask.objects.all().order_by('-created_date')[:10]
    
    context = {
        'portfolios': portfolios,
        'tasks': tasks,
    }
    
    return render(request, 'admin_panel.html', context)

def handle_portfolio_upload(request):
    """Handle portfolio file upload and analysis"""
    
    brand_name = request.POST.get('brand_name', '').strip()
    product_names_text = request.POST.get('product_names', '').strip()
    document = request.FILES.get('document')
    lookup_ingredients = request.POST.get('lookup_ingredients') == 'on'
    
    # Validate
    if not brand_name:
        messages.error(request, 'Brand name is required')
        return redirect('admin_panel')
    
    if not document:
        messages.error(request, 'Document is required')
        return redirect('admin_panel')
    
    product_names = [p.strip() for p in product_names_text.split('\n') if p.strip()]
    if not product_names:
        messages.error(request, 'Please enter at least one product name')
        return redirect('admin_panel')
    
    try:
        # Create portfolio
        portfolio = BrandPortfolio.objects.create(
            name=brand_name,
            created_by=request.user
        )
        
        # Save document
        UPLOAD_DIR = '/app/uploads'
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        filename = f"{uuid.uuid4()}_{document.name}"
        doc_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(doc_path, 'wb') as f:
            for chunk in document.chunks():
                f.write(chunk)
        
        # Start Celery task - use pdf_path instead of document_path
        task = analyze_portfolio_task.delay(
            portfolio_id=portfolio.id,
            document_path=doc_path,  # Changed from pdf_path
            brand_name=brand_name,
            product_names=product_names,
            lookup_ingredients=lookup_ingredients
        )
        
        AnalysisTask.objects.create(
            task_id=task.id,
            portfolio=portfolio,    
            status='pending',
            product_count=len(product_names)
        )
        
        messages.success(request, f'Analysis started for {len(product_names)} products')
        return redirect('admin_panel')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel')

def handle_portfolio_delete(request):
    """Handle portfolio deletion"""
    
    portfolio_id = request.POST.get('portfolio_id')
    
    try:
        portfolio = get_object_or_404(BrandPortfolio, id=portfolio_id)
        portfolio.delete()
        messages.success(request, f'Portfolio "{portfolio.name}" deleted')
    except Exception as e:
        messages.error(request, f'Error deleting portfolio: {str(e)}')
    
    return redirect('admin_panel')

# ============ USER VIEWS ============

@login_required(login_url='login')
def user_dashboard(request):
    """User dashboard for asking questions"""
    
    answer = None
    brands_used = []
    products_referenced = []
    tokens_used = 0
    
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        brand_ids = request.POST.getlist('brand_ids')
        
        if not question:
            messages.error(request, 'Please ask a question')
        elif not brand_ids:
            messages.error(request, 'Please select at least one brand')
        else:
            try:
                answer, brands_used, products_referenced, tokens_used = get_ai_response(
                    question=question,
                    brand_ids=brand_ids
                )
                if not answer:
                    messages.warning(request, 'No products found matching your criteria')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    
    portfolios = BrandPortfolio.objects.all()
    
    context = {
        'portfolios': portfolios,
        'answer': answer,
        'brands_used': brands_used,
        'products_referenced': products_referenced,
        'tokens_used': tokens_used,
    }
    
    return render(request, 'user_dashboard.html', context)

def get_ai_response(question, brand_ids):
    """Get AI response using Agent 3 + 4"""
    
    # Get brand names
    portfolios = BrandPortfolio.objects.filter(id__in=brand_ids)
    brand_names = list(portfolios.values_list('name', flat=True))
    
    if not brand_names:
        return None, [], [], 0
    
    # Agent 3: Filter products
    agent3 = Agent3Filter(chroma_db_path="/app/chroma_db")
    filtered_products = agent3.search_products(question, brand_names, top_k=5)
    
    if not filtered_products:
        return None, brand_names, [], 0
    
    # Format for Agent 4
    formatted_products = agent3.format_for_agent4(filtered_products)
    
    # Agent 4: Generate answer
    agent4 = Agent4Answerer(openai_api_key=os.getenv("OPENAI_API_KEY"))
    answer, referenced_products = agent4.answer_question(
        question=question, 
        brand_names=brand_names, 
        top_k=5
    )
    
    # Extract product names for display
    products_referenced = [p['metadata'].get('product', 'Unknown') for p in filtered_products if p.get('metadata', {}).get('product')]
    
    return answer, brand_names, products_referenced, 0

# ============ API ENDPOINTS (for future use) ============

@login_required
def api_task_status(request, task_id):
    """Get task status (for AJAX polling if needed)"""
    
    task = get_object_or_404(AnalysisTask, task_id=task_id)
    
    return JsonResponse({
        'status': task.status,
        'progress': task.progress,
        'current_step': task.current_step,
        'error_message': task.error_message,
        'product_count': task.product_count,
    })