# ==============================
# IMPORTS
# ==============================
import requests
import random
import asyncio
import sys

from json import JSONDecodeError
from flow_py_sdk import flow_client
from flow_py_sdk.cadence import Address, UInt64
from utils.helpers import get_last_processed_block, save_last_processed_block, save_gift
from requests.auth import HTTPBasicAuth

# TEMP CREDENTIALS FOR FORTE HACKS
USERNAME = "bobo"
PASSWORD = ""

# ==============================
# CONFIG
# ==============================
BASE_URL = "https://api.find.xyz/simple/v1"
FLOW_ACCOUNT = "0xf853bd09d46e7db6"
STARTING_HEIGHT = 118542742
OFFSET = 100


# ==============================
# RETRYING GET REQUEST
# ==============================
async def get_with_retries(url, headers={}, max_retries=5, backoff_factor=1.5, **kwargs):
    attempt = 0
    wait_time = 1

    while attempt < max_retries:
        try:
            response = requests.get(url, headers=headers, **kwargs)
            if response.status_code == 200:
                return response

            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = float(retry_after)
                else:
                    wait_time *= backoff_factor
            elif response.status_code >= 500:
                print(f"Server error {response.status_code}. Retrying...")
                wait_time *= backoff_factor
            else:
                await response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}. Retrying...")
            wait_time *= backoff_factor

        await asyncio.sleep(wait_time + random.uniform(0, 0.5))
        attempt += 1

    raise Exception(f"Failed to get {url} after {max_retries} retries")


# ==============================
# TIER → POINTS
# ==============================
def get_points_for_tier(tier: str) -> int:
    mapping = {
        "MOMENT_TIER_COMMON": 1,
        "MOMENT_TIER_FANDOM": 1,
        "MOMENT_TIER_RARE": 50,
        "MOMENT_TIER_LEGENDARY": 1000,
        "MOMENT_TIER_ULTIMATE": 1000,
        "MOMENT_TIER_ANTHOLOGY": 1000,
    }
    return mapping.get(tier, 0)


# ==============================
# GRAPHQL CALL
# ==============================
async def query_moment_metadata(moment_id: int) -> dict:
    url = "https://public-api.nbatopshot.com/graphql"
    query = """
    query getMintedMoment($momentId: ID!) {
      getMintedMoment(momentId: $momentId) {
        data {
          id
          tier
          set {
            flowId
          }
          play {
            headline
          }
        }
      }
    }
    """
    variables = {"momentId": str(moment_id)}
    payload = {"query": query, "variables": variables}
    headers = {
        "User-Agent": "PetJokicsHorses",
        "Content-Type": "application/json"
    }

    for attempt in range(5):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data["data"]["getMintedMoment"]["data"]
        except (requests.RequestException, KeyError, TypeError) as e:
            print(f"Error querying GraphQL (attempt {attempt + 1}): {e}")
            await asyncio.sleep(1.5 * (attempt + 1))

    print(f"Failed to get metadata for moment ID {moment_id} after retries.")
    return None


# ==============================
# FINAL GET MOMENT POINTS
# ==============================
async def get_moment_points(moment_id: int) -> int:
    metadata = await query_moment_metadata(moment_id)
    if metadata is None:
        print(f"Failed to get metadata for moment {moment_id}", file=sys.stderr, flush=True)
        return 0

    # Special rule: if set.flowId == 2, award 250 points
    flow_id = metadata.get("set", {}).get("flowId")
    if flow_id == 2:
        # print(f"Moment ID {moment_id} has set.flowId 2 → 250 points.")
        return 250

    if not metadata.get("play", {}).get("headline", "").startswith("Nikola Joki"):
        return 0

    tier = metadata.get("tier")
    points = get_points_for_tier(tier)
    # print(f"Moment ID {moment_id} is tier {tier}, awarded {points} points.")
    return points

