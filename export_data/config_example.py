# Configuration Examples for fill_template.py
# Copy these configurations to the top of fill_template.py to customize analysis

# Example 1: Extended price range
PRICE_RANGE = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Example 2: More granular time frames
TIME_FRAMES = [
    {'name': '0-2', 'min': 0, 'max': 2},
    {'name': '2-4', 'min': 2, 'max': 4},
    {'name': '4-6', 'min': 4, 'max': 6},
    {'name': '6-8', 'min': 6, 'max': 8},
    {'name': '8-10', 'min': 8, 'max': 10},
    {'name': '10-15', 'min': 10, 'max': 15}
]

# Example 3: Focus on early time frames
TIME_FRAMES_EARLY = [
    {'name': '0-1', 'min': 0, 'max': 1},
    {'name': '1-2', 'min': 1, 'max': 2},
    {'name': '2-3', 'min': 2, 'max': 3},
    {'name': '3+', 'min': 3, 'max': 999}
]

# Example 4: Custom column order (add more frame indices as needed)
ANALYSIS_COLUMNS_EXTENDED = [
    # First 3 time frames - just rounds count
    {'type': 'time_frame', 'frame_index': 0, 'property': 'in_frame_rounds'},
    {'type': 'time_frame', 'frame_index': 1, 'property': 'in_frame_rounds'},
    {'type': 'time_frame', 'frame_index': 2, 'property': 'in_frame_rounds'},
    # Win rates for first 3 time frames
    {'type': 'win_time_frame', 'frame_index': 0, 'property': 'win_rate'},
    {'type': 'win_time_frame', 'frame_index': 1, 'property': 'win_rate'},
    {'type': 'win_time_frame', 'frame_index': 2, 'property': 'win_rate'},
    # EV values for first 3 time frames
    {'type': 'win_time_frame', 'frame_index': 0, 'property': 'ev_value'},
    {'type': 'win_time_frame', 'frame_index': 1, 'property': 'ev_value'},
    {'type': 'win_time_frame', 'frame_index': 2, 'property': 'ev_value'},
]

# Example 5: Focus only on win statistics
ANALYSIS_COLUMNS_WIN_FOCUS = [
    {'type': 'win_time_frame', 'frame_index': 0, 'property': 'win_in_frame_rounds'},
    {'type': 'win_time_frame', 'frame_index': 0, 'property': 'win_rate'},
    {'type': 'win_time_frame', 'frame_index': 0, 'property': 'ev_value'},
    {'type': 'win_time_frame', 'frame_index': 1, 'property': 'win_in_frame_rounds'},
    {'type': 'win_time_frame', 'frame_index': 1, 'property': 'win_rate'},
    {'type': 'win_time_frame', 'frame_index': 1, 'property': 'ev_value'},
]

"""
Available properties:
- time_frame: 'in_frame_rounds', 'in_frame_rounds_rate'
- win_time_frame: 'win_in_frame_rounds', 'win_rate', 'ev_value'
"""
