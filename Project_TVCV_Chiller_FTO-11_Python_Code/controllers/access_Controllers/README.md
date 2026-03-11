### access_Controller.py

Location: TVCV_Demo_Code/controllers/access_Controllers/access_Controller.py

Purpose:
Provides a simple access-token generator for authenticating with the ANTAR IIoT (ThingsBoard) backend. The class exposes a static method that performs an HTTP login using fixed credentials and returns a Bearer token which other modules can use for authenticated requests.

Class: access_Token

Static Method: access_Token_Generator()

- Sends a POST request to:
  {ANTAR_IIoT_URL}/api/auth/login
  using JSON body:
  {"username": "tenant@antariiot.com", "password": "tenant"}
- Headers used:
  {
  "accept": "application/json",
  "Content-Type": "application/json"
  }
- On success (HTTP 200):
  - Extracts `token` from the JSON response and returns it.
  - Prints "LogIn was Successfull." with a timestamp.
- On failure:
  - Prints "Token generation failed." and returns `None`.

Usage:

- Intended to be called periodically to refresh the authentication token.
- In this project the method is invoked from `main_Code.py` in a background thread (every 840 seconds / 14 minutes) to keep `ACCESS_TOKEN` up-to-date for modules that require authentication.

Dependencies:

- requests
- json
- datetime
- config.ANTAR_IIoT_URL

Notes & recommendations:

- Credentials are hard-coded in the method. For production, move credentials to secure storage (environment variables, secrets manager) and do not commit them to source control.
- The method performs a blocking network call; it is safe here because it runs from a dedicated background thread. For high-availability systems consider retries with exponential backoff and error handling for transient network failures.
- Returned token should be validated by callers (i.e., check for None) before use.
- Consider caching and reusing tokens until expiration rather than logging in repeatedly if the backend supports token introspection/expiration metadata.
- Replace print statements with structured logging when integrating into larger deployments.
