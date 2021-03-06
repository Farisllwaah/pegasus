"""
Contains the code to create and map objects to the Stampede DB schema
via a SQLAlchemy interface.
"""
__author__ = "Monte Goode MMGoode@lbl.gov"

import time
import warnings
import sys
import logging

from sqlalchemy import *
from sqlalchemy import MetaData, orm, func, exc
from sqlalchemy.orm import relation, backref

from Pegasus.db.schema import SABase, KeyInteger

log = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 4.0

metadata = MetaData()

# These are keywords that all tables should have
table_keywords = {}
table_keywords['mysql_charset'] = 'latin1'
table_keywords['mysql_engine'] = 'InnoDB'

def initializeToPegasusDB(db):
    # for SQLite
    warnings.filterwarnings('ignore', '.*does \*not\* support Decimal*.')

    # This is only required if you want to query using the domain objects
    # instead of the session
    #metadata.bind = db

    # Create all the tables if they don't exist
    metadata.create_all(db)

# Empty classes that will be populated and mapped
# to tables via the SQLAlch mapper.
class Host(SABase):
    pass

class Workflow(SABase):
    pass

class Workflowstate(SABase):
    pass

class Job(SABase):
    pass

class JobEdge(SABase):
    pass

class JobInstance(SABase):
    pass

class Jobstate(SABase):
    pass

class Task(SABase):
    pass

class TaskEdge(SABase):
    pass

class Invocation(SABase):
    pass

class File(SABase):
    pass

class SchemaInfo(SABase):
    pass


st_workflow = Table('workflow', metadata,
    # ==> Information comes from braindump.txt file
    Column('wf_id', KeyInteger, primary_key=True, nullable=False),
    Column('wf_uuid', VARCHAR(255), nullable=False),
    Column('dag_file_name', VARCHAR(255), nullable=True),
    Column('timestamp', NUMERIC(precision=16,scale=6), nullable=True),
    Column('submit_hostname', VARCHAR(255), nullable=True),
    Column('submit_dir', TEXT, nullable=True),
    Column('planner_arguments', TEXT, nullable=True),
    Column('user', VARCHAR(255), nullable=True),
    Column('grid_dn', VARCHAR(255), nullable=True),
    Column('planner_version', VARCHAR(255), nullable=True),
    Column('dax_label', VARCHAR(255), nullable=True),
    Column('dax_version', VARCHAR(255), nullable=True),
    Column('dax_file', VARCHAR(255), nullable=True),
    Column('parent_wf_id', KeyInteger, ForeignKey("workflow.wf_id", ondelete='CASCADE'), nullable=True),
    # not marked as FK to not screw up the cascade.
    Column('root_wf_id', KeyInteger, nullable=True),
    **table_keywords
)

Index('wf_id_KEY', st_workflow.c.wf_id, unique=True)
Index('wf_uuid_UNIQUE', st_workflow.c.wf_uuid, unique=True)

orm.mapper(Workflow, st_workflow, properties = {
    'child_wf':relation(Workflow, cascade='all, delete-orphan', passive_deletes=True),
    'child_wfs':relation(Workflowstate, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_host':relation(Host, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_task':relation(Task, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_job':relation(Job, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_invocation':relation(Invocation, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_task_e':relation(TaskEdge, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
    'child_job_e':relation(JobEdge, backref='st_workflow', cascade='all, delete-orphan', passive_deletes=True),
})


st_workflowstate = Table('workflowstate', metadata,
    # All three columns are marked as primary key to produce the desired
    # effect - ie: it is the combo of the three columns that make a row
    # unique.
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), nullable=False, primary_key=True),
    Column('state', Enum('WORKFLOW_STARTED', 'WORKFLOW_TERMINATED'), nullable=False, primary_key=True),
    Column('timestamp', NUMERIC(precision=16,scale=6), nullable=False, primary_key=True, default=time.time()),
    Column('restart_count', INT, nullable=False),
    Column('status', INT, nullable=True),
    **table_keywords
)

Index('UNIQUE_WORKFLOWSTATE',
    st_workflowstate.c.wf_id,
    st_workflowstate.c.state,
    st_workflowstate.c.timestamp,
    unique=True)

orm.mapper(Workflowstate, st_workflowstate)


# st_host definition
# ==> Information from kickstart output file
#
# site_name = <resource, from invocation element>
# hostname = <hostname, from invocation element>
# ip_address = <hostaddr, from invocation element>
# uname = <combined (system, release, machine) from machine element>
# total_ram = <ram_total from machine element>

st_host = Table('host', metadata,
    Column('host_id', KeyInteger, primary_key=True, nullable=False),
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), nullable=False),
    Column('site', VARCHAR(255), nullable=False),
    Column('hostname', VARCHAR(255), nullable=False),
    Column('ip', VARCHAR(255), nullable=False),
    Column('uname', VARCHAR(255), nullable=True),
    Column('total_memory', Integer, nullable=True),
    **table_keywords
)

