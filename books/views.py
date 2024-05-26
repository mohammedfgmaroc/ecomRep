from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
import stripe
from django.views.decorators.csrf import csrf_exempt
from ecom_project import settings
from .models import Book, Cart, CartItem, Order, Category, OrderItem
from django.db.models import Q
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import UpdateView


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'

class CategoryListView(ListView):
    model = Category
    template_name = 'category_list.html'
    context_object_name = 'categories' 

class BooksListView(ListView):
    model = Book
    template_name = 'list.html'

class BooksDetailView(DetailView):
    model = Book
    template_name = 'detail.html'



class SearchResultsListView(ListView):
    model = Book
    template_name = 'search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q', '')  # Default to empty string if not provided
        category_id = self.request.GET.get('category_id', '')  # Ensure this matches the name in your form

        queryset = Book.objects.all()  # Start with all books

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(author__icontains=query))

        if category_id and category_id.isdigit():  # Ensure category_id is a valid number
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(SearchResultsListView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()  # Include all categories in context for dropdown
        return context



def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def create_book(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        category_id = request.POST.get('category', '')
        description = request.POST.get('description', '')
        price = request.POST.get('price', 0.0)
        image_url = request.POST.get('image_url', '')
        follow_author = request.POST.get('follow_author', '')
        book_available = request.POST.get('book_available', 0)

        # Récupérer l'objet Category correspondant à l'ID
        category = Category.objects.get(pk=category_id)

        book = Book(
            title=title,
            author=author,
            category=category,  # Utiliser l'objet Category
            description=description,
            price=price,
            image_url=image_url,
            follow_author=follow_author,
            book_available=book_available,
        )
        book.save()
        return redirect('list')

    return render(request, 'create_book.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def update_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        book.title = request.POST.get('title', book.title)
        book.author = request.POST.get('author', book.author)
        book.description = request.POST.get('description', book.description)
        book.price = request.POST.get('price', book.price)
        book.image_url = request.POST.get('image_url', book.image_url)
        book.follow_author = request.POST.get('follow_author', book.follow_author)
        book.book_available = request.POST.get('book_available', book.book_available)
        category_id = request.POST.get('category')
        if category_id:
            book.category = get_object_or_404(Category, pk=category_id)
        book.save()
        return redirect('detail', pk=book.pk)
    return render(request, 'update_book.html', {'book': book, 'categories': categories})

@login_required
@user_passes_test(is_admin)
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('list')  # Assurez-vous que 'list' est le nom correct de la vue qui affiche la liste des livres
    return redirect('list')

class BookCheckoutView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'checkout.html'
    
    def post(self, request):
        selected_items = request.POST.getlist('selected_items')

        if not selected_items:
            messages.error(request, "No items selected for checkout.")
            return redirect('cart_detail')

        cart_items = CartItem.objects.filter(id__in=selected_items, cart__user=request.user)

        if not cart_items:
            messages.error(request, "Selected items are not available in your cart.")
            return redirect('cart_detail')
        
        total = sum(item.book.price * item.quantity for item in cart_items)

        order = Order.objects.create()  # Create the order
        for item in cart_items:
            OrderItem.objects.create(order=order, book=item.book, quantity=item.quantity)
            

        context = {
            'order': order,
            'total_amount': total,
            'cart_items': cart_items,  # Pass the cart items to the template
        }

        return render(request, self.template_name, context)

    def get(self, request):
        cart = Cart.objects.filter(user=request.user).first()  # assuming user is logged in
        if not cart or not cart.items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart_detail')
        cart_items = cart.items.all()  # Get the cart items
        total = sum(item.book.price * item.quantity for item in cart_items)
        context = {
            'cart_items': cart_items,
            'total_amount': total,
        }
        return render(request, self.template_name, context)




@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        print("Processing payment request...")  # Debug print statement
        
        # Get the total amount from the request
        total_amount = request.POST.get('total_amount')
        print("Total amount:", total_amount)  # Debug print statement

        try:
            # Perform payment processing here
            # This could involve integrating with a payment gateway like PayPal, Braintree, etc.
            # For testing purposes, we'll assume the payment is successful
            # Replace this with actual payment processing logic
            
            # Simulate the payment and return a success message
            payment_success = True
            
            if payment_success:
                print("Payment successful!")  # Debug print statement
                
                # Get the selected items from the cart
                selected_items = request.POST.getlist('selected_items')
                
                # Retrieve the cart items
                cart_items = CartItem.objects.filter(id__in=selected_items, cart__user=request.user)
                
                # Delete each cart item
                for item in cart_items:
                    item.delete()

                # Return a success response with a message
                # Redirect to the list page after successful payment
                return redirect('list')
            else:
                # Return an error response if payment fails
                return JsonResponse({'error': 'Payment failed. Please try again.'}, status=400)

        except Exception as e:
            # Return an error response for any exceptions
            print("An error occurred during payment processing:", e)  # Debug print statement
            return JsonResponse({'error': str(e)}, status=500)

    # Return an error response if request method is not POST
    return JsonResponse({'error': 'Invalid request method'}, status=405)
def paymentComplete(request):
    body = json.loads(request.body)
    print('BODY:', body)
    product = Book.objects.get(id=body['productId'])
    Order.objects.create(
        product=product
    )
    return JsonResponse('Payment completed!', safe=False)

@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
    except Cart.DoesNotExist:
        items = []
    return render(request, 'cart/cart_detail.html', {'cart_items': items})

@login_required
@csrf_exempt
def cart_item_update(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        item.quantity = quantity
        item.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
@csrf_exempt
def cart_item_delete(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            return redirect('cart_detail')
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found'}, status=404)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    cart, created = Cart.objects.get_or_create(user=request.user, defaults={'user': request.user})

    # Vérifie si le livre est déjà dans le panier
    cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={'cart': cart, 'book': book})

    if not created:
        # Si l'objet CartItem existait déjà, augmentez la quantité
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_detail')