# toolrequests/views.py
from django.shortcuts import render, redirect
from django.contrib import messages # For success message
from .models import ToolRequest

def request_tool_view(request):
    success_message = None # Initialize success message variable

    if request.method == 'POST':
        # --- Manual POST Data Handling ---
        tool_name_data = request.POST.get('tool_name', '').strip()
        description_data = request.POST.get('description', '').strip()
        email_data = request.POST.get('requester_email', '').strip()

        # --- Manual Validation ---
        errors = {}
        if not tool_name_data:
            errors['tool_name'] = 'Please provide a name or idea for the tool.'
        if not description_data:
            errors['description'] = 'Please describe the tool you are requesting.'
        # Basic email check (optional field) - Django's EmailField does better validation
        if email_data and '@' not in email_data:
             errors['requester_email'] = 'Please enter a valid email address (or leave blank).'


        if not errors:
            # --- Manually Create Model Instance ---
            try:
                ToolRequest.objects.create(
                    tool_name=tool_name_data,
                    description=description_data,
                    requester_email=email_data if email_data else None # Store None if empty
                )
                # Set success message instead of using Django messages framework for simplicity here
                success_message = "Thank you! Your tool request has been submitted successfully."
                # Optionally redirect after success:
                # messages.success(request, "Thank you! Your tool request has been submitted successfully.")
                # return redirect('toolrequests:request_form')
            except Exception as e:
                 # Basic error handling if saving fails
                 errors['general'] = f"An error occurred while saving your request: {e}"

        # --- If there are errors, pass them back to the template ---
        # Also pass back the submitted data to repopulate the form
        if errors:
             context = {
                'page_title': 'Request a Tool',
                'errors': errors,
                'submitted_data': request.POST # Pass the whole POST dict
             }
             return render(request, 'toolrequests/request_form.html', context)

    # --- If GET request or after successful POST (if not redirecting) ---
    context = {
        'page_title': 'Request a Tool',
        'success_message': success_message # Pass success message
    }
    return render(request, 'toolrequests/request_form.html', context)