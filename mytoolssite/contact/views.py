# contact/views.py
from django.shortcuts import render, redirect
from django.core.validators import validate_email # For basic email validation
from django.core.exceptions import ValidationError
from .models import ContactMessage

def contact_view(request):
    success_message = None
    errors = {}
    submitted_data = {} # Initialize empty dict for submitted data

    if request.method == 'POST':
        submitted_data = request.POST # Store submitted data for repopulation

        # --- Manual POST Data Handling ---
        name_data = request.POST.get('name', '').strip()
        email_data = request.POST.get('email', '').strip()
        subject_data = request.POST.get('subject', '').strip()
        message_data = request.POST.get('message', '').strip()

        # --- Manual Validation ---
        if not name_data:
            errors['name'] = 'Please enter your name.'
        if not email_data:
            errors['email'] = 'Please enter your email address.'
        else:
            # Basic email validation
            try:
                validate_email(email_data)
            except ValidationError:
                errors['email'] = 'Please enter a valid email address.'
        if not subject_data:
            errors['subject'] = 'Please enter a subject.'
        if not message_data:
            errors['message'] = 'Please enter your message.'

        if not errors:
            # --- Manually Create Model Instance ---
            try:
                ContactMessage.objects.create(
                    name=name_data,
                    email=email_data,
                    subject=subject_data,
                    message=message_data
                )
                success_message = "Thank you for contacting us! We'll get back to you if necessary."
                submitted_data = {} # Clear submitted data on success
                # Optionally redirect after success:
                # from django.contrib import messages
                # messages.success(request, "Thank you for contacting us!")
                # return redirect('contact:contact_form')
            except Exception as e:
                 errors['general'] = f"An error occurred: {e}"

    # --- Pass data to template ---
    context = {
        'page_title': 'Contact Us',
        'errors': errors,
        'submitted_data': submitted_data,
        'success_message': success_message
    }
    return render(request, 'contact/contact_form.html', context)