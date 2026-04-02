import asyncio
from solana.rpc.websocket_api import connect
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions

# ================== إعدادات ==================
HELIUS_API_KEY = "https://mainnet.helius-rpc.com/?api-key=646ea1ed-2917-4644-a471-cef65623c174"   # ← غيرها بمفتاحك الكامل

RAYDIUM_V4_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

async def main():
    wss_url = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

    print("[*] جاري الاتصال بـ Helius WebSocket...")

    async with connect(wss_url) as websocket:
        print("[✓] متصل بالـ WebSocket بنجاح")

        filter_mentions = RpcTransactionLogsFilterMentions(
            Pubkey.from_string(RAYDIUM_V4_PROGRAM)
        )

        await websocket.logs_subscribe(
            filter_mentions,
            commitment="confirmed"
        )

        first_resp = await websocket.recv()
        subscription_id = first_resp.result
        print(f"[✓] تم الاشتراك بنجاح | Subscription ID: {subscription_id}")
        print("[*] يراقب الآن: Raydium V4 initialize2 ...\n")
        print("-" * 90)

        async for msg in websocket:
            try:
                value = msg.result.value
                signature = str(value.signature)
                logs = value.logs or []

                if any("initialize2" in line for line in logs):
                    print(f"\n🚨 تم اكتشاف initialize2 جديد!")
                    print(f"🔗 Transaction Signature: {signature}")
                    print(f"📜 عدد Logs: {len(logs)}")
                    for line in logs:
                        if "initialize2" in line:
                            print(f"   → {line}")
                            break
                    print("-" * 90)

            except Exception:
                continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] تم إيقاف المراقبة")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
