import asyncio
import json
import time

from web3 import Web3
from websockets import connect
from eth_abi import decode_single

INFURA_ID = ""

if len(INFURA_ID) == 0:
  raise BaseException("Undefined INFURA_ID. You can get one for free by signing up at https://infura.io")

w3 = Web3(
    Web3.WebsocketProvider(
        f"wss://mainnet.infura.io/ws/v3/{INFURA_ID}"
    )
)

contracts = []

file = open("contracts.csv", "a")
file.write("tx,contract,balance,name,tokenURI,minter,timestamp")
file.close()

async def get_event():
    async with connect(
        f"wss://mainnet.infura.io/ws/v3/{INFURA_ID}"
    ) as ws:
        await ws.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": [
                        "logs",
                        {
                            "topics": [
                                w3.keccak(
                                    text="Transfer(address,address,uint256)"
                                ).hex(),
                                "0x0000000000000000000000000000000000000000000000000000000000000000",
                            ]
                        },
                    ],
                }
            )
        )

        subscription_response = await ws.recv()
        print(subscription_response)

        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60)
                payload = json.loads(message)

                token_id = list(
                    decode_single(
                        "(uint256)",
                        bytearray.fromhex(payload["params"]["result"]["topics"][3][2:]),
                    )
                )
                # We only want to target new NFT collections
                if token_id and int(token_id[0]) > 5 and int(token_id[0]) < 300:
                    contract_addr = payload["params"]["result"]["address"]

                    if contract_addr in contracts:
                        pass
                    else:
                        try:
                            contract = w3.eth.contract(address=Web3.toChecksumAddress(contract_addr), abi='[{ "inputs": [], "name": "name", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "stateMutability": "view", "type": "function" },{ "inputs": [ { "internalType": "uint256", "name": "_tokenId","type": "uint256"}],"name": "tokenURI","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"}]')
                            token_uri = contract.functions.tokenURI(int(token_id[0])).call()
                            name = contract.functions.name().call()
                        except:
                            name = ""
                            token_uri = ""

                        contract_balance = w3.eth.getBalance(Web3.toChecksumAddress(contract_addr))
                        contract_balance = round(w3.fromWei(contract_balance, "ether"), 2)
                        minter_addr = list(decode_single('(address)',bytearray.fromhex(payload['params']['result']['topics'][2][2:])))[0]
                        tx = payload['params']['result']['transactionHash']
                        file = open("contracts.csv", "a")
                        file.write("\n")
                        file.write(f"{tx},{contract_addr},{contract_balance},{name},{token_uri},{minter_addr},{int(time.time())}")
                        file.close()

                        contracts.append(contract_addr)
                    pass
            except:
                pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    while True:
        loop.run_until_complete(get_event())
