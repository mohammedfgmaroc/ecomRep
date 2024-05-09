from django.db import models

from django.contrib.auth import get_user_model

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.CharField(max_length=500, null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    image_url = models.CharField(max_length=2083, null=True, blank=True)
    follow_author = models.CharField(max_length=2083, null=True, blank=True)
    book_available = models.IntegerField(default=0)  # Nombre de copies disponibles
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

    def save(self, *args, **kwargs):
        if not self.category:
            default_category, _ = Category.objects.get_or_create(name="Uncategorized")
            self.category = default_category
        super().save(*args, **kwargs)

class Order(models.Model):
    books = models.ManyToManyField(Book, through='OrderItem')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.book.title}"

class Cart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} of User {self.user.username if self.user else 'Anonymous'}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.book.title}"

    def total_price(self):
        return self.quantity * self.book.price