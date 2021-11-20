from uvicorn.workers import UvicornWorker


class CloudRunUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {"forwarded_allow_ips": "*"}
