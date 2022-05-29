# This script is provided for educational purposes only.

from web3 import Web3
from bs4 import BeautifulSoup
from tqdm import tqdm
import tabulate
import requests

page = requests.get("https://icy.tools/discover").text
doc = BeautifulSoup(page, "html.parser")

INFURA_ID = ""

if len(INFURA_ID) == 0:
  raise BaseException("Undefined INFURA_ID. You can get one for free by signing up at https://infura.io")

infura_url = f"https://mainnet.infura.io/v3/{INFURA_ID}"
w3 = Web3(Web3.HTTPProvider(infura_url))

for parent in doc.find("p", string="Collection").parents:
    if parent.name == "table":
        table = parent

cols = []

size = len(table.find("tbody").find_all("tr"))

banner = """
██╗░█████╗░██╗░░░██╗  ██████╗░░█████╗░██████╗░░██████╗███████╗██████╗░
██║██╔══██╗╚██╗░██╔╝  ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗
██║██║░░╚═╝░╚████╔╝░  ██████╔╝███████║██████╔╝╚█████╗░█████╗░░██████╔╝
██║██║░░██╗░░╚██╔╝░░  ██╔═══╝░██╔══██║██╔══██╗░╚═══██╗██╔══╝░░██╔══██╗
██║╚█████╔╝░░░██║░░░  ██║░░░░░██║░░██║██║░░██║██████╔╝███████╗██║░░██║
╚═╝░╚════╝░░░░╚═╝░░░  ╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝╚═╝░░╚═╝
"""

copy = """
by @ADAM0x28
"""

print(banner)
print(copy)

show_links = False
show_balance = True

for i in tqdm(range(size)):
    col = table.find("tbody").find_all("tr")[i]
    url = ""
    contract = ""
    balance = ""
    name = ""
    mints_count = ""
    minters = ""
    opensea_url = ""
    etherscan_url = ""

    minters_count = col.find_all("td")[5].find("p").string
    mints_count = col.find_all("td")[4].find("p").string
    details = col.find("td").find("a")
    img = details.find("img")
    contract_raw = list(
        filter(lambda str: str.startswith("0x"), details["href"].split("/"))
    )

    if len(contract_raw) == 0:
        contract = ""
    else:
        contract = contract_raw[0]

        if show_balance:
            balance = w3.eth.getBalance(Web3.toChecksumAddress(contract))
            balance = round(w3.fromWei(balance, "ether"), 2)

    if show_links:
        col_page = requests.get(
            f"https://icy.tools/collections/{contract}/overview"
        ).text
        col_doc = BeautifulSoup(col_page, "html.parser")

        for link in col_doc.find_all("a", rel="dofollow"):
            if link is not None:
                href = link["href"]

                if href.startswith("https://opensea"):
                    opensea_url = href.split("?")[0]

                if href.startswith("https://etherscan"):
                    etherscan_url = href.split("?")[0]

    if img is not None:
        url = img["src"]

        for sib in img.parent.next_siblings:
            if sib.name == "div":
                real_sib = sib

        name = real_sib.find("p").string

    mints_count = int(mints_count.get_text().replace(",", ""))
    minters_count = int(minters_count.get_text().replace(",", ""))

    cols.append(
        {
            "name": name,
            "contract": contract,
            "balance, ETH": balance,
            "mints_count": int(mints_count),
            "minters_count": minters_count,
            "average_mint": round(mints_count / minters_count, 2),
            "opensea": opensea_url,
            "etherscan": etherscan_url,
        }
    )

cols.sort(key=lambda e: e["average_mint"])

header = cols[0].keys()
rows = [x.values() for x in cols]
print(tabulate.tabulate(rows, header))
