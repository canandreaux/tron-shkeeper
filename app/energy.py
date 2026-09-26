from tronpy.abi import trx_abi
from tronpy.exceptions import UnknownError, ValidationError


def estimate_transfer_energy(client, owner, contract, recipient, amount):
    parameter = trx_abi.encode_single(
        "(address,uint256)", (recipient, amount)
    ).hex()
    try:
        energy = client.get_estimated_energy(
            owner, contract, "transfer(address,uint256)", parameter
        )
    except (UnknownError, ValidationError) as exc:
        if "does not support estimate energy" not in str(exc).lower():
            raise
        # Public nodes may disable estimateenergy but still support simulation.
        result = client.trigger_constant_contract(
            owner, contract, "transfer(address,uint256)", parameter
        )
        if result.get("result", {}).get("result") is not True:
            raise ValueError("Energy simulation did not succeed")
        energy = result.get("energy_used")
    if isinstance(energy, bool) or not isinstance(energy, int) or energy <= 0:
        raise ValueError("RPC returned an invalid energy estimate")
    return energy
