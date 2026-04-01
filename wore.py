# -*- coding: utf-8 -*-
import asyncio
import json
import os
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey
from solders.signature import Signature

# ================== إعدادات ==================
API_KEY = "646ea1ed-2917-4644-a471-cef65623c174"
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={API_KEY}"

RAYDIUM_AMM_V4 = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
SEEN_FILE = "seen_pools.json"

client = None
seen_pools = set()

def load_seen_pools():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_seen_pools():
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen_pools), f)

async def get_transaction(tx_sig: str):
    try:
        resp = await client.get_transaction(
            Signature.from_string(tx_sig),
            encoding="jsonParsed",
            max_supported_transaction_version=0,
            commitment=Confirmed
        )
        return resp.value if resp else None
    except Exception as e:
        print(f"❌ خطأ get_transaction: {e}")
        return None

def extract_mints_from_tx(tx):
    if not tx or not tx.transaction:
        return None, None, None
    try:
        account_keys = [str(key) for key in tx.transaction.message.account_keys]
        base_mint = None
        quote_mint = None
        pool_id = None

        for instr in tx.transaction.message.instructions:
            if str(instr.program_id) == str(RAYDIUM_AMM_V4):
                if len(account_keys) > 5:
                    pool_id = account_keys[4]
                if tx.meta and hasattr(tx.meta, 'post_token_balances'):
                    for bal in tx.meta.post_token_balances:
                        mint = bal.mint
                        if mint != "So11111111111111111111111111111111111111112":
                            base_mint = mint
                        else:
                            quote_mint = mint
        return pool_id, base_mint, quote_mint
    except:
        return None, None, None

async def process_pool(signature: str):
    global seen_pools
    if signature in seen_pools:
        return

    print(f"\n📡 تحليل معاملة جديدة: {signature[:15]}...")

    tx = await get_transaction(signature)
    if not tx:
        return

    pool_id, base_mint, quote_mint = extract_mints_from_tx(tx)

    if not pool_id:
        pool_id = signature

    if pool_id in seen_pools:
        return

    seen_pools.add(pool_id)
    save_seen_pools()

    print("\n" + "═" * 80)
    print(f"🚨 **حوض سيولة جديد على Raydium V4** 🚨")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📜 التوقيع     : {signature}")
    print(f"🏠 Pool ID      : {pool_id}")
    if base_mint:
        print(f"🪙 Base Token   : {base_mint}")
        print(f"🔗 Solscan Token: https://solscan.io/token/{base_mint}")
    if quote_mint:
        print(f"💰 Quote Token  : {'SOL' if quote_mint.startswith('So111') else quote_mint}")
    print(f"🔍 Solscan TX   : https://solscan.io/tx/{signature}")
    print("═" * 80 + "\n")

async def keep_alive():
    while True:
        await asyncio.sleep(60)
        try:
            await client.get_health()
        except:
            pass

async def main():
    global client, seen_pools
    client = AsyncClient(RPC_URL)
    seen_pools = load_seen_pools()

    print("🚀 رادار Raydium V4 يعمل باستخدام Helius RPC...")
    print(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-8:]}")
    print("🔍 يراقب: initialize2\n")

    asyncio.create_task(keep_alive())

    async def callback(logs_info):
        try:
            logs = logs_info.value.logs
            signature = str(logs_info.value.signature)

            if any("initialize2" in log.lower() for log in logs):
                await process_pool(signature)
        except Exception as e:
            print(f"⚠️ Callback error: {e}")

    try:
        resp = await client.logs_subscribe(
            mentions=[RAYDIUM_AMM_V4],
            commitment=Confirmed
        )
        sub_id = resp.value.subscription_id
        print(f"✅ تم الاشتراك بنجاح | Subscription ID: {sub_id}")

        async for log_info in client.logs_subscribe_iter(sub_id):
            await callback(log_info)

    except asyncio.CancelledError:
        print("\n🛑 تم إيقاف الرادار.")
    except Exception as e:
        print(f"❌ خطأ رئيسي: {e}")
    finally:
        if client:
            await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الرادار يدوياً.")
