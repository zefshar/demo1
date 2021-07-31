import logging

import aiohttp
from oauthlib.common import generate_token, urldecode
from oauthlib.oauth2 import (Client, InsecureTransportError,
                             LegacyApplicationClient, TokenExpiredError,
                             WebApplicationClient, is_secure_transport)

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class TokenUpdated(Warning):
    """Exception."""

    def __init__(self, token):
        super(TokenUpdated, self).__init__()
        self.token = token


class AAuthSession(aiohttp.ClientSession):

    def __init__(
        self,
        client_id=None,
        client: Client = None,
        auto_refresh_url=None,
        auto_refresh_kwargs=None,
        scope=None,
        redirect_uri=None,
        token=None,
        state=None,
        token_updater=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._client = client or WebApplicationClient(client_id, token=token)
        self.token = token or {}
        self.scope = scope
        self.redirect_uri = redirect_uri
        self.state = state or generate_token
        self._state = state
        self.auto_refresh_url = auto_refresh_url
        self.auto_refresh_kwargs = auto_refresh_kwargs or {}
        self.token_updater = token_updater

        if self.token_updater:
            assert self.auto_refresh_url, "Auto refresh URL required if token updater"

        # Allow customizations for non compliant providers through various
        # hooks to adjust requests and responses.
        self.compliance_hook = {
            "access_token_response": set(),
            "refresh_token_response": set(),
            "protected_request": set(),
        }

    def new_state(self):
        """Generates a state string to be used in authorizations."""
        try:
            self._state = self.state()
            logger.debug("Generated new state %s.", self._state)
        except TypeError:
            self._state = self.state
            logger.debug("Re-using previously supplied state %s.", self._state)
        return self._state

    @property
    def client_id(self):
        """Get the client_id."""
        return getattr(self._client, "client_id", None)

    @client_id.setter
    def client_id(self, value):
        """Set the client_id."""
        self._client.client_id = value

    @client_id.deleter
    def client_id(self):
        """Remove the client_id."""
        del self._client.client_id

    @property
    def token(self):
        """Get the token."""
        return getattr(self._client, "token", None)

    @token.setter
    def token(self, value):
        """Set the token."""
        self._client.token = value
        # pylint: disable=W0212
        self._client._populate_attributes(value)

    @property
    def access_token(self):
        """Get the access_token."""
        return getattr(self._client, "access_token", None)

    @access_token.setter
    def access_token(self, value):
        """Set the access_token."""
        self._client.access_token = value

    @access_token.deleter
    def access_token(self):
        """Remove the access_token."""
        del self._client.access_token

    @property
    def authorized(self) -> bool:
        return bool(self.access_token)

    def authorization_url(self, url, state=None, **kwargs):
        state = state or self.new_state()
        return (
            self._client.prepare_request_uri(
                url,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                state=state,
                **kwargs
            ),
            state,
        )

    async def fetch_token(
        self,
        token_url,
        code=None,
        authorization_response=None,
        body="",
        auth=None,
        username=None,
        password=None,
        method="POST",
        force_querystring=False,
        timeout=None,
        headers=None,
        verify_ssl=True,
        proxies=None,
        include_client_id=None,
        client_id=None,
        client_secret=None,
        **kwargs
    ):
        if not is_secure_transport(token_url):
            raise InsecureTransportError()

        if not code and authorization_response:
            logger.debug("-- response %s", authorization_response)
            self._client.parse_request_uri_response(
                str(authorization_response), state=self._state
            )
            code = self._client.code
            logger.debug("--code %s", code)
        elif not code and isinstance(self._client, WebApplicationClient):
            code = self._client.code
            if not code:
                raise ValueError(
                    "Please supply either code or " "authorization_response parameters."
                )

        if isinstance(self._client, LegacyApplicationClient):
            if username is None:
                raise ValueError(
                    "`LegacyApplicationClient` requires both the "
                    "`username` and `password` parameters."
                )
            if password is None:
                raise ValueError(
                    "The required paramter `username` was supplied, "
                    "but `password` was not."
                )

        # merge username and password into kwargs for `prepare_request_body`
        if username is not None:
            kwargs["username"] = username
        if password is not None:
            kwargs["password"] = password

        # is an auth explicitly supplied?
        if auth is not None:
            # if we're dealing with the default of `include_client_id` (None):
            # we will assume the `auth` argument is for an RFC compliant server
            # and we should not send the `client_id` in the body.
            # This approach allows us to still force the client_id by submitting
            # `include_client_id=True` along with an `auth` object.
            if include_client_id is None:
                include_client_id = False

        # otherwise we may need to create an auth header
        else:
            # since we don't have an auth header, we MAY need to create one
            # it is possible that we want to send the `client_id` in the body
            # if so, `include_client_id` should be set to True
            # otherwise, we will generate an auth header
            if include_client_id is not True:
                client_id = self.client_id
            if client_id:
                logger.debug(
                    'Encoding `client_id` "%s" with `client_secret` '
                    "as Basic auth credentials.",
                    client_id,
                )
                client_secret = client_secret if client_secret is not None else ""
                auth = aiohttp.BasicAuth(
                    login=client_id, password=client_secret)

        if include_client_id:
            # this was pulled out of the params
            # it needs to be passed into prepare_request_body
            if client_secret is not None:
                kwargs["client_secret"] = client_secret

        body = self._client.prepare_request_body(
            code=code,
            body=body,
            redirect_uri=self.redirect_uri,
            include_client_id=include_client_id,
            **kwargs
        )

        headers = headers or {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
        self.token = {}
        request_kwargs = {}
        if method.upper() == "POST":
            request_kwargs["params" if force_querystring else "data"] = dict(
                urldecode(body)
            )
        elif method.upper() == "GET":
            request_kwargs["params"] = dict(urldecode(body))
        else:
            raise ValueError("The method kwarg must be POST or GET.")

        async with self.request(
            method=method,
            url=token_url,
            timeout=timeout,
            headers=headers,
            auth=auth,
            verify_ssl=verify_ssl,
            proxy=proxies,
            **request_kwargs
        ) as resp:
            logger.debug(
                "Request to fetch token completed with status %s.", resp.status
            )
            logger.debug("Request headers were %s", headers)
            logger.debug("Request body was %s", body)
            text = await resp.text()

            logger.debug("Response headers were %s and content %s.",
                         resp.headers, text)
            (resp,) = self._invoke_hooks("access_token_response", resp)

        self._client.parse_request_body_response(text, scope=self.scope)
        self.token = self._client.token
        logger.debug("Obtained token %s.", self.token)
        return self.token

    def token_from_fragment(self, authorization_response):
        """Parse token from the URI fragment, used by MobileApplicationClients.

        :param authorization_response: The full URL of the redirect back to you
        :return: A token dict
        """
        self._client.parse_request_uri_response(
            authorization_response, state=self._state
        )
        self.token = self._client.token
        return self.token

    async def refresh_token(
        self,
        token_url,
        refresh_token=None,
        body="",
        auth=None,
        timeout=None,
        headers=None,
        verify_ssl=True,
        proxies=None,
        **kwargs
    ):
        if not token_url:
            raise ValueError("No token endpoint set for auto_refresh.")

        if not is_secure_transport(token_url):
            raise InsecureTransportError()

        refresh_token = refresh_token or self.token.get("refresh_token")

        logger.debug(
            "Adding auto refresh key word arguments %s.", self.auto_refresh_kwargs
        )

        kwargs.update(self.auto_refresh_kwargs)
        body = self._client.prepare_refresh_body(
            body=body, refresh_token=refresh_token, scope=self.scope, **kwargs
        )
        logger.debug("Prepared refresh token request body %s", body)

        if headers is None:
            headers = {
                "Accept": "application/json",
                "Content-Type": ("application/x-www-form-urlencoded;charset=UTF-8"),
            }

        async with self.post(
            token_url,
            data=dict(urldecode(body)),
            auth=auth,
            timeout=timeout,
            headers=headers,
            verify_ssl=verify_ssl,
            withhold_token=True,
            # proxy=proxies,
        ) as resp:
            logger.debug(
                "Request to refresh token completed with status %s.", resp.status
            )
            text = await resp.text()
            logger.debug("Response headers were %s and content %s.",
                         resp.headers, text)
            (resp,) = self._invoke_hooks("refresh_token_response", resp)

        self.token = self._client.parse_request_body_response(
            text, scope=self.scope)
        if "refresh_token" not in self.token:
            logger.debug("No new refresh token given. Re-using old.")
            self.token["refresh_token"] = refresh_token
        return self.token

    async def _request(
        self,
        method,
        url,
        *,
        data=None,
        headers=None,
        withhold_token=False,
        client_id=None,
        client_secret=None,
        **kwargs
    ):
        """Intercept all requests and add the OAuth 2 token if present."""
        if not is_secure_transport(url):
            raise InsecureTransportError()
        if self.token and not withhold_token:

            url, headers, data = self._invoke_hooks(
                "protected_request",
                url,
                headers,
                data,
            )
            logger.debug("Adding token %s to request.", self.token)
            try:
                url, headers, data = self._client.add_token(
                    url,
                    http_method=method,
                    body=data,
                    headers=headers,
                )
            # Attempt to retrieve and save new access token if expired
            except TokenExpiredError:
                if self.auto_refresh_url:
                    logger.debug(
                        "Auto refresh is set, attempting to refresh at %s.",
                        self.auto_refresh_url,
                    )

                    # We mustn't pass auth twice.
                    auth = kwargs.pop("auth", None)
                    if client_id and client_secret and (auth is None):
                        logger.debug(
                            'Encoding client_id "%s" with client_secret as Basic auth credentials.',
                            client_id,
                        )
                        auth = aiohttp.BasicAuth(
                            login=client_id,
                            password=client_secret,
                        )
                    token = await self.refresh_token(
                        self.auto_refresh_url, auth=auth, **kwargs
                    )
                    if self.token_updater:
                        logger.debug(
                            "Updating token to %s using %s.", token, self.token_updater
                        )
                        await self.token_updater(token)
                        url, headers, data = self._client.add_token(
                            url, http_method=method, body=data, headers=headers
                        )
                    else:
                        raise TokenUpdated(token)
                else:
                    raise

        logger.debug("Requesting url %s using method %s.", url, method)
        logger.debug("Supplying headers %s and data %s", headers, data)
        logger.debug("Passing through key word arguments %s.", kwargs)
        return await super()._request(method, url, headers=headers, data=data, **kwargs)

    def register_compliance_hook(self, hook_type, hook):
        if hook_type not in self.compliance_hook:
            raise ValueError(
                "Hook type {} is not in {}.".format(
                    hook_type, self.compliance_hook)
            )
        self.compliance_hook[hook_type].add(hook)

    def _invoke_hooks(self, hook_type, *hook_data):
        logger.debug(
            "Invoking %d %s hooks.", len(
                self.compliance_hook[hook_type]), hook_type
        )
        for hook in self.compliance_hook[hook_type]:
            logger.debug("Invoking hook %s.", hook)
            hook_data = hook(*hook_data)
        return hook_data
