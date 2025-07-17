# utility_tools/ip_info_logic.py

def get_client_ip(request):
    """
    Attempts to get the real client IP address from the request headers.
    Checks X-Forwarded-For first, then REMOTE_ADDR.
    """
    # Check standard header set by many proxies/load balancers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list (client, proxy1, proxy2)
        # The first IP is usually the original client
        ip = x_forwarded_for.split(',')[0].strip()
        print(f"[Get IP] Found X-Forwarded-For: {x_forwarded_for}, using: {ip}")
    else:
        # Fallback to the direct connection IP
        ip = request.META.get('REMOTE_ADDR')
        print(f"[Get IP] No X-Forwarded-For, using REMOTE_ADDR: {ip}")

    return ip if ip else "Not Available" # Return something if IP couldn't be determined