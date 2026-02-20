# Running NetMonitor in Docker

## Build the Docker Image

```sh
docker build -t netmonitor .
```

## Run the Container

```sh
docker run -d \
  --name netmonitor \
  -e INFLUX_TOKEN=your_token_here \
  netmonitor
```

- The container will run the monitor using your config.yaml.
- You can mount a custom config file or set environment variables as needed.

## Example: Mounting a Custom Config

```sh
docker run -d \
  --name netmonitor \
  -v /path/to/your/config.yaml:/app/config.yaml \
  -e INFLUX_TOKEN=your_token_here \
  netmonitor
```
