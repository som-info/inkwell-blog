from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    # Honeypot: real users never see or fill this field.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        labels = {"body": "Comment"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 80}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "body": forms.Textarea(attrs={"rows": 5, "maxlength": 2000}),
        }

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) < 3:
            raise forms.ValidationError("Your comment is a little too short.")
        return body

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""