def generate_jwt_token(expiry: str = "168h"):
    """
    Use the auth/v1/generate endpoint with Basic Auth to get a JWT token.
    expiry example: "10m", "2h", etc.
    Returns the token string, or raises an exception.
    """
    url = f"https://api.find.xyz/auth/v1/generate"
    params = {"expiry": expiry}
    resp = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params)
    resp.raise_for_status()
    data = resp.json()
    # expected keys: access_token, token_type, expires_in, etc.
    return data["access_token"], data


# ==============================
# FETCH FLOW EVENTS
# ==============================
async def get_block_gifts(block_height, offset):
    gifts = []
    gift_txns = []

    delay = 30  # add few min delay for block info to get populated
    token, token_info = generate_jwt_token(expiry="1h")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = await get_with_retries(f"{BASE_URL}/blocks?height={block_height + offset + delay}", headers=headers)
    blocks = response.json()
    
    page = 0
    eventsjson = list()
    while True:

        if blocks['blocks'][0]['height'] != block_height + offset + delay:
            # print('Waiting for more blocks')
            await asyncio.sleep(10)
            return False
        response = await get_with_retries(
            f"{BASE_URL}/events?from_height={block_height}&to_height={block_height + offset}&limit=100&offset={page * 100}&name=A.0b2a3299cc857e29.TopShot.Deposit",
            headers=headers
        )
        #print(response.json())
        new_events = list(response.json()['events'])
        print(len(new_events))
        eventsjson.extend(new_events)
        if len(new_events) < 100:
            break
        page += 1
        if page > 50:
            break

    for event in eventsjson:
        if event['fields']['to'] == FLOW_ACCOUNT:
            gift_txns.append(event['transaction_hash'])

    # print(f"Block {block_height}: Found gift transactions {gift_txns}")

    for txn in gift_txns:
        response = await get_with_retries(f"{BASE_URL}/transaction?id={txn}", headers=headers)
        try:
            txn_content = response.json()
            if txn_content['transactions'][0]['status'] != 'SEALED':
                continue
            events = txn_content['transactions'][0]['events']
            if len(events) < 4:
                continue
            if events[0]['name'] == 'A.0b2a3299cc857e29.TopShot.Withdraw' and \
                    events[3]['name'] == 'A.0b2a3299cc857e29.TopShot.Deposit' and \
                    events[3]['fields']['to'] == FLOW_ACCOUNT:
                gift = events[0]['fields']
                gift['moment_id'] = gift['id']
                del gift['id']
                gift['txn_id'] = txn_content['transactions'][0]['id']
                gift['timestamp'] = txn_content['transactions'][0]['timestamp']
                gifts.append(gift)
        except (KeyError, JSONDecodeError):
            pass

    return gifts


# ==============================
# MAIN LOOP
# ==============================
async def main(offset=OFFSET):
    # all_gifts = []
    #reset_last_processed_block("129210000")
    block_height = get_last_processed_block() - offset

    while True:
        new_gifts = await get_block_gifts(block_height, offset)

        if new_gifts is False:
            continue  # Do NOT advance block_height
        for gift in new_gifts:
            moment_id = int(gift['moment_id'])
            # print(f"Checking moment ID {moment_id} for points...")
            points = await get_moment_points(moment_id)
            if points == 0:
                points = await get_moment_points(moment_id)
            # print(f"Transaction {gift['txn_id']} - Awarded {points} points")
            # Here you can save to DB, file, etc.
            # all_gifts.append((gift, points))
            save_gift(
                txn_id=gift['txn_id'],
                moment_id=int(gift['moment_id']),
                from_address=gift.get('from', 'unknown'),
                points=points,
                timestamp=gift.get('timestamp', '')
            )
        if offset == OFFSET:
            save_last_processed_block(block_height + offset)
        block_height += offset + 1
        await asyncio.sleep(0.01)
        # print(f"Next block_height: {block_height}")

        # Optional stop condition
        # if block_height > STARTING_HEIGHT + 1000:
        #     break