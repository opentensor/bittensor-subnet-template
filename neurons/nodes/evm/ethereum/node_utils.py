from web3.providers.base import JSONBaseProvider

# asynchronous JSON RPC API request
async def async_rpc_request(session, url, method, params):
    base_provider = JSONBaseProvider()
    request_data = base_provider.encode_rpc_request(method, params)
    async with session.post(url, data=request_data,
                        headers={'Content-Type': 'application/json'}) as response:
        content = await response.read()
    response = base_provider.decode_rpc_response(content)
    return response
