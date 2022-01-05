import pytest
from dls_barcode.camera.scanner_message import ScanErrorMessage
from dls_barcode.frame_processor import SideProcessor
from mock.mock import Mock

from dls_barcode.scan.scan_result import ScanResult

@pytest.fixture(scope='module')
def side_processor():
    side_camera_stream = Mock()
    side_frame = Mock()
    side_processor = SideProcessor(side_camera_stream, side_frame)
    yield side_processor


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