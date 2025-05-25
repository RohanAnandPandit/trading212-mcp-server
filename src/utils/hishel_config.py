import hishel
from httpcore import Request
from hishel._utils import generate_key



def custom_key_generator(request: Request, body: bytes):
    key = generate_key(request, body)
    method = request.method.decode()
    host = request.url.host.decode()
    path = request.url.target.decode()
    return f"{host}/{path}"

storage = hishel.FileStorage(ttl=300)

# All the specification configs
controller = hishel.Controller(
    # Cache only GET and POST methods
    cacheable_methods=["GET", "POST"],

    # Cache only 200 status codes
    cacheable_status_codes=[200],

    # Use the stale response if there is a connection issue and the new response cannot be obtained.
    allow_stale=True,

    force_cache=True,

    # key_generator=custom_key_generator,
    # First, revalidate the response and then utilize it.
    # If the response has not changed, do not download the
    # entire response data from the server; instead,
    # use the one you have because you know it has not been modified.
    # always_revalidate=True,
)
