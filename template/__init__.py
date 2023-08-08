# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# TODO(developer): Change this value when updating your code base.
# Define the version of the template module.
__version__ = "0.0.0"
version_split = __version__.split(".")
__spec_version__ = (1000 * int(version_split[0])) + (10 * int(version_split[1])) + (1 * int(version_split[2]))

# TODO(developer): Change this value to the chain your subnet runs on.
# Global chain endpoint for this module, 'test' points the
# miner and the validator at the bittensor test network, 'finney
# points the miner and the validator at the bittensor main network.
CHAIN_ENDPOINT = None # Must be set.
# Optional: assert CHAIN_ENDPOINT is not None, "CHAIN_ENDPOINT must be set."

# TODO(developer): Change this value to the netuid of your subnet.
# Global netid for this module, -1 is a dummy value.
# This value must be set by you after going through the process
# of registering a subnetwork on the chain you selected above.
NETUID = None # Must be set.
# Optional: assert NETUID is not None, "NETUID must be set."

# Import all submodules.
from . import protocol
