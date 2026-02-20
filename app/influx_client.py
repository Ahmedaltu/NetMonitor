from influxdb_client import InfluxDBClient, WriteOptions
from app.config.config import TOKEN, ORG, URL

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=WriteOptions(batch_size=1))
