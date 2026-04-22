import hishel

storage = hishel.FileStorage(ttl=300)

# The API exposes non-idempotent POST endpoints for orders, pies, and exports,
# so we only cache GET requests.
controller = hishel.Controller(
    # Cache only GET methods
    cacheable_methods=["GET"],

    # Cache only 200 status codes
    cacheable_status_codes=[200],

    # Use the stale response if there is a connection issue and the new response cannot be obtained.
    allow_stale=True,

    force_cache=True,
)
