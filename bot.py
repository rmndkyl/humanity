import random
from web3 import Web3, HTTPProvider
import requests
from colorama import init, Fore
import sys
import time
from datetime import datetime

# Inisialisasi colorama
init(autoreset=True)

# Fungsi untuk menampilkan timestamp
def timestamp():
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

# Fungsi untuk membaca proxy dari file
def load_proxy(file_path):
    try:
        with open(file_path, 'r') as file:
            proxies = [line.strip() for line in file if line.strip()]
            if proxies:
                selected_proxy = random.choice(proxies)
                return selected_proxy
            else:
                print(Fore.YELLOW + f"{timestamp()} ⚠️ File proxy.txt kosong.")
                return None
    except FileNotFoundError:
        print(Fore.YELLOW + f"{timestamp()} ⚠️ File proxy.txt tidak ditemukan.")
        return None

# Pengaturan dan koneksi blockchain
def setup_blockchain_connection(rpc_url, use_proxy=False):
    session = requests.Session()

    if use_proxy:
        proxy = load_proxy('proxy.txt')
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy,
            }
            session.proxies.update(proxies)
            print(Fore.GREEN + f"{timestamp()} ✅ Proxy diatur: {proxy}")
        else:
            print(Fore.YELLOW + f"{timestamp()} ⚠️ Proxy tidak tersedia, menggunakan koneksi langsung.")
    else:
        print(Fore.CYAN + f"{timestamp()} 🌐 Tidak menggunakan proxy, menghubungkan langsung.")

    provider = HTTPProvider(rpc_url, session=session)
    web3 = Web3(provider)

    if web3.is_connected():
        print(Fore.GREEN + f"{timestamp()} ✅ Terhubung ke Humanity Protocol")
    else:
        print(Fore.RED + f"{timestamp()} ❌ Koneksi gagal.")
        sys.exit(1)

    return web3

# Memuat kunci privat dari file
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + f"{timestamp()} ❌ File private_keys.txt tidak ditemukan.")
        sys.exit(1)

# Cek apakah hadiah perlu diklaim
def claim_rewards_with_proxy(private_key, rpc_url, use_proxy, contract):
    web3 = setup_blockchain_connection(rpc_url, use_proxy)
    try:
        account = web3.eth.account.from_key(private_key)
        sender_address = account.address
        genesis_claimed = contract.functions.userGenesisClaimStatus(sender_address).call()
        current_epoch = contract.functions.currentEpoch().call()
        _, claim_status = contract.functions.userClaimStatus(sender_address, current_epoch).call()

        if genesis_claimed and not claim_status:
            print(Fore.GREEN + f"{timestamp()} 🎉 Mengklaim hadiah untuk: {sender_address} (Hadiah Genesis sudah diklaim)")
            process_claim(sender_address, private_key, web3, contract)
        elif not genesis_claimed:
            print(Fore.GREEN + f"{timestamp()} 🎁 Mengklaim hadiah untuk: {sender_address} (Hadiah Genesis belum diklaim)")
            process_claim(sender_address, private_key, web3, contract)
        else:
            print(Fore.YELLOW + f"{timestamp()} ⚠️ Hadiah sudah diklaim untuk alamat: {sender_address} di epoch {current_epoch}. Melewati.")

    except Exception as e:
        handle_error(e, sender_address)

# Menangani kesalahan dengan pesan yang jelas
def handle_error(e, address):
    error_message = str(e)
    if "Rewards: user not registered" in error_message:
        print(Fore.RED + f"{timestamp()} ❌ Kesalahan: Pengguna {address} tidak terdaftar.")
    elif "ALREADY_EXISTS" in error_message:
        print(Fore.YELLOW + f"{timestamp()} ⚠️ Transaksi sudah dalam mempool untuk {address}. Melewati.")
    else:
        print(Fore.RED + f"{timestamp()} ❌ Kesalahan mengklaim hadiah untuk {address}: {error_message}")

# Memproses transaksi klaim hadiah
def process_claim(sender_address, private_key, web3, contract):
    try:
        nonce = web3.eth.get_transaction_count(sender_address)
        gas_amount = contract.functions.claimReward().estimate_gas({
            'chainId': web3.eth.chain_id,
            'from': sender_address,
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce
        })
        transaction = contract.functions.claimReward().build_transaction({
            'chainId': web3.eth.chain_id,
            'from': sender_address,
            'gas': gas_amount,
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce
        })
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(Fore.GREEN + f"{timestamp()} ✅ Transaksi berhasil untuk {sender_address} dengan hash: {web3.to_hex(tx_hash)}")

    except Exception as e:
        handle_error(e, sender_address)

# Eksekusi utama
if __name__ == "__main__":
    rpc_url = 'https://rpc.testnet.humanity.org'

    # Prompt user to choose proxy usage
    use_proxy_input = input(Fore.CYAN + f"{timestamp()} ❓ Apakah Anda ingin menggunakan proxy? (y/n): ").strip().lower()
    use_proxy = use_proxy_input == 'y'

    web3 = setup_blockchain_connection(rpc_url, use_proxy)
    
    contract_address = '0xa18f6FCB2Fd4884436d10610E69DB7BFa1bFe8C7'
    contract_abi = [...]  # Tempatkan ABI lengkap di sini
    contract = web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=contract_abi)

    print(Fore.CYAN + "📢 Ikuti Channel Telegram: https://t.me/layerairdrop untuk mendapatkan update skrip lebih lanjut.")

    # Loop untuk menjalankan setiap 6 jam
    while True:
        private_keys = load_private_keys('private_keys.txt')
        for private_key in private_keys:
            claim_rewards_with_proxy(private_key, rpc_url, use_proxy, contract)

        print(Fore.CYAN + f"{timestamp()} ⏳ Menunggu selama 6 jam sebelum menjalankan lagi...")
        confirmation = input(Fore.CYAN + "❓ Apakah Anda ingin melanjutkan loop? (y/n): ").strip().lower()
        if confirmation != 'y':
            print(Fore.CYAN + f"{timestamp()} 🚪 Keluar dari loop. Sampai jumpa!")
            break
        time.sleep(6 * 60 * 60)
