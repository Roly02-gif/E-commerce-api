from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from shop.catalog.categories.categoryModel import CategoryModel
from shop.catalog.products.productModel import (
    ProductModel,
    ProductVariantModel,
    SizeModel,
)
from shop.models import AddressModel, UserModel


class AddressInline(admin.StackedInline):
    model = AddressModel
    extra = 0


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = UserModel
        fields = "__all__"

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = UserModel
        fields = ["email", "password", "is_active", "is_staff"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [AddressInline]

    list_display = ["email", "first_name", "last_name", "is_staff"]
    list_filter = ["is_staff"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ["first_name", "last_name"]}),
        ("Permissions", {"fields": ["is_staff"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ],
            },
        ),
    ]
    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = []


class SizeAdmin(admin.ModelAdmin):
    list_display = ["category", "name", "display_order"]
    list_filter = ["category"]
    ordering = ["category", "display_order"]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active"]
    list_filter = ["parent"]
    ordering = ["name"]

    @admin.display(empty_value="???")
    def parent(self, obj):
        return obj.parent.name if obj.parent else None


class ProductVariantInline(admin.TabularInline):
    model = ProductVariantModel
    extra = 0
    fields = [
        "sku",
        "color",
        "size",
        "price",
        "compare_price",
        "stock_quantity",
    ]
    raw_id_fields = ["size"]


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "is_active"]
    list_filter = ["category"]
    ordering = ["name"]
    inlines = [ProductVariantInline]
    search_fields = ["name", "category__name"]


admin.site.register(SizeModel, SizeAdmin)
admin.site.register(CategoryModel, CategoryAdmin)
admin.site.register(UserModel, UserAdmin)
admin.site.register(ProductModel, ProductAdmin)
# admin.site.unregister(Group)
