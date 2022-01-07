import pytest
from mock.mock import Mock

from dls_barcode.camera.scanner_message import ScanErrorMessage
from dls_barcode.frame_processor import SideProcessor, TopProcessor
from dls_barcode.scan.scan_result import ScanResult

@pytest.fixture(scope='module')
def side_processor():
    side_camera_stream = Mock()
    side_frame = Mock()
    side_processor = SideProcessor(side_camera_stream, side_frame)
    yield side_processor

@pytest.fixture(scope='module')
def top_processor():
    top_camera_stream = Mock()
    top_frame = Mock()
    top_processor = TopProcessor(top_camera_stream, top_frame)
    yield top_processor

def test_error_signal_is_emitted_when_result_has_error(qtbot, side_processor): # this functionality is not used ??
    side_result = ScanResult(1)
    side_result._error = ScanErrorMessage("error")
    side_processor._side_camera_stream.process_frame = Mock(return_value=side_result)
    with qtbot.waitSignal(side_processor.side_scan_error_signal,timeout=100) as blocker:
        side_processor.run()

    assert blocker.args, "error"
    assert blocker.signal_triggered, "side_scan_error_signal"

def test_side_result_signal_emitted(qtbot, side_processor):
    side_result = ScanResult(1)
    side_result._error = None
    side_result.has_valid_barcodes = Mock(return_value=True)
    side_processor._side_camera_stream.process_frame = Mock(return_value=side_result)
    with qtbot.waitSignal(side_processor.side_result_signal,timeout=100) as blocker:
        side_processor.run()

    assert blocker.signal_triggered, "side_result_signal"

def test_top_result_signal_emitted_if_result_successful(qtbot, top_processor):
    top_result = ScanResult(1)
    top_result.success = Mock(return_value = True)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    with qtbot.waitSignal(top_processor.top_result_signal,timeout=100) as blocker:
        top_processor.run()
        
    assert blocker.signal_triggered, "top_result_signal"

def test_top_result_signal_not_emitted_if_result_not_successful(qtbot, top_processor):
    top_result = ScanResult(1)
    top_result.success = Mock(return_value=False)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    with qtbot.assertNotEmitted(top_processor.top_result_signal):
        top_processor.run()

def test_full_and_valid_signal_emitted_if_result_full_valid(qtbot, top_processor):
    top_result = ScanResult(1)
    top_result.success = Mock(return_value = True)
    top_result.is_full_valid = Mock(return_value = True)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    with qtbot.waitSignal(top_processor.full_and_valid_signal, timeout=100) as blocker:
        top_processor.run()
        
    assert blocker.signal_triggered, "full_and_valid_signal"
    
def test_full_and_valid_not_emmited_it_result_not_successful(qtbot, top_processor):
    top_result = ScanResult(1)
    top_result.success = Mock(return_value=False)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    with qtbot.assertNotEmitted(top_processor.full_and_valid_signal):
        top_processor.run()
        
def test_full_and_valid_not_emmited_it_result_successful_but_not_full_valid(qtbot, top_processor):
    top_result = ScanResult(1)
    top_result.success = Mock(return_value=True)
    top_result.is_full_valid = Mock(return_value=False)
    top_processor._top_camera_stream.process_frame = Mock(return_value=top_result)
    with qtbot.assertNotEmitted(top_processor.full_and_valid_signal):
        top_processor.run()