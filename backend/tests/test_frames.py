from halo.media.frames import extract_audio, extract_frames, frame_timestamps, probe_duration


def test_timestamps_weight_the_hook():
    ts = frame_timestamps(30.0, 8)
    assert ts[:3] == [0.3, 1.5, 3.0]
    assert len(ts) == 8
    assert ts == sorted(ts)
    assert ts[-1] < 30.0


def test_timestamps_short_video():
    assert frame_timestamps(1.0, 8) == [0.3, 0.97]
    assert frame_timestamps(0.4, 8) == [0.3]
    assert frame_timestamps(0, 8) == []


async def test_extract_frames_and_audio(sample_video):
    assert 5.5 < await probe_duration(sample_video) < 6.5
    frames = await extract_frames(sample_video, count=8, width=320)
    assert len(frames) == 8
    assert all(f.jpeg.startswith(b"\xff\xd8") for f in frames)  # JPEG magic bytes
    audio = await extract_audio(sample_video, max_seconds=60)
    assert audio and len(audio) > 1000