Index('UNIQUE_HOST', st_host.c.wf_id, st_host.c.site, st_host.c.hostname, st_host.c.ip, unique=True)

orm.mapper(Host, st_host)


# static job table

st_job = Table('job', metadata,
    Column('job_id', KeyInteger, primary_key=True, nullable=False),
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), nullable=False),
    Column('exec_job_id', VARCHAR(255), nullable=False),
    Column('submit_file', VARCHAR(255), nullable=False),
    Column('type_desc', Enum('unknown',
                             'compute',
                             'stage-in-tx',
                             'stage-out-tx',
                             'registration',
                             'inter-site-tx',
                             'create-dir',
                             'staged-compute',
                             'cleanup',
                             'chmod',
                             'dax',
                             'dag'), nullable=False),
    Column('clustered', BOOLEAN, nullable=False),
    Column('max_retries', INT, nullable=False),
    Column('executable', TEXT, nullable=False),
    Column('argv', TEXT, nullable=True),
    Column('task_count', INT, nullable=False),
    **table_keywords
)

Index('job_id_KEY', st_job.c.job_id, unique=True)
Index('job_type_desc_COL', st_job.c.type_desc)
Index('job_exec_job_id_COL', st_job.c.exec_job_id)
Index('UNIQUE_JOB', st_job.c.wf_id, st_job.c.exec_job_id, unique=True)

orm.mapper(Job, st_job, properties = {
    'child_job_instance':relation(JobInstance, backref='st_job', cascade='all, delete-orphan', passive_deletes=True, lazy=True)
})



st_job_edge = Table('job_edge', metadata,
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('parent_exec_job_id', VARCHAR(255), primary_key=True, nullable=False),
    Column('child_exec_job_id', VARCHAR(255), primary_key=True, nullable=False),
    **table_keywords
)

Index('UNIQUE_JOB_EDGE',
    st_job_edge.c.wf_id,
    st_job_edge.c.parent_exec_job_id,
    st_job_edge.c.child_exec_job_id,
    unique=True)

orm.mapper(JobEdge, st_job_edge)


st_job_instance = Table('job_instance', metadata,
    Column('job_instance_id', KeyInteger, primary_key=True, nullable=False),
    Column('job_id', KeyInteger, ForeignKey('job.job_id', ondelete='CASCADE'), nullable=False),
    Column('host_id', KeyInteger, ForeignKey('host.host_id', ondelete='SET NULL'), nullable=True),
    Column('job_submit_seq', INT, nullable=False),
    Column('sched_id', VARCHAR(255), nullable=True),
    Column('site', VARCHAR(255), nullable=True),
    Column('user', VARCHAR(255), nullable=True),
    Column('work_dir', TEXT, nullable=True),
    Column('cluster_start', NUMERIC(16,6), nullable=True),
    Column('cluster_duration', NUMERIC(10,3), nullable=True),
    Column('local_duration', NUMERIC(10,3), nullable=True),
    Column('subwf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='SET NULL'), nullable=True),
    Column('stdout_file', VARCHAR(255), nullable=True),
    Column('stdout_text', TEXT, nullable=True),
    Column('stderr_file', VARCHAR(255), nullable=True),
    Column('stderr_text', TEXT, nullable=True),
    Column('stdin_file', VARCHAR(255), nullable=True),
    Column('multiplier_factor', INT, nullable=False, default=1),
    Column('exitcode', INT, nullable=True),
    **table_keywords
)

Index('job_instance_id_KEY',
    st_job_instance.c.job_instance_id,
    unique=True)
Index('UNIQUE_JOB_INSTANCE',
    st_job_instance.c.job_id,
    st_job_instance.c.job_submit_seq,
    unique=True)

orm.mapper(JobInstance, st_job_instance, properties = {
    #PM-712 don't want merges to happen to invocation table .
    #setting lazy = false leads to a big join query when a job_instance is updated
    #with the postscript status.
    'child_tsk':relation(Invocation, backref='st_job_instance', cascade='all, delete-orphan', passive_deletes=True, lazy=True),
    'child_jst':relation(Jobstate, backref='st_job_instance', cascade='all, delete-orphan', passive_deletes=True, lazy=True),
})

# st_jobstate definition
# ==> Same information that currently goes into jobstate.log file,
#       obtained from dagman.out file
#
# job_id = from st_job table (autogenerated)
# state = from dagman.out file (3rd column of jobstate.log file)
# timestamp = from dagman,out file (1st column of jobstate.log file)

st_jobstate = Table('jobstate', metadata,
    # All four columns are marked as primary key to produce the desired
    # effect - ie: it is the combo of the four columns that make a row
    # unique.
    Column('job_instance_id', KeyInteger, ForeignKey('job_instance.job_instance_id', ondelete='CASCADE'), nullable=False, primary_key=True),
    Column('state', VARCHAR(255), nullable=False, primary_key=True),
    Column('timestamp', NUMERIC(precision=16,scale=6), nullable=False, primary_key=True, default=time.time()),
    Column('jobstate_submit_seq', INT, nullable=False, primary_key=True),
    **table_keywords
)

Index('UNIQUE_JOBSTATE',
    st_jobstate.c.job_instance_id,
    st_jobstate.c.state,
    st_jobstate.c.timestamp,
    st_jobstate.c.jobstate_submit_seq,
    unique=True)

orm.mapper(Jobstate, st_jobstate)


st_task = Table('task', metadata,
    Column('task_id', KeyInteger, primary_key=True, nullable=False),
    Column('job_id', KeyInteger, ForeignKey('job.job_id', ondelete='SET NULL'), nullable=True),
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), nullable=False),
    Column('abs_task_id', VARCHAR(255), nullable=False),
    Column('transformation', TEXT, nullable=False),
    Column('argv', TEXT, nullable=True),
    Column('type_desc', VARCHAR(255), nullable=False),
    **table_keywords
)

