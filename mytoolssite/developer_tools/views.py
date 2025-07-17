# developer_tools/views.py
from django.shortcuts import render
from .xml_formatter_logic import format_xml_string
from django.contrib import messages # Can use messages for errors

def xml_formatter_view(request):
    context = {
        'page_title': 'XML Formatter',
        'xml_input': '',
        'formatted_xml': None,
        'error_message': None,
        'indent_choice': '4s' # Default indent
    }

    if request.method == 'POST':
        xml_input = request.POST.get('xml_input', '').strip()
        indent_choice = request.POST.get('indent_type', '4s')

        context['xml_input'] = xml_input # Repopulate input
        context['indent_choice'] = indent_choice # Repopulate selection

        if not xml_input:
            messages.warning(request, "Please paste some XML content to format.")
        else:
            print(f"Formatting XML with indent: {indent_choice}")
            formatted_xml, error_message = format_xml_string(xml_input, indent_choice)

            if error_message:
                messages.error(request, error_message)
                context['error_message'] = error_message # Pass specific error if needed
            else:
                context['formatted_xml'] = formatted_xml
                messages.success(request, "XML formatted successfully!")

    return render(request, 'developer_tools/tool_xml_formatter.html', context)







# developer_tools/views.py
from django.shortcuts import render

def regex_tester_view(request):
    """Displays the Regex Tester page."""
    # No backend logic needed for the tester itself
    context = {
        'page_title': 'Regex Tester'
    }
    return render(request, 'developer_tools/tool_regex_tester.html', context)