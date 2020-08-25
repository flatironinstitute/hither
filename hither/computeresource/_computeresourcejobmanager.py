from hither import computeresource
from typing import Dict, Any
import hither as hi
import kachery_p2p as kp
from ..job import Job, JobStatus
from .._enums import SerializedJobKeys
from .._serialize_job import _deserialize_job

class ComputeResourceJobManager:
    def __init__(self, compute_resource_job_handlers: Dict[str, Any]):
        # jobs by job_hash
        self._jobs_by_job_hash: Dict[str, Job] = {}
        self._cr_job_handlers = compute_resource_job_handlers
    def add_job(self, job_hash, job_serialized) -> Job:
        job = None
        if job_hash in self._jobs_by_job_hash:
            job = self._jobs_by_job_hash[job_hash]
            if job._status == JobStatus.ERROR:
                create_new_job = True
            else:
                create_new_job = False
        else:
            create_new_job = True
        if create_new_job:
            job = _deserialize_job(
                serialized_job=job_serialized,
                job_handler=None,
                job_cache=None,
                job_manager=None
            )
            self._jobs_by_job_hash[job_hash] = job
            code_uri = job_serialized[SerializedJobKeys.CODE_URI]
            if code_uri is not None:
                code = kp.load_object(code_uri)
                if code is None:
                    exception = Exception(f'Unable to load code from URI: {code_uri}')
                    job._set_error_status(exception=exception, runtime_info=dict())
            if job.get_status() is not JobStatus.ERROR:
                job._set_status(JobStatus.QUEUED)
                job._job_handler = self._cr_job_handlers['default']
                job._job_handler.handle_job(job)
        assert job is not None
        return job
    def iterate(self):
        for jh in self._cr_job_handlers.values():
            jh.iterate()
        # todo: periodic cleanup of jobs_by_job_hash