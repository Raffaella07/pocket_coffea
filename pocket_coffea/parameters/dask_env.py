def setup_dask(dask_config):
    dask_config.set({"distributed.scheduler.allowed-failures": 10})
    dask_config.set({"distributed.scheduler.work-stealing": True})
    dask_config.set({"distributed.scheduler.default-task-durations.processor": "60s"})
    dask_config.set({"distributed.scheduler.default-task-durations.reduce": "10s"})
    dask_config.set({"distributed.worker.memory.target": 0.8})
    dask_config.set({"distributed.worker.memory.spill": 0.9})
    dask_config.set({"distributed.worker.memory.pause": 0.92})
    dask_config.set({"distributed.worker.memory.terminate": 0})
    dask_config.set({"distributed.worker.profile.interval": "1d"})
    dask_config.set({"distributed.worker.profile.cycle": "2d"})
    dask_config.set({"distributed.worker.profile.low-level": False})
    dask_config.set({"distributed.diagnostics.nvml": False})
