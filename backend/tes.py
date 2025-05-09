from poseidon import poseidon


access_key="3b1fda5f-7e49-40ee-af2b-efcb123dff1d"
secret_key="1154e06f-269d-4778-808c-841ae310a5a8"
org_id="o17430663433591689"
asset_id="YzPnXh1Q"
api_gw=f"https://apim-sg1.envisioniot.com/enos-edge/v2.4/discovery/getNetConfig?orgId={org_id}&assetId={asset_id}"
req=poseidon.urlopen(access_key, secret_key, api_gw)









