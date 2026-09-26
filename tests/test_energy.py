from unittest.mock import Mock

import pytest
from tronpy.abi import trx_abi
from tronpy.exceptions import UnknownError

from app.energy import estimate_transfer_energy


ADDRESS = "TPEkEPcfbckifNwGjdQK3fat9vDLPrQBV7"


def estimate(client):
    return estimate_transfer_energy(client, ADDRESS, ADDRESS, ADDRESS, 55500000)


def test_primary_estimate_uses_actual_transfer_amount():
    client = Mock()
    client.get_estimated_energy.return_value = 65000
    assert estimate(client) == 65000
    encoded = client.get_estimated_energy.call_args.args[3]
    assert trx_abi.decode_single("(address,uint256)", bytes.fromhex(encoded)) == (
        ADDRESS, 55500000
    )
    client.trigger_constant_contract.assert_not_called()


def test_unsupported_estimation_falls_back_to_simulation():
    client = Mock()
    client.get_estimated_energy.side_effect = UnknownError(
        "this node does not support estimate energy"
    )
    client.trigger_constant_contract.return_value = {
        "result": {"result": True}, "energy_used": 64285
    }
    assert estimate(client) == 64285
    assert client.trigger_constant_contract.call_args == client.get_estimated_energy.call_args


def test_unrelated_rpc_failure_is_not_hidden():
    client = Mock()
    client.get_estimated_energy.side_effect = UnknownError("contract execution failed")
    with pytest.raises(UnknownError):
        estimate(client)
    client.trigger_constant_contract.assert_not_called()


@pytest.mark.parametrize("response", [
    {},
    {"result": {"result": False}, "energy_used": 65000},
    {"result": {"result": True}},
    {"result": {"result": True}, "energy_used": 0},
    {"result": {"result": True}, "energy_used": -1},
])
def test_invalid_simulation_stops_transfer(response):
    client = Mock()
    client.get_estimated_energy.side_effect = UnknownError(
        "this node does not support estimate energy"
    )
    client.trigger_constant_contract.return_value = response
    with pytest.raises(ValueError):
        estimate(client)
