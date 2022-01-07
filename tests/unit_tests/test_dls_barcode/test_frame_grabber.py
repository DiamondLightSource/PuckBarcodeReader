import pytest
from mock.mock import MagicMock, Mock

from dls_barcode.frame_grabber import FrameGrabber
from dls_util.cv.frame import Frame

@pytest.fixture(scope='module')
def frame_grabber():
    side_camera_stream = Mock()
    top_camera_stream = Mock()
    frame_grabber = FrameGrabber(side_camera_stream, top_camera_stream)
    yield frame_grabber
    
def test_finished_signal_emitted_if_run_flag_down(qtbot, frame_grabber):
    frame_grabber._run_flag = False
    with qtbot.waitSignal(frame_grabber.finished, timeout=100) as blocker:
        frame_grabber.run()
    assert blocker.signal_triggered, "finished"        
    
def test_new_side_frame_not_emited_if_run_flag_down(qtbot, frame_grabber):
    frame_grabber._run_flag = False
    with qtbot.assertNotEmitted(frame_grabber.new_side_frame):
        frame_grabber.run()
        
def test_new_side_frame_emitted_if_side_frame_not_none(qtbot, frame_grabber):
    side_frame = Frame(MagicMock())
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=side_frame)
    frame_grabber._top_camera_stream.get_frame = Mock(return_value=None)
    with qtbot.waitSignal(frame_grabber.new_side_frame, timeout=100) as blocker:
        frame_grabber.run()
        
    assert blocker.signal_triggered, "new_side_frame"
    
def test_camera_error_emitted_if_side_frame_is_none(qtbot, frame_grabber):
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=None)
    with qtbot.waitSignal(frame_grabber.camera_error, timeout=100) as blocker:
        frame_grabber.run()
        
    assert blocker.signal_triggered, "camera_error"
    
def test_finished_emitted_if_side_frame_is_none(qtbot, frame_grabber):
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=None)
    with qtbot.waitSignal(frame_grabber.finished) as blocker:
        frame_grabber.run()
        
    assert blocker.signal_triggered, "finished"
    
def test_new_top_frame_not_emitted_if_top_frame_none(qtbot, frame_grabber):
    side_frame = Frame(MagicMock())
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=side_frame)
    frame_grabber._top_camera_stream.get_frame = Mock(return_value=None)
    with qtbot.assertNotEmitted(frame_grabber.new_top_frame):
        frame_grabber.run()

def test_camera_error_emitted_if_top_frame_is_none(qtbot, frame_grabber):
    side_frame = Frame(MagicMock())
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=side_frame)
    frame_grabber._top_camera_stream.get_frame = Mock(return_value=None)
    with qtbot.waitSignal(frame_grabber.camera_error, timeout=100) as blocker:
        frame_grabber.run()
        
    assert blocker.signal_triggered, "camera_error"
    
def test_new_side_emitted_if_both_frames_not_none(qtbot, frame_grabber):
    # no test for new_top_frame still - infinite loop
    side_frame = Frame(MagicMock())
    top_frame = Frame(MagicMock())
    frame_grabber._side_camera_stream.get_frame = Mock(return_value=side_frame)
    frame_grabber._top_camera_stream.get_frame = Mock(return_value=top_frame, side_effect=frame_grabber.stop)
    with qtbot.waitSignal(frame_grabber.new_side_frame, timeout=100) as blocker:
        frame_grabber.run()
    assert blocker.signal_triggered, "new_side_frame"
