# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest
from mock import MagicMock

from indico_livesync.models.queue import LiveSyncQueueEntry, ChangeType
from indico_livesync.uploader import Uploader, MARCXMLUploader


class RecordingUploader(Uploader):
    """An uploader which logs each 'upload'"""
    def __init__(self, *args, **kwargs):
        super(RecordingUploader, self).__init__(*args, **kwargs)
        self._uploaded = []
        self.logger = MagicMock()

    def upload_records(self, records, from_queue):
        self._uploaded.append((records, from_queue))


class FailingUploader(RecordingUploader):
    """An uploader where the second batch fails"""
    def __init__(self, *args, **kwargs):
        super(FailingUploader, self).__init__(*args, **kwargs)
        self._n = 0

    def upload_records(self, records, from_queue):
        super(FailingUploader, self).upload_records(records, from_queue)
        self._n += 1
        if self._n == 2:
            raise Exception('All your data are belong to us!')


@pytest.fixture(autouse=True)
def mock_resolved_zodb_objects(mocker):
        mocker.patch.object(LiveSyncQueueEntry, 'object', autospec=True)


def test_run_initial(mocker):
    """Test the initial upload"""
    mocker.patch.object(Uploader, 'processed_records', autospec=True)
    uploader = RecordingUploader(MagicMock())
    uploader.INITIAL_BATCH_SIZE = 3
    records = tuple(LiveSyncQueueEntry(change=ChangeType.created, type='event', event_id=evt_id)
                    for evt_id in xrange(4))
    uploader.run_initial(records)
    # We expect two batches, with the second one being smaller (i.e. no None padding, just the events)
    refs = tuple(record.object_ref for record in records)
    batches = refs[:3], refs[3:]
    assert len(batches[0]) > len(batches[1])
    assert uploader._uploaded == [(batches[0], False), (batches[1], False)]
    # During an initial export there are no records to mark as processed
    assert not uploader.processed_records.called


def test_run(mocker):
    """Test uploading queued data"""
    db = mocker.patch('indico_livesync.uploader.db')
    uploader = RecordingUploader(MagicMock())
    uploader.BATCH_SIZE = 3
    records = tuple(
        LiveSyncQueueEntry(change=ChangeType.created, type='event', event_id=evt_id) for evt_id in xrange(4))
    uploader.run(records)
    refs = tuple(record.object_ref for record in records)
    batches = refs[:3], refs[3:]
    assert uploader._uploaded == [(batches[0], True), (batches[1], True)]
    # All records should be marked as processed
    assert all(record.processed for record in records)
    # Marking records as processed is committed immediately
    assert db.session.commit.call_count == 2


def test_run_failing(mocker):
    """Test a failing queue run"""
    db = mocker.patch('indico_livesync.uploader.db')
    uploader = FailingUploader(MagicMock())
    uploader.BATCH_SIZE = 3
    records = tuple(
        LiveSyncQueueEntry(change=ChangeType.created, type='event', event_id=evt_id) for evt_id in xrange(10))
    uploader.run(records)
    refs = tuple(record.object_ref for record in records)
    assert uploader.logger.exception.called
    # No uploads should happen after a failed batch
    assert uploader._uploaded == [(refs[:3], True), (refs[3:6], True)]
    # Only successful records should be marked as processed
    assert all(record.processed for record in records[:3])
    assert not any(record.processed for record in records[3:])
    # Only the first uccessful batch should have triggered a commit
    assert db.session.commit.call_count == 1


def test_marcxml_run(mocker):
    """Text if the MARCXML uploader uses the correct function"""
    mocker.patch('indico_livesync.uploader.db')
    mocker.patch.object(MARCXMLUploader, 'upload_xml', autospec=True)
    mxg = mocker.patch('indico_livesync.uploader.MARCXMLGenerator')
    uploader = MARCXMLUploader(MagicMock())
    uploader.run([LiveSyncQueueEntry(change=ChangeType.created)])
    assert mxg.records_to_xml.called
    assert not mxg.objects_to_xml.called
    assert uploader.upload_xml.called
    mxg.reset_mock()
    uploader.run_initial([LiveSyncQueueEntry(change=ChangeType.created)])
    assert not mxg.records_to_xml.called
    assert mxg.objects_to_xml.called
    assert uploader.upload_xml.called


def test_marcxml_empty_result(mocker):
    """Test if the MARCXML uploader doesn't upload empty records"""
    mocker.patch('indico_livesync.uploader.MARCXMLGenerator.objects_to_xml', return_value=None)
    mocker.patch.object(MARCXMLUploader, 'upload_xml', autospec=True)
    uploader = MARCXMLUploader(MagicMock())
    uploader.run_initial([LiveSyncQueueEntry(change=ChangeType.created)])
    assert not uploader.upload_xml.called
