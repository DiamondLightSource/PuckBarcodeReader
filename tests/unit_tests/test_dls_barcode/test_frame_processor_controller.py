import pytest
from mock.mock import MagicMock, Mock

from dls_barcode.frame_processor_controller import FrameProcessorController
from dls_barcode.scan.scan_result import ScanResult

@pytest.fixture(scope='module')
def frame_processor_side_camera_stream():
    config = Mock()
    config.get_top_camera_tiemout=MagicMock(return_value = 10)
    manager = Mock()
    manager.side_camera_stream = Mock()
    manager.side_camera_stream.process_frame = MagicMock(return_value = ScanResult(1))
    frame_processor = FrameProcessorController(manager, config, 
                                               Mock(), Mock(), 
                                               Mock(), Mock(), 
                                               Mock(), Mock(), Mock())
    yield frame_processor
    
@pytest.fixture(scope='module')
def frame_processor_top_camera_stream():
    config = Mock()
    config.get_top_camera_tiemout=MagicMock(return_value = 10)
    manager = Mock()
    manager.top_camera_stream = Mock()
    manager.top_camera_stream.process_frame = MagicMock(return_value = ScanResult(1))
    frame_processor = FrameProcessorController(manager, config, 
                                               Mock(), Mock(), 
                                               Mock(), Mock(), 
                                               Mock(), Mock(), Mock())
    yield frame_processor

#fixture 1
def test_side_processor_therad_starts_if_top_processor_thread_is_not_running(qtbot, frame_processor_side_camera_stream):
    frame_processor_side_camera_stream.top_processor_thread.isRunning = MagicMock(return_value = False)
    with qtbot.waitSignal(frame_processor_side_camera_stream.side_processor_thread.started, timeout=100) as blocker:
        frame_processor_side_camera_stream.start_processor(Mock(), Mock())
    assert blocker.signal_triggered, "started"
    
def test_side_processor_therad_doesnt_start_if_top_processor_is_running(qtbot, frame_processor_side_camera_stream):
    frame_processor_side_camera_stream.top_processor_thread.isRunning = MagicMock(return_value = True)
    with qtbot.assertNotEmitted(frame_processor_side_camera_stream.side_processor_thread.started):
        frame_processor_side_camera_stream.start_processor(Mock(), Mock())

# fixture 2       
def test_process_side_triggers_top_processor_thread_if_processing_flag_is_on(qtbot, frame_processor_top_camera_stream):
    frame_processor_top_camera_stream.processing_flag = True
    frame_processor_top_camera_stream.timer.isActive = MagicMock(return_value = True)
    with qtbot.waitSignal(frame_processor_top_camera_stream.top_processor_thread.started) as blocker:
        frame_processor_top_camera_stream.process_side(MagicMock())
    
    assert blocker.signal_triggered, "started"
    
def test_process_side_starts_timer_if_not_active(qtbot, frame_processor_top_camera_stream):
    
    frame_processor_top_camera_stream.processing_flag = True
    frame_processor_top_camera_stream.timer.start = Mock()
    frame_processor_top_camera_stream.timer.isActive = MagicMock(return_value = False)
    with qtbot.waitSignal(frame_processor_top_camera_stream.top_processor_thread.started):
        frame_processor_top_camera_stream.process_side(MagicMock())

    assert frame_processor_top_camera_stream.timer.start.call_count == 1
    assert frame_processor_top_camera_stream.startCountdown.call_count == 1
    assert frame_processor_top_camera_stream.clear_frame.call_count == 1
    
def test_on_time_out_sets_processing_flag_to_false( frame_processor_side_camera_stream):
    frame_processor_side_camera_stream.processing_flag = True
    frame_processor_side_camera_stream._side_result = Mock(return_value = ScanResult(1))
    
    frame_processor_side_camera_stream._on_time_out()
    
    assert frame_processor_side_camera_stream.processing_flag == False
    
def test_on_time_out_triggers_scan_timeout_if_holder_barcode_not_new( frame_processor_side_camera_stream):
    frame_processor_side_camera_stream._side_result = Mock(return_value = ScanResult(1))
    frame_processor_side_camera_stream.is_latest_holder_barcode = Mock(return_value = False)
    
    frame_processor_side_camera_stream._on_time_out()
    
    assert frame_processor_side_camera_stream.displayScanTimeoutMessage.call_count == 1
    assert frame_processor_side_camera_stream.displayPuckScanCompleteMessage.call_count == 0
    
def test_on_time_out_triggers_scan_complete_for_new_holder_barcode(frame_processor_side_camera_stream):

    frame_processor_side_camera_stream._side_result = Mock(return_value = ScanResult(1))
    frame_processor_side_camera_stream.is_latest_holder_barcode = Mock(return_value = True)
    
    frame_processor_side_camera_stream._on_time_out()
    
    assert frame_processor_side_camera_stream.displayPuckScanCompleteMessage.call_count == 1
    assert frame_processor_side_camera_stream.displayScanTimeoutMessage.call_count == 0
    
def test_set_top_processing_flag_only_sets_the_flag_if_a_new_holder_barcode_detected(frame_processor_side_camera_stream):
    frame_processor_side_camera_stream.processing_flag = False
    frame_processor_side_camera_stream._side_result = Mock(return_value = ScanResult(1))
    frame_processor_side_camera_stream.is_latest_holder_barcode = Mock(return_value = True)
    
    frame_processor_side_camera_stream._set_top_porcessing_flag()
    
    assert frame_processor_side_camera_stream.processing_flag == False
    
    frame_processor_side_camera_stream.is_latest_holder_barcode = Mock(return_value = False)
    
    frame_processor_side_camera_stream._set_top_porcessing_flag()
    
    assert frame_processor_side_camera_stream.processing_flag == True