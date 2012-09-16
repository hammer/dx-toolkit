"""
DXJob Handler
+++++++++++++

Jobs are DNAnexus entities that capture an instantiation of a running app or
applet. They can be created from either
:func:`dxpy.bindings.dxapplet.DXApplet.run` or
:func:`dxpy.bindings.dxapp.DXApp.run` if running an applet or app, or via
:func:`new_dxjob` or :func:`DXJob.new` in the special case of a job creating a
subjob.

"""

from dxpy.bindings import *

_test_harness_jobs = {}

#########
# DXJob #
#########

def new_dxjob(fn_input, fn_name, **kwargs):
    '''
    :param fn_input: Function input
    :type fn_input: dict
    :param fn_name: Name of the function to be called
    :type fn_name: string
    :rtype: :class:`~dxpy.bindings.dxjob.DXJob`

    Creates and enqueues a new job that will execute a particular function
    (from the same app as the one the current job is running). Returns the
    :class:`~dxpy.bindings.dxjob.DXJob` handle for the job.

    Note that this function is shorthand for::

        dxjob = DXJob()
        dxjob.new(fn_input, fn_name)

    .. note:: This method is intended for calls made from within already-executing jobs or apps.  If it is called from outside of an Execution Environment, an exception will be thrown.

    .. note:: If the environment variable ``DX_JOB_ID`` is not set, this method assmes that it is running within the debug harness, executes the job in place, and provides a debug job handler object that does not have a corresponding remote API job object.

    '''
    dxjob = DXJob()
    dxjob.new(fn_input, fn_name, **kwargs)
    return dxjob

class DXJob(DXObject):
    '''
    Remote job object handler.
    '''

    _class = "job"

    def __init__(self, dxid=None):
        self._test_harness_result = None
        if dxid is not None:
            self.set_id(dxid)

    def new(self, fn_input, fn_name, **kwargs):
        '''
        :param fn_input: Function input
        :type fn_input: dict
        :param fn_name: Name of the function to be called
        :type fn_name: string

        Creates and enqueues a new job that will execute a particular
        function (from the same app as the one the current job is
        running).

        .. note:: This method is intended for calls made from within already-executing jobs or apps.  If it is called from outside of an Execution Environment, an exception will be thrown.

        '''
        if 'DX_JOB_ID' in os.environ:
            req_input = {}
            req_input["input"] = fn_input
            req_input["function"] = fn_name
            resp = dxpy.api.jobNew(req_input, **kwargs)
            self.set_id(resp["id"])
        else:
            result = dxpy.run(function_name=fn_name, function_input=fn_input)
            self.set_id("job-" + str(len(_test_harness_jobs) + 1))
            _test_harness_jobs[self.get_id()] = self
            self._test_harness_result = result

    def set_id(self, dxid):
        '''
        :param dxid: Object ID
        :type dxid: string

        Discards the currently stored ID and associates the handler
        with *dxid*.
        '''
        self._dxid = dxid

    def get_id(self):
        '''
        :returns: Job ID of associated job
        :rtype: string

        Returns the job ID that the handler is currently associated
        with.

        '''

        return self._dxid

    def describe(self, io=True, **kwargs):
        """
        :param io: Include input and output fields in description
        :type io: bool
        :returns: Description of the job
        :rtype: dict

        Returns a hash that contains key-value pairs with information about the
        job, including its state and (optionally) its inputs and outputs. See
        the API documentation for the full list.

        """
        return dxpy.api.jobDescribe(self._dxid, {"io": io}, **kwargs)

    def wait_on_done(self, interval=2, timeout=sys.maxint, **kwargs):
        '''
        :param interval: Number of seconds between queries to the job's state
        :type interval: integer
        :param timeout: Max amount of time to wait until the job is done running
        :type timeout: integer
        :raises: :exc:`~dxpy.exceptions.DXError` if the timeout is reached before the job has finished running

        Waits until the job has finished running.
        '''

        elapsed = 0
        while True:
            state = self._get_state(**kwargs)
            if state == "done":
                break
            if state == "failed":
                raise DXJobFailureError("Job has failed.")
            if state == "terminated":
                raise DXJobFailureError("Job was terminated.")

            if elapsed >= timeout or elapsed < 0:
                raise DXJobFailureError("Reached timeout while waiting for the job to finish")

            time.sleep(interval)
            elapsed += interval

    def terminate(self, **kwargs):
        '''
        Terminates the associated job.
        '''
        dxpy.api.jobTerminate(self._dxid, **kwargs)

    def _get_state(self, **kwargs):
        '''
        :returns: State of the remote object
        :rtype: string

        Queries the API server for the job's state.

        Note that this function is shorthand for:

            dxjob.describe()["state"]

        '''

        return self.describe(io=False, **kwargs)["state"]
