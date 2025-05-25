import hishel

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
)
