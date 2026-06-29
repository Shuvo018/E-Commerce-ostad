from django import forms


class AddToCartForm(forms.Form):
    variant_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)

class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=0)
    