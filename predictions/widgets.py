from django import forms


class CatRatingWidget(forms.NumberInput):
    """Range slider that mirrors its value with the five MeowMeowBeenz tier cats."""

    input_type = "range"
    template_name = "predictions/widgets/cat_rating.html"

    def __init__(self, attrs=None):
        base_attrs = {"min": "1.00", "max": "5.00", "step": "0.01"}
        base_attrs.update(attrs or {})
        super().__init__(base_attrs)
