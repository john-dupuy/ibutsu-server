import json
import tarfile
import time
from datetime import datetime
from io import BytesIO

from dateutil import parser
from ibutsu_server.db.base import session
from ibutsu_server.db.models import Artifact
from ibutsu_server.db.models import Import
from ibutsu_server.db.models import ImportFile
from ibutsu_server.db.models import Result
from ibutsu_server.db.models import Run
from ibutsu_server.tasks import task
from ibutsu_server.tasks.runs import update_run
from ibutsu_server.util.projects import get_project_id
from ibutsu_server.util.uuid import convert_objectid_to_uuid
from ibutsu_server.util.uuid import is_uuid
from lxml import objectify


def _create_result(tar, run_id, result, artifacts):
    """Create a result with artifacts, used in the archive importer"""
    old_id = None
    result_id = convert_objectid_to_uuid(result.get("id"))
    if is_uuid(result_id):
        result_record = session.query(Result).get(result_id)
    else:
        result_record = None
    if result_record:
        result_record.data["metadata"]["run"] = run_id
    else:
        old_id = result["id"]
        if "id" in result:
            result.pop("id")
        result["metadata"]["run"] = run_id
        result_record = Result.from_dict(result)
    session.add(result_record)
    session.commit()
    result = result_record.to_dict()
    for artifact in artifacts:
        session.add(
            Artifact(
                data={
                    "filename": "traceback.log",
                    "metadata": {"contentType": "text/plain", "resultId": result["id"]},
                },
                content=tar.extractfile(artifact).read(),
            )
        )
    session.commit()
    return old_id


def _update_import_status(import_record, status):
    """Update the status of the import"""
    import_record.data["status"] = status
    session.add(import_record)
    session.commit()


@task
def run_junit_import(import_):
    """Import a test run from a JUnit file"""
    # Update the status of the import
    import_record = session.query(Import).get(import_["id"])
    _update_import_status(import_record, "running")
    # Fetch the file contents
    import_file = (
        session.query(ImportFile)
        .filter(ImportFile.data["metadata"]["import_id"] == import_["id"])
        .first()
    )
    if not import_file:
        _update_import_status(import_record, "error")
        return
    # Parse the XML and create a run object(s)
    tree = objectify.parse(import_file.content)
    root = tree.getroot()
    import_record.data["run_id"] = []
    for testsuite in root.testsuite:
        run_dict = {
            "created": datetime.fromtimestamp(time.time()).isoformat(),
            "start_time": parser.parse(testsuite.get("timestamp")).strftime("%s"),
            "duration": testsuite.get("time"),
            "summary": {
                "errors": testsuite.get("errors"),
                "failures": testsuite.get("failures"),
                "skips": testsuite.get("skipped"),
                "tests": testsuite.get("tests"),
            },
        }
        # Insert the run, and then update the import with the run id
        run = Run(data=run_dict)
        session.add(run)
        session.commit()
        run_dict = run.to_dict()
        import_record.data["run_id"].append(run.id)
        # Import the contents of the XML file
        for testcase in testsuite.testcase:
            test_name = testcase.get("name").split(".")[-1]
            if testcase.get("classname"):
                test_name = testcase.get("classname").split(".")[-1] + "." + test_name
            result_dict = {
                "test_id": test_name,
                "start_time": run["start_time"],
                "duration": float(testcase.get("time")),
                "metadata": {
                    "run": run.id,
                    "fspath": testcase.get("file"),
                    "line": testcase.get("line"),
                },
                "params": {},
                "source": testsuite.get("name"),
            }
            skip_reason, traceback = None, None
            if testcase.find("failure"):
                result_dict["result"] = "failed"
                traceback = bytes(str(testcase.failure), "utf8")
            elif testcase.find("error"):
                result_dict["result"] = "error"
                traceback = bytes(str(testcase.error), "utf8")
            elif testcase.find("skipped"):
                result_dict["result"] = "skipped"
                skip_reason = str(testcase.skipped)
            else:
                result_dict["result"] = "passed"
            if skip_reason:
                result_dict["metadata"]["skip_reason"] = skip_reason

            result = Result(data=result_dict)
            session.add(result)
            session.commit()

            if traceback:
                session.add(
                    Artifact(
                        data={
                            "filename": "traceback.log",
                            "metadata": {"contentType": "text/plain", "resultId": result.id},
                        },
                        content=traceback,
                    )
                )
            if testcase.find("system-out"):
                system_out = bytes(str(testcase["system-out"]), "utf8")
                session.add(
                    Artifact(
                        data={
                            "filename": "system-out.log",
                            "metadata": {"contentType": "text/plain", "resultId": result.id},
                        },
                        content=system_out,
                    )
                )
            if testcase.find("system-err"):
                system_err = bytes(str(testcase["system-err"]), "utf8")
                session.add(
                    Artifact(
                        data={
                            "filename": "system-err.log",
                            "metadata": {"contentType": "text/plain", "resultId": result.id},
                        },
                        content=system_err,
                    )
                )
            session.commit()
    _update_import_status(import_record, "done")