Index('task_id_KEY', st_task.c.task_id, unique=True)
Index('task_abs_task_id_COL', st_task.c.abs_task_id)
Index('task_wf_id_COL', st_task.c.wf_id)
Index('UNIQUE_TASK', st_task.c.wf_id, st_task.c.abs_task_id, unique=True)

orm.mapper(Task, st_task, properties = {
    'child_file':relation(File, backref='st_task', cascade='all, delete-orphan', passive_deletes=True),
})


st_task_edge = Table('task_edge', metadata,
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('parent_abs_task_id', VARCHAR(255), primary_key=True, nullable=True),
    Column('child_abs_task_id', VARCHAR(255), primary_key=True, nullable=True),
    **table_keywords
)

Index('UNIQUE_TASK_EDGE',
    st_task_edge.c.wf_id,
    st_task_edge.c.parent_abs_task_id,
    st_task_edge.c.child_abs_task_id,
    unique=True)

orm.mapper(TaskEdge, st_task_edge)


st_invocation = Table('invocation', metadata,
    Column('invocation_id', KeyInteger, primary_key=True, nullable=False),
    Column('job_instance_id', KeyInteger, ForeignKey('job_instance.job_instance_id', ondelete='CASCADE'), nullable=False),
    Column('task_submit_seq', INT, nullable=False),
    Column('start_time', NUMERIC(16,6), nullable=False, default=time.time()),
    Column('remote_duration', NUMERIC(10,3), nullable=False),
    Column('remote_cpu_time', NUMERIC(10,3), nullable=True),
    Column('exitcode', INT, nullable=False),
    Column('transformation', TEXT, nullable=False),
    Column('executable', TEXT, nullable=False),
    Column('argv', TEXT, nullable=True),
    Column('abs_task_id', VARCHAR(255), nullable=True),
    Column('wf_id', KeyInteger, ForeignKey('workflow.wf_id', ondelete='CASCADE'), nullable=False),
    **table_keywords
)

Index('invocation_id_KEY', st_invocation.c.invocation_id, unique=True)
Index('invoc_abs_task_id_COL', st_invocation.c.abs_task_id)
Index('invoc_wf_id_COL', st_invocation.c.wf_id)
Index('UNIQUE_INVOCATION', st_invocation.c.job_instance_id, st_invocation.c.task_submit_seq, unique=True)

orm.mapper(Invocation, st_invocation)


st_file = Table('file', metadata,
    # ==> Information will come from kickstart output file
    Column('file_id', KeyInteger, primary_key=True, nullable=False),
    Column('task_id', KeyInteger, ForeignKey('task.task_id', ondelete='CASCADE'), nullable=True),
    Column('lfn', VARCHAR(255), nullable=True),
    Column('estimated_size', INT, nullable=True),
    Column('md_checksum', VARCHAR(255), nullable=True),
    Column('type', VARCHAR(255), nullable=True),
    **table_keywords
)

Index('file_id_UNIQUE', st_file.c.file_id, unique=True)
Index('FK_FILE_TASK_ID', st_task.c.task_id, unique=False)

orm.mapper(File, st_file)


st_schema_info = Table('schema_info', metadata,
    Column('version_number', NUMERIC(2,1), primary_key=True, nullable=False),
    Column('version_timestamp', NUMERIC(16,6), primary_key=True, nullable=False, default=time.time())
)

orm.mapper(SchemaInfo, st_schema_info)

