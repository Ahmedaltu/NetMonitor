# Running NetMonitor as a Windows Service

## Requirements
- Python 3.x
- pywin32 (`pip install pywin32`)

## Install the Service

```sh
python netmonitor_service.py install
```

## Start the Service

```sh
python netmonitor_service.py start
```

## Stop the Service

```sh
python netmonitor_service.py stop
```

## Remove the Service

```sh
python netmonitor_service.py remove
```

## Logs
- Service logs are available in the Windows Event Viewer under `Application`.