@task
def run_archive_import(import_):
    """Import a test run from an Ibutsu archive file"""
    # Update the status of the import
    import_record = session.query(Import).get(str(import_["id"]))
    _update_import_status(import_record, "running")
    # Fetch the file contents
    import_file = (
        session.query(ImportFile)
        .filter(ImportFile.data["metadata"]["import_id"] == import_["id"])
        .first()
    )
    if not import_file:
        _update_import_status(import_record, "error")
        return

    # First open the tarball and pull in the results
    run = None
    run_dict = None
    results = []
    result_artifacts = {}
    current_dir = None
    result = None
    artifacts = []
    start_time = None
    file_object = BytesIO(import_file.content)
    with tarfile.open(mode="r:gz", fileobj=file_object) as tar:
        # run through the files and dirs, skipping the first one as it is the base directory
        for member in tar.getmembers()[1:]:
            if member.isdir() and member.name != current_dir:
                if result:
                    results.append(result)
                    result_artifacts[result["id"]] = artifacts
                artifacts = []
                result = None
            elif member.name.endswith("result.json"):
                result = json.loads(tar.extractfile(member).read())
                result_start_time = result.get("start_time", result.get("starttime"))
                if not start_time or start_time > result_start_time:
                    start_time = result_start_time
            elif member.name.endswith("run.json"):
                run = json.loads(tar.extractfile(member).read())
            elif member.isfile():
                artifacts.append(member)
        if result:
            results.append(result)
            result_artifacts[result["id"]] = artifacts
        if run:
            run_dict = run
        else:
            run_dict = {
                "duration": 0,
                "summary": {"errors": 0, "failures": 0, "skips": 0, "tests": 0},
            }
        # patch things up a bit, if necessary
        if run_dict.get("id"):
            run_dict["id"] = convert_objectid_to_uuid(run_dict["id"])
        if run_dict.get("start_time") and not run_dict.get("created"):
            run_dict["created"] = run_dict["start_time"]
        elif run_dict.get("created") and not run_dict.get("start_time"):
            run_dict["start_time"] = run_dict["created"]
        elif not run_dict.get("created") and not run_dict.get("start_time"):
            run_dict["created"] = start_time
            run_dict["start_time"] = start_time
        if run_dict.get("metadata", {}).get("project"):
            run_dict["metadata"]["project"] = get_project_id(run_dict["metadata"]["project"])
        # If this run has a valid ObjectId, check if this run exists
        if is_uuid(run_dict.get("id")):
            run = session.query(Run).get(run_dict["id"])
        if run:
            run.update(run_dict)
        else:
            run = Run(id=run_dict["id"], data=run_dict)
        session.add(run)
        session.commit()
        run_dict = run.to_dict()
        import_record.data["run_id"] = [run.id]
        # Now loop through all the results, and create or update them
        for result in results:
            artifacts = result_artifacts.get(result["id"], [])
            _create_result(tar, run.id, result, artifacts)
    # Update the import record
    _update_import_status(import_record, "done")
    if run:
        update_run.delay(run.id)
